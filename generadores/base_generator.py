"""Generador base: orquesta la pipeline común a los tres formatos.

Pipeline:
  1. Cargar fuente(s) → texto + tokens.
  2. Pre-escritura: extraer datos numéricos, casos, frase-fuerza, contraintuitivos.
  3. Construir prompt: system (bloques cacheables) + user con la pre-escritura.
  4. Llamar a Anthropic (con retry-con-feedback o patch retry).
  5. Post-process: trim fuentes → num2words → pronunciation overrides → SSML pauses.
  6. Validar con el validador del formato.
  7. Si hard-fail: hasta `max_retries` reintentos con feedback explícito.
     Early-stop si (hard ≤ early_stop_hard, soft ≤ early_stop_soft) tras
     attempt ≥ 2.
  8. Tracking de coste extendido en costes_generacion.log (formato v2).
"""
from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from generadores import retry_hints
from generadores.shared import (
    anthropic_client,
    num2words_es,
    pronunciation_overrides,
    ssml_pauses,
)
from generadores.shared.anthropic_client import CacheableBlock
from validators.result import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineRequest:
    """Lo que el especialista pasa al pipeline.

    Soporta dos formas de pasar el system prompt:
    - `system_prompt` (str): legacy, sin caching.
    - `system_blocks` (list[CacheableBlock]): bloques cacheados con `cache_control`.

    Si se pasan ambos, gana `system_blocks`.
    """

    episode_id: str
    kind: str                                  # "M" | "T" | "S"
    user_prompt: str
    model: str
    repo_root: Path
    system_prompt: str = ""
    system_blocks: list[CacheableBlock] | None = None
    max_output_tokens: int = 8000
    temperature: float = 0.7
    apply_num2words: bool = True
    apply_pronunciation_overrides: bool = True
    apply_ssml_pauses: bool = True
    ssml_pauses_config: dict | None = None
    validate_fn: Callable[[str, str], list[ValidationResult]] | None = None
    # Número de re-intentos con feedback tras un fallo hard. 0 = sin retry
    # (solo la generación inicial). 3 = hasta 4 intentos en total.
    max_retries: int = 3
    # Early stop: si tras attempt ≥ 2 el mejor score es (≤hard, ≤soft), salir.
    # None = desactivado.
    early_stop_threshold: tuple[int, int] | None = (2, 5)
    # Estrategia de retry: "full" = regen completo, "auto" = patch retry cuando
    # los fallos están localizados, "full" en caso contrario.
    retry_strategy: Literal["full", "auto"] = "auto"
    # Si > 0, aplica trim mecánico de BLOQUE_FUENTES tras la generación
    # cuando el conteo de años distintos excede este máximo. None = no aplica.
    trim_fuentes_max_years: int | None = None


@dataclass
class PipelineResult:
    request: PipelineRequest
    raw_text: str                              # antes de post-process
    final_text: str                            # tras num2words + overrides + SSML
    generation: anthropic_client.GenerationResult
    retry_generation: anthropic_client.GenerationResult | None = None
    validation_results: list[ValidationResult] = field(default_factory=list)
    used_retry: bool = False
    retries_done: int = 0
    patch_retries: int = 0

    @property
    def is_blocked_by_validation(self) -> bool:
        return any(r.is_blocking for r in self.validation_results)


