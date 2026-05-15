"""Cliente envolvente de Anthropic con tracking de coste y retry estructurado.

Pensado para ser mockeable en tests (todas las llamadas pasan por `generate()`,
que en tests se reemplaza con un fake que devuelve texto predefinido).

Tracking: cada llamada se loguea en `costes_generacion.log` (CSV append) con
modelo, tokens y coste estimado.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:  # carga .env de la raíz del repo si está disponible (override=True para
    # asegurar que las claves del fichero ganan a las del shell)
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:  # pragma: no cover
    pass

# Precios por millón de tokens (orientativos a 2026-05).
_PRICES_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.8, 4.0),
    "claude-haiku-4-5": (0.8, 4.0),
}


@dataclass
class GenerationResult:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    error: str | None = None
    raw_response: object | None = field(default=None, repr=False)

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text)


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    inp, out = _PRICES_USD_PER_MTOK.get(model, (3.0, 15.0))
    return round((input_tokens * inp + output_tokens * out) / 1_000_000, 6)


def _log_cost(repo_root: Path, kind: str, episode_id: str,
              result: GenerationResult, validation_result: str) -> None:
    """Append a `costes_generacion.log` (CSV) con el coste de esta generación."""
    log_path = repo_root / "costes_generacion.log"
    new_file = not log_path.exists()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow([
                "timestamp", "kind", "episode_id", "model",
                "input_tokens", "output_tokens", "cost_usd",
                "validation_result",
            ])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            kind, episode_id, result.model,
            result.input_tokens, result.output_tokens, result.cost_usd,
            validation_result,
        ])


def generate(*, system: str, user: str, model: str,
             max_output_tokens: int = 8000,
             temperature: float = 0.7,
             stream: bool = True,
             api_key: str | None = None) -> GenerationResult:
    """Llama a la API de Anthropic y devuelve un `GenerationResult`.

    Si el paquete `anthropic` no está disponible o no hay API key, devuelve un
    `GenerationResult` con `text=""` y `error` describiendo el motivo. Los
    tests mockean esta función para no llamar la API real.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return GenerationResult(
            text="", model=model, input_tokens=0, output_tokens=0,
            cost_usd=0.0, error="ANTHROPIC_API_KEY no definida",
        )
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        return GenerationResult(
            text="", model=model, input_tokens=0, output_tokens=0,
            cost_usd=0.0, error=f"anthropic no disponible: {exc}",
        )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        kwargs = dict(
            model=model,
            max_tokens=max_output_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if stream:
            text_parts: list[str] = []
            input_tokens = 0
            output_tokens = 0
            with client.messages.stream(**kwargs) as stream_resp:
                for delta in stream_resp.text_stream:
                    text_parts.append(delta)
                final = stream_resp.get_final_message()
                input_tokens = getattr(final.usage, "input_tokens", 0)
                output_tokens = getattr(final.usage, "output_tokens", 0)
            text = "".join(text_parts)
        else:
            resp = client.messages.create(**kwargs)
            text = "".join(getattr(b, "text", "") for b in resp.content)
            input_tokens = getattr(resp.usage, "input_tokens", 0)
            output_tokens = getattr(resp.usage, "output_tokens", 0)
        cost = _estimate_cost(model, input_tokens, output_tokens)
        return GenerationResult(
            text=text, model=model,
            input_tokens=input_tokens, output_tokens=output_tokens,
            cost_usd=cost,
        )
    except Exception as exc:  # noqa: BLE001
        return GenerationResult(
            text="", model=model, input_tokens=0, output_tokens=0,
            cost_usd=0.0, error=f"{type(exc).__name__}: {exc}",
        )


def generate_with_retry(*, system: str, user: str, model: str,
                         retry_feedback: str | None = None,
                         **kwargs) -> tuple[GenerationResult, GenerationResult | None]:
    """Genera y, si `retry_feedback` se proporciona tras un hard-fail, hace UN
    reintento con feedback explícito. Devuelve `(primer_intento, segundo|None)`.

    El segundo intento añade el feedback al final del prompt user, manteniendo
    el system idéntico (más cache-friendly).
    """
    first = generate(system=system, user=user, model=model, **kwargs)
    if retry_feedback is None:
        return first, None
    retry_user = (
        f"{user}\n\n---\nFEEDBACK DE LA GENERACIÓN ANTERIOR (no se aceptó):\n"
        f"{retry_feedback}\n\n"
        "Genera de nuevo respetando exactamente las reglas del system prompt."
    )
    second = generate(system=system, user=retry_user, model=model, **kwargs)
    return first, second


def track_cost(repo_root: Path, kind: str, episode_id: str,
               result: GenerationResult,
               validation_result: str = "n/a") -> None:
    """Atajo para loguear la generación en costes_generacion.log."""
    _log_cost(repo_root, kind, episode_id, result, validation_result)
