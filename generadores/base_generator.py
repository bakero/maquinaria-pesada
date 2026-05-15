"""Generador base: orquesta la pipeline común a los tres formatos.

Pipeline:
  1. Cargar fuente(s) → texto + tokens.
  2. Pre-escritura: extraer datos numéricos, casos, frase-fuerza, contraintuitivos.
  3. Construir prompt: system + user con la pre-escritura inyectada.
  4. Llamar a Anthropic (con retry-con-feedback).
  5. Post-process: num2words → pronunciation overrides → SSML pauses.
  6. Validar con el validador del formato.
  7. Si hard-fail: 1 retry con feedback explícito al LLM.
  8. Tracking de coste en costes_generacion.log.

Los generadores especialistas (m/t/s_generator) llaman a `run_pipeline()` con
sus parámetros propios y, opcionalmente, su validate_fn.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from generadores.shared import (
    anthropic_client,
    num2words_es,
    pronunciation_overrides,
    ssml_pauses,
)
from validators.result import ValidationResult, summarize


@dataclass
class PipelineRequest:
    """Lo que el especialista pasa al pipeline."""

    episode_id: str
    kind: str                                  # "M" | "T" | "S"
    system_prompt: str
    user_prompt: str
    model: str
    repo_root: Path
    max_output_tokens: int = 8000
    temperature: float = 0.7
    apply_num2words: bool = True
    apply_pronunciation_overrides: bool = True
    apply_ssml_pauses: bool = True
    ssml_pauses_config: dict | None = None
    validate_fn: Callable[[str, str], list[ValidationResult]] | None = None


@dataclass
class PipelineResult:
    request: PipelineRequest
    raw_text: str                              # antes de post-process
    final_text: str                            # tras num2words + overrides + SSML
    generation: anthropic_client.GenerationResult
    retry_generation: anthropic_client.GenerationResult | None = None
    validation_results: list[ValidationResult] = field(default_factory=list)
    used_retry: bool = False

    @property
    def is_blocked_by_validation(self) -> bool:
        return any(r.is_blocking for r in self.validation_results)


def _format_hard_failures_feedback(results: list[ValidationResult]) -> str:
    blocking = [r for r in results if r.is_blocking]
    if not blocking:
        return ""
    lines = ["Reglas HARD que no se cumplieron en el guion anterior:"]
    for r in blocking:
        lines.append(f"- {r.rule_name}: {r.message}")
    lines.append(
        "Regenera el guion respetando exactamente esas reglas, sin tocar "
        "las que sí cumplió."
    )
    return "\n".join(lines)


def post_process_text(text: str, *, apply_num2words: bool = True,
                     apply_pronunciation_overrides: bool = True,
                     apply_ssml_pauses: bool = True,
                     pauses_config: dict | None = None) -> str:
    """Aplica los tres pases post-LLM en orden: números → overrides → SSML."""
    out = text
    if apply_num2words:
        out = num2words_es.replace_numbers_in_text(out)
    if apply_pronunciation_overrides:
        out = pronunciation_overrides.apply_overrides(out)
    if apply_ssml_pauses:
        out = ssml_pauses.insert_all(out, pauses_config)
    return out


def run_pipeline(request: PipelineRequest) -> PipelineResult:
    """Ejecuta la pipeline completa.

    Llama al LLM, post-procesa, valida y, si hay hard-fail, hace 1 retry con
    feedback explícito. El coste de cada llamada se registra en
    `costes_generacion.log`.
    """
    first = anthropic_client.generate(
        system=request.system_prompt,
        user=request.user_prompt,
        model=request.model,
        max_output_tokens=request.max_output_tokens,
        temperature=request.temperature,
    )

    raw_text = first.text
    final_text = post_process_text(
        raw_text,
        apply_num2words=request.apply_num2words,
        apply_pronunciation_overrides=request.apply_pronunciation_overrides,
        apply_ssml_pauses=request.apply_ssml_pauses,
        pauses_config=request.ssml_pauses_config,
    )

    validation_results: list[ValidationResult] = []
    retry: anthropic_client.GenerationResult | None = None
    used_retry = False

    if request.validate_fn and final_text:
        validation_results = request.validate_fn(final_text, request.episode_id)
        if any(r.is_blocking for r in validation_results):
            feedback = _format_hard_failures_feedback(validation_results)
            retry_user = (
                f"{request.user_prompt}\n\n---\n"
                "FEEDBACK DE LA GENERACIÓN ANTERIOR (no se aceptó):\n"
                f"{feedback}\n\n"
                "Genera de nuevo respetando exactamente las reglas del system "
                "prompt."
            )
            retry = anthropic_client.generate(
                system=request.system_prompt,
                user=retry_user,
                model=request.model,
                max_output_tokens=request.max_output_tokens,
                temperature=request.temperature,
            )
            used_retry = True
            if retry and retry.ok:
                raw_text = retry.text
                final_text = post_process_text(
                    raw_text,
                    apply_num2words=request.apply_num2words,
                    apply_pronunciation_overrides=request.apply_pronunciation_overrides,
                    apply_ssml_pauses=request.apply_ssml_pauses,
                    pauses_config=request.ssml_pauses_config,
                )
                validation_results = request.validate_fn(final_text, request.episode_id)

    # Tracking de coste: logueamos la(s) llamada(s).
    summary = summarize(validation_results)
    validation_label = (
        "blocked" if summary.get("blocking") else
        "ok" if validation_results else "no_validation"
    )
    anthropic_client.track_cost(
        request.repo_root, request.kind, request.episode_id, first,
        validation_label,
    )
    if used_retry and retry is not None:
        anthropic_client.track_cost(
            request.repo_root, f"{request.kind}-retry", request.episode_id,
            retry, validation_label,
        )

    return PipelineResult(
        request=request, raw_text=raw_text, final_text=final_text,
        generation=first, retry_generation=retry,
        validation_results=validation_results, used_retry=used_retry,
    )