_RULE_ACTION_HINTS: dict[str, str] = {
    "word_count":
        "ACCIÓN: amplía bloques de desarrollo (4-6 frases, 70-100 palabras "
        "cada uno) hasta llegar al rango. NO recortes nada existente; AÑADE.",
    "s_word_count":
        "ACCIÓN según dirección del fallo: "
        "(a) Si word count < 157: tu Short es MUY corto. AÑADE DOS frases "
        "concretas más antes del cierre canónico: (1) un caso de empresa "
        "real con resultado documentado (~25-35 palabras: 'Morgan Stanley "
        "implementó esto con sus asesores; en seis meses la búsqueda de "
        "información pasó de horas a minutos.') y (2) una métrica adicional "
        "o un sector más afectado (~20-30 palabras). Apunta a 180-185 "
        "palabras totales — calcúlalo. SI EL PREVIO TENÍA 109 PALABRAS, "
        "AÑADE 70 PALABRAS NUEVAS — no 10 ni 20, SETENTA. "
        "(b) Si word count > 198: RECORTA frases redundantes del EJEMPLO. "
        "PROHIBIDO devolver meta-texto (cabeceras tipo '# BORRADOR', "
        "'# PLAN', listados de pasos, target totals). DEVUELVE SOLO el "
        "texto narrado del Short, empezando por el HOOK y terminando con "
        "el cierre canónico literal.",
    "parity_opener":
        "ACCIÓN: cambia el HOOK para que lo abra el speaker correcto por "
        "paridad. El opener dice HOOK + el aviso de IA.",
    "ia_warning":
        "ACCIÓN: traslada el aviso de IA al opener. La intervención con "
        "'sistema automatico' y 'puede contener errores' la pronuncia el "
        "speaker que abre el HOOK.",
    "m_concepts_count":
        "ACCIÓN: en CIERRE_CONCEPTOS deben quedar 3-5 INTERVENCIONES totales. "
        "Si tienes 6 o más, fusiona la apertura 'No te puedes ir...' con el "
        "primer concepto EN UN SOLO BLOQUE del opener. Total bloques = nº "
        "conceptos (3-5).",
    "m_leader_aplicacion":
        "ACCIÓN: en APLICACION_PRACTICA Maria debe quedar entre 30% y 40%. "
        "Para subirla: amplía SU apertura del caso a 130-160 palabras y SU "
        "intervención del cierre conjunto a 70-90 palabras. Yago se mantiene "
        "en 140-200 por turno de detalle (2-3 turnos).",
    "m_leader_destacado":
        "ACCIÓN: en BLOQUE_DESTACADO el balance debe estar entre 40%-60%. "
        "El speaker minoritario debe tener al menos 1-2 bloques de desarrollo "
        "completos (4-6 frases, 60-100 palabras).",
    "m_fuentes_count":
        "ACCIÓN: BLOQUE_FUENTES requiere 3 o 4 fuentes con AÑOS DISTINTOS. "
        "Si el mensaje dice 'detecta 2': te falta una. AÑADE una tercera "
        "con año distinto (Vaswani 2017, Lewis 2020, Stanford 2021, NIST "
        "2023, AI Act EU 2024). "
        "Si dice 5+: ELIMINA fuentes hasta dejar 3 o 4 o reescribe años "
        "laterales como 'hoy'/'actualmente'.",
    "t_fuentes_count_exact_3":
        "ACCIÓN CRÍTICA: BLOQUE_FUENTES debe tener EXACTAMENTE 3 fuentes "
        "con 3 AÑOS DISTINTOS. "
        "Si el mensaje dice 'detecta 2': te FALTA una fuente. AÑADE una "
        "tercera fuente con un año distinto a las dos que ya tienes — usa "
        "un paper o informe canónico (Vaswani 2017, Lewis 2020, Guu 2020, "
        "Bommasani Stanford 2021, NIST AI RMF 2023, AI Act EU 2024, "
        "OWASP LLM Top10 2025...). "
        "Si dice 'detecta 4' o más: te SOBRA. ELIMINA fuentes o reemplaza "
        "sus años por 'hoy'/'actualmente'. "
        "PROCEDIMIENTO: (1) Escribe SOLO 3 fuentes en BLOQUE_FUENTES, una "
        "por una, cada una con un año único en palabras. (2) Cuenta los "
        "años distintos en el bloque antes de cerrarlo: deben ser 3 exactos.",
    "t_leader_como":
        "ACCIÓN CRÍTICA: BLOQUE_COMO debe ser 40-60% para cada speaker. "
        "Si Yago lidera con >60%: ELIMINA o ACORTA un turno largo suyo "
        "(quita 60-100 palabras del bloque más extenso de Yago) Y AÑADE "
        "a Maria un nuevo turno de 80-120 palabras explicando un sub-"
        "mecanismo completo (4-6 frases). Si Maria <40%: dale otro turno "
        "de desarrollo de 80-120 palabras. Verifica el reparto antes de "
        "devolver: cuenta palabras de cada speaker en COMO y confirma que "
        "Yago está entre 40% y 60%.",
    "t_leader_casos":
        "ACCIÓN: en BLOQUE_CASOS Maria debe liderar con ≥60% de palabras. "
        "Si Maria <60%, amplía sus turnos con detalles del caso (cifras, "
        "actores, resultado).",
    "t_leader_limites":
        "ACCIÓN: en BLOQUE_LIMITES Yago debe liderar con ≥55% de palabras.",
    "t_casos_company_count":
        "ACCIÓN: BLOQUE_CASOS necesita ≥2 EMPRESAS CON NOMBRE PROPIO "
        "reconocible. Usa al menos dos de: Harvey AI, Morgan Stanley, "
        "JPMorgan, IBM, Microsoft, Google, OpenAI, Anthropic, Meta, "
        "Lemonade, Zara, Nordea, BBVA, Santander, Telefonica, McKinsey, "
        "Gartner, Stanford, MIT.",
    "canonical_hook_closing":
        "ACCIÓN: el HOOK debe cerrar LITERALMENTE con 'Esto es MaquinarIA "
        "Pesada. Arrancamos.'",
    "canonical_concepts_opening":
        "ACCIÓN: CIERRE_CONCEPTOS abre con 'No te puedes ir de este capitulo "
        "sin haber entendido estos conceptos' (literal, sin tildes en "
        "'capitulo').",
    "canonical_final_closing":
        "ACCIÓN: CIERRE_FINAL debe incluir la frase canónica con 'I.A.' "
        "ESCRITO LITERAL CON PUNTOS — NO la expandas a 'inteligencia "
        "artificial'. Frase: 'Y hasta aquí ha llegado nuestro episodio de "
        "MaquinarIA Pesada. Síguenos para nuevos capítulos donde la I.A. "
        "crea contenido sobre I.A.' (tildes válidas; el TTS pronunciará "
        "'I.A.' como las letras i-a, coherente con la marca MaquinarIA).",
    "canonical_s_closing":
        "ACCIÓN: el Short debe terminar con 'Más sobre [tema] en el episodio "
        "T de MaquinarIA Pesada.' (literal, 'T' es una letra).",
    "audio_rule_reaction_length":
        "ACCIÓN: las preguntas/reacciones deben tener ≤15 palabras. Acorta "
        "las preguntas largas o conviértelas en afirmaciones cortas.",
    "saludo_format":
        "ACCIÓN: SALUDO_Y_PRESENTACION debe tener 3 intervenciones SEPARADAS, "
        "una por línea. Los dos nombres no pueden aparecer en la misma "
        "intervención.",
    "section_order":
        "ACCIÓN: respeta el orden EXACTO de secciones del system prompt.",
    "required_sections":
        "ACCIÓN: añade todas las secciones obligatorias listadas.",
    "forbidden_sections":
        "ACCIÓN: elimina las secciones prohibidas del guion.",
    "no_invented_surnames":
        "ACCIÓN: elimina apellidos. Los presentadores se llaman solo Maria y "
        "Yago, sin apellidos.",
    "blacklist_interjection":
        "ACCIÓN: elimina las interjecciones de validación-coro "
        "('exactamente', 'exacto', 'claro que si', 'por supuesto', etc.) y "
        "sustitúyelas por contenido específico del tema.",
    "s_hook_template":
        "ACCIÓN: el HOOK del Short debe encajar en una plantilla H1 "
        "(contradicción: 'no es / no son / aunque...'), H2 (número en "
        "palabras impactante), o H3 (pregunta '¿...?').",
    # ---- Soft (pulido fino) ----
    "pingpong":
        "ACCIÓN (anti-pingpong): en el bloque señalado, el speaker de APOYO "
        "tiene demasiada presencia. Su ratio palabras-apoyo / palabras-líder "
        "debe quedar ≤ 0.33. Convierte sus turnos de desarrollo en "
        "reacciones BREVES de 5-12 palabras (una pregunta corta o una "
        "confirmación específica al tema, NO 'exactamente'/'claro'). "
        "Mantén el liderazgo del speaker que toca por bloque (PANORAMA→Yago, "
        "CASOS→Maria, LIMITES→Yago). Reduce las palabras del apoyo "
        "fusionando dos turnos suyos en uno corto o eliminando uno.",
    "tts_invariant_long_sentences":
        "ACCIÓN: hay frases de >32 palabras. Localízalas y PÁRTELAS en 2 "
        "o 3 frases cortas (cada una ≤30 palabras). Usa puntos en lugar "
        "de comas largas, conjunciones 'y'/'porque' o pronombres demos"
        "trativos para encadenar. Nunca dejes una frase >32 palabras.",
    "tts_invariant_consecutive_short_sentences":
        "ACCIÓN: hay intervenciones con >3 frases cortas (≤8 palabras) "
        "seguidas. Fusiona pares de frases cortas en una mediana (15-25 "
        "palabras) con conector 'y'/'porque'/'que' o coma + relativo, "
        "para alternar ritmo. Apunta a no más de 2 frases cortas "
        "consecutivas por intervención.",
    "tts_tags_allowed":
        "ACCIÓN: sólo se permiten las etiquetas TTS canónicas "
        "([didactico], [analitico], [reflexivo], [claro], [explicativo], "
        "[curioso], [escéptico], [enfático]). Elimina cualquier tag "
        "fuera de esa lista.",
    "audio_rule_intervention_over_max":
        "ACCIÓN: hay alguna intervención que supera el máximo permitido. "
        "Pártela en dos turnos del mismo speaker o redistribuye con un "
        "turno corto del otro en medio.",

    # ---- Regla pedagógica SOFT post-override (master) ----
    "pedagogy_first_mention":
        "ACCIÓN: la primera mención de los términos listados no tiene su "
        "expansión/traducción en las ~250 chars cercanas. Reescribe la "
        "primera aparición usando uno de estos patrones: "
        "(a) Sigla inglesa: 'RAG, que viene de Retrieval-Augmented "
        "Generation, o Generación Aumentada por Recuperación, es...'; "
        "(b) Término inglés: 'El fine-tuning, o ajuste fino del modelo, "
        "consiste en...'; "
        "(c) Sigla castellana: 'PCA, Análisis de Componentes Principales, "
        "es...'; "
        "(d) Producto: 'BERT, un modelo desarrollado por Google para "
        "comprensión de lenguaje, ...'. "
        "Solo la PRIMERA mención: las siguientes pueden ser el término "
        "corto. NO añadas la expansión en cada uso.",

    # ---- v6.1 — reglas editoriales HARD pre-override ----
    "glossary_term_first_use_expanded":
        "ACCIÓN: cada sigla del glosario (LLM, RAG, GPT, MLOps, CoT, RLHF, "
        "etc.) debe expandirse en CASTELLANO la PRIMERA vez que aparezca en "
        "el guion, en aposición con comas: 'los LLM, modelos de lenguaje "
        "grandes, son...'. La expansión castellana exacta está en el campo "
        "**ES:** del glosario unificado (PDFs/auxiliares/glosario_unificado.md). "
        "Tras el primer uso ya solo se nombra la sigla. NO expandas en "
        "inglés ('large language models') ni con paréntesis hablado.",

    "blacklist_ai_bro":
        "ACCIÓN: elimina las frases AI-bro pomposas al inicio de "
        "intervención ('En el mundo actual de la IA', 'Sin más preámbulos', "
        "'Es importante destacar que', 'Cabe mencionar'). Empieza la "
        "intervención con contenido específico del tema, no con clichés de "
        "divulgador genérico.",

    "blacklist_coach":
        "ACCIÓN: elimina las frases de coach motivacional ('¡Excelente "
        "pregunta!', 'Espero que esto te ayude', '¡Adelante con tu "
        "proyecto!'). MaquinarIA Pesada NO aplaude al oyente — es anti-marca.",

    "blacklist_cliffhanger":
        "ACCIÓN: elimina cliffhangers artificiales al inicio de intervención "
        "('Stay tuned', 'lo veremos en próximos episodios' sin nombrar un "
        "tema concreto). Si quieres remitir a un episodio T del módulo, "
        "nómbralo: '...lo desarrollamos en el T sobre [tema concreto]'.",
}


def _format_soft_failures_feedback(results: list[ValidationResult]) -> str:
    soft = [r for r in results if r.severity == "SOFT" and not r.passed]
    if not soft:
        return ""
    lines = [
        "El guion ya pasa todas las reglas HARD. Quedan estos avisos SOFT "
        "(calidad/pulido fino). Mantén EXACTAMENTE las decisiones HARD "
        "que ya están bien (estructura, líderes por bloque, fuentes, "
        "word counts, cierres canónicos) y SOLO ajusta lo necesario para "
        "limpiar estos avisos:"
    ]
    for r in soft:
        lines.append(f"\n- {r.rule_name}: {r.message}")
        hint = retry_hints.get_hint(r.rule_name) or _RULE_ACTION_HINTS.get(r.rule_name)
        if hint:
            lines.append(hint if hint.lstrip().startswith("ACCIÓN")
                          else f"  {hint}")
    lines.append(
        "\nIMPORTANTE: no rehagas el guion entero. Reescribe SOLO las "
        "frases / turnos afectados. No toques HOOK, SALUDO, CIERRE_CONCEPTOS, "
        "CIERRE_FINAL ni BLOQUE_FUENTES — esos ya están validados. "
        "Entrega el guion completo, pero con cambios mínimos quirúrgicos."
    )
    return "\n".join(lines)


def _format_hard_failures_feedback(results: list[ValidationResult]) -> str:
    blocking = [r for r in results if r.is_blocking]
    if not blocking:
        return ""
    lines = [
        "Reglas HARD que NO se cumplieron en el guion anterior. "
        "Corrige TODAS y conserva las que sí pasaste:"
    ]
    for r in blocking:
        lines.append(f"\n- {r.rule_name}: {r.message}")
        hint = retry_hints.get_hint(r.rule_name) or _RULE_ACTION_HINTS.get(r.rule_name)
        if hint:
            lines.append(hint if hint.lstrip().startswith("ACCIÓN")
                          else f"  {hint}")
    lines.append(
        "\nCuenta y verifica cada regla antes de devolver el guion. "
        "No empieces a redactar hasta haber decidido el tamaño exacto de "
        "cada bloque y el reparto de palabras por speaker."
    )
    return "\n".join(lines)


def _score(results: list[ValidationResult]) -> tuple[int, int]:
    """Score para comparar intentos: (hard_count, soft_count). Menor = mejor."""
    hard = sum(1 for r in results if r.severity == "HARD" and not r.passed)
    soft = sum(1 for r in results if r.severity == "SOFT" and not r.passed)
    return (hard, soft)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text
    first_nl = stripped.find("\n")
    if first_nl == -1:
        return text
    inner = stripped[first_nl + 1:]
    if inner.rstrip().endswith("```"):
        inner = inner.rstrip()[:-3]
    return inner.strip("\n")


def post_process_text(text: str, *, apply_num2words: bool = True,
                     apply_pronunciation_overrides: bool = True,
                     apply_pedagogy_inject: bool = True,
                     apply_ssml_pauses: bool = True,
                     pauses_config: dict | None = None,
                     trim_fuentes_max_years: int | None = None) -> str:
    out = _strip_code_fence(text)
    if trim_fuentes_max_years is not None:
        from generadores.shared.fuentes_trim import trim_bloque_fuentes
        out = trim_bloque_fuentes(out, max_years=trim_fuentes_max_years)
    if apply_num2words:
        out = num2words_es.replace_numbers_in_text(out)
    if apply_pronunciation_overrides:
        out = pronunciation_overrides.apply_overrides(out)
    if apply_pedagogy_inject:
        # Inserta expansion en primera mencion de terminos tecnicos.
        # Opera sobre texto post-overrides (busca "elemen", "rag", etc.).
        # Debe ir DESPUES de overrides y ANTES de SSML pauses.
        from generadores.shared.pedagogy_inject import inject_first_mentions
        out, _injected = inject_first_mentions(out)
    if apply_ssml_pauses:
        out = ssml_pauses.insert_all(out, pauses_config)
    return out


def _system_param(request: PipelineRequest) -> str | list[CacheableBlock]:
    """Devuelve el system param a pasar al cliente.

    Prioriza `system_blocks` sobre `system_prompt` legacy.
    """
    if request.system_blocks:
        return request.system_blocks
    return request.system_prompt


def _post_process_from_request(request: PipelineRequest, text: str) -> str:
    return post_process_text(
        text,
        apply_num2words=request.apply_num2words,
        apply_pronunciation_overrides=request.apply_pronunciation_overrides,
        apply_ssml_pauses=request.apply_ssml_pauses,
        pauses_config=request.ssml_pauses_config,
        trim_fuentes_max_years=request.trim_fuentes_max_years,
    )


def _select_retry_strategy(
    results: list[ValidationResult],
    attempt: int,
    configured: str,
) -> str:
    """Decide entre "full" regen y "patch" retry quirúrgico.

    Solo intentamos patch si:
    - configurado como "auto"
    - hay ≤3 hard fails
    - ninguno es estructural (orden / secciones faltantes / prohibidas)
    """
    if configured == "full":
        return "full"
    hard = [r for r in results if r.is_blocking]
    if not hard or len(hard) > 3:
        return "full"
    structural = {"required_sections", "forbidden_sections", "section_order",
                  "saludo_format"}
    if any(r.rule_name in structural for r in hard):
        return "full"
    return "patch"


def run_pipeline(request: PipelineRequest) -> PipelineResult:
    """Ejecuta la pipeline completa con caching, validación y retries.

    Estrategia de retry: por defecto "auto", que intenta patch quirúrgico
    cuando los fallos están localizados (1-3 hard, no estructurales) y full
    regen en otro caso. Se puede forzar full con `retry_strategy="full"`.
    """
    system_param = _system_param(request)

    # Primera generación.
    first = anthropic_client.generate(
        system=system_param,
        user=request.user_prompt,
        model=request.model,
        max_output_tokens=request.max_output_tokens,
        temperature=request.temperature,
    )
    best_raw = first.text
    best_final = _post_process_from_request(request, first.text) if first.text else ""
    best_results: list[ValidationResult] = (
        request.validate_fn(best_final, request.episode_id)
        if request.validate_fn and best_final else []
    )
    best_score = _score(best_results) if best_results else (999, 999)
    anthropic_client.track_cost(
        request.repo_root, request.kind, request.episode_id, first,
        "ok" if best_score == (0, 0) else "pending",
        attempt=0,
        hard_failed=best_score[0] if best_results else 0,
        soft_failed=best_score[1] if best_results else 0,
    )
    if first.cache_read_input_tokens or first.cache_creation_input_tokens:
        logger.info(
            "cache hit_rate=%.1f%% read=%d create=%d",
            first.cache_hit_rate * 100,
            first.cache_read_input_tokens,
            first.cache_creation_input_tokens,
        )

    last_retry: anthropic_client.GenerationResult | None = None
    used_retry = False
    retries_done = 0
    patch_retries = 0

    attempt = 0
    while (
        request.validate_fn
        and best_final
        and best_score != (0, 0)
        and attempt < request.max_retries
    ):
        attempt += 1
        # Early stop: si el resultado ya es "suficientemente bueno", parar.
        if request.early_stop_threshold and attempt >= 2:
            hard_thr, soft_thr = request.early_stop_threshold
            if best_score[0] <= hard_thr and best_score[1] <= soft_thr:
                logger.info(
                    "early_stop attempt=%d score=%s threshold=%s",
                    attempt, best_score, request.early_stop_threshold,
                )
                break

        strategy = _select_retry_strategy(
            best_results, attempt, request.retry_strategy,
        )

        retry_gen: anthropic_client.GenerationResult | None = None
        candidate_raw = ""
        candidate_final = ""
        candidate_results: list[ValidationResult] = []
        patch_applied = False

        if strategy == "patch":
            try:
                from generadores import patch_retry as pr
                patches, retry_gen = pr.request_patches(
                    script=best_final,
                    validation_results=best_results,
                    primary_model=request.model,
                    user_prompt_context=request.user_prompt[:1500],
                )
                if patches and retry_gen and retry_gen.ok:
                    patch_retries += 1
                    patch_applied = True
                    candidate_raw = pr.apply_patches(best_raw, patches)
                    candidate_final = _post_process_from_request(request, candidate_raw)
                    candidate_results = request.validate_fn(
                        candidate_final, request.episode_id,
                    )
            except Exception:  # noqa: BLE001
                logger.exception("patch_retry falló, cayendo a full regen")
                strategy = "full"

        if not patch_applied:
            # Full regen con feedback.
            if best_score[0] > 0:
                feedback = _format_hard_failures_feedback(best_results)
                severity_label = "HARD"
            else:
                feedback = _format_soft_failures_feedback(best_results)
                severity_label = "SOFT (pulido fino — los hard ya están)"
            retry_user = (
                f"{request.user_prompt}\n\n---\n"
                f"FEEDBACK DE LA GENERACIÓN ANTERIOR (intento {attempt} de "
                f"{request.max_retries}, {severity_label}):\n"
                f"{feedback}\n\n"
                "Genera de nuevo respetando exactamente las reglas del system "
                "prompt. Esta vez NO repitas los fallos listados."
            )
            temp = (
                request.temperature
                if attempt < request.max_retries
                else max(0.2, request.temperature - 0.3)
            )
            retry_gen = anthropic_client.generate(
                system=system_param,
                user=retry_user,
                model=request.model,
                max_output_tokens=request.max_output_tokens,
                temperature=temp,
            )
            if retry_gen.ok:
                candidate_raw = retry_gen.text
                candidate_final = _post_process_from_request(request, candidate_raw)
                candidate_results = request.validate_fn(
                    candidate_final, request.episode_id,
                )

        last_retry = retry_gen
        used_retry = True
        retries_done = attempt

        if retry_gen is None or not retry_gen.ok:
            anthropic_client.track_cost(
                request.repo_root, f"{request.kind}-retry{attempt}",
                request.episode_id,
                retry_gen or anthropic_client.GenerationResult(
                    text="", model=request.model,
                    input_tokens=0, output_tokens=0, cost_usd=0.0,
                    error="retry sin resultado",
                ),
                "error", attempt=attempt,
            )
            continue

        candidate_score = _score(candidate_results)
        anthropic_client.track_cost(
            request.repo_root,
            f"{request.kind}-{'patch' if strategy == 'patch' else 'retry'}{attempt}",
            request.episode_id, retry_gen,
            "ok" if candidate_score == (0, 0) else "pending",
            attempt=attempt,
            hard_failed=candidate_score[0],
            soft_failed=candidate_score[1],
        )
        # Nos quedamos con el MEJOR intento por (hard, soft).
        if candidate_score < best_score:
            best_score = candidate_score
            best_raw = candidate_raw
            best_final = candidate_final
            best_results = candidate_results
        if best_score == (0, 0):
            break

    return PipelineResult(
        request=request, raw_text=best_raw, final_text=best_final,
        generation=first, retry_generation=last_retry,
        validation_results=best_results, used_retry=used_retry,
        retries_done=retries_done, patch_retries=patch_retries,
    )


# --- Overrides por variable de entorno -----------------------------------
def env_max_retries(kind: str, default: int) -> int:
    """Permite forzar max_retries por env var (`MAX_RETRIES_M`, etc.)."""
    val = os.environ.get(f"MAX_RETRIES_{kind.upper()}")
    if val is None:
        return default
    try:
        return max(0, int(val))
    except ValueError:
        return default
