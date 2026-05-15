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
    # Número de re-intentos con feedback tras un fallo hard. 0 = sin retry
    # (solo la generación inicial). 3 = hasta 4 intentos en total.
    max_retries: int = 3
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
        "ACCIÓN: CIERRE_FINAL debe incluir LITERALMENTE 'Y hasta aqui ha "
        "llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos "
        "capitulos donde la I.A. crea contenido sobre I.A.'",
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
}


def _format_soft_failures_feedback(results: list[ValidationResult]) -> str:
    """Feedback para la fase de pulido fino: 0 hard, quedan soft.

    Se llama sólo cuando todos los hard ya están a 0 — el guion está
    aceptado funcionalmente, pero queremos quitar los avisos de calidad
    (pingpong, frases largas, rachas cortas, tags, etc.).
    """
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
        hint = _RULE_ACTION_HINTS.get(r.rule_name)
        if hint:
            lines.append(f"  {hint}")
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
        hint = _RULE_ACTION_HINTS.get(r.rule_name)
        if hint:
            lines.append(f"  {hint}")
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
    """Quita ``` y ```lenguaje envolventes que algunos modelos añaden alrededor
    del guion. Conserva la indentación interior del guion."""
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text
    # Quita la primera línea (```lang opcional) y el cierre final (```).
    first_nl = stripped.find("\n")
    if first_nl == -1:
        return text
    inner = stripped[first_nl + 1:]
    if inner.rstrip().endswith("```"):
        inner = inner.rstrip()[:-3]
    return inner.strip("\n")


def post_process_text(text: str, *, apply_num2words: bool = True,
                     apply_pronunciation_overrides: bool = True,
                     apply_ssml_pauses: bool = True,
                     pauses_config: dict | None = None,
                     trim_fuentes_max_years: int | None = None) -> str:
    """Aplica los pases post-LLM en orden: trim-fuentes → números → overrides → SSML.

    El trim de BLOQUE_FUENTES corre PRIMERO (sobre el texto crudo), porque
    los pases posteriores pueden mover separadores y los offsets del trim
    se calculan respecto al texto bruto.
    """
    out = _strip_code_fence(text)
    if trim_fuentes_max_years is not None:
        from generadores.shared.fuentes_trim import trim_bloque_fuentes
        out = trim_bloque_fuentes(out, max_years=trim_fuentes_max_years)
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
    # Primera generación.
    first = anthropic_client.generate(
        system=request.system_prompt,
        user=request.user_prompt,
        model=request.model,
        max_output_tokens=request.max_output_tokens,
        temperature=request.temperature,
    )
    anthropic_client.track_cost(
        request.repo_root, request.kind, request.episode_id, first,
        "pending",
    )

    best_raw = first.text
    best_final = post_process_text(
        first.text,
        apply_num2words=request.apply_num2words,
        apply_pronunciation_overrides=request.apply_pronunciation_overrides,
        apply_ssml_pauses=request.apply_ssml_pauses,
        pauses_config=request.ssml_pauses_config,
        trim_fuentes_max_years=request.trim_fuentes_max_years,
    )
    best_results: list[ValidationResult] = (
        request.validate_fn(best_final, request.episode_id)
        if request.validate_fn and best_final else []
    )
    best_score = _score(best_results) if best_results else (999, 999)
    last_retry: anthropic_client.GenerationResult | None = None
    used_retry = False

    # Bucle de retries con feedback enriquecido. Cada intento usa el MEJOR
    # resultado anterior para construir el feedback (incluso si el último
    # intento fue peor). Si la 1ª llamada vino sin texto (error de red /
    # rate-limit), no entramos al bucle: no hay nada que validar.
    # CONDICIÓN: seguimos mientras quede CUALQUIER fallo (hard o soft),
    # hasta agotar `max_retries`. Los hard tienen prioridad: cuando todavía
    # hay hard, sólo se inyecta su feedback; cuando ya hay 0 hard y queda
    # soft, se inyecta feedback de los soft restantes.
    attempt = 0
    while (
        request.validate_fn
        and best_final                # 1ª generación produjo texto
        and best_score != (0, 0)       # quedan hard o soft
        and attempt < request.max_retries
    ):
        attempt += 1
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
        # En el último intento bajamos un poco la temperatura para que el
        # modelo sea más conservador siguiendo las reglas.
        temp = (
            request.temperature
            if attempt < request.max_retries
            else max(0.2, request.temperature - 0.3)
        )
        retry_gen = anthropic_client.generate(
            system=request.system_prompt,
            user=retry_user,
            model=request.model,
            max_output_tokens=request.max_output_tokens,
            temperature=temp,
        )
        last_retry = retry_gen
        used_retry = True
        anthropic_client.track_cost(
            request.repo_root, f"{request.kind}-retry{attempt}",
            request.episode_id, retry_gen, "pending",
        )
        if not (retry_gen and retry_gen.ok):
            continue
        candidate_raw = retry_gen.text
        candidate_final = post_process_text(
            candidate_raw,
            apply_num2words=request.apply_num2words,
            apply_pronunciation_overrides=request.apply_pronunciation_overrides,
            apply_ssml_pauses=request.apply_ssml_pauses,
            pauses_config=request.ssml_pauses_config,
            trim_fuentes_max_years=request.trim_fuentes_max_years,
        )
        candidate_results = request.validate_fn(candidate_final, request.episode_id)
        candidate_score = _score(candidate_results)
        # Nos quedamos con el MEJOR intento por (hard, soft) — incluso si la
        # iteración nueva fue peor, conservamos el anterior.
        if candidate_score < best_score:
            best_score = candidate_score
            best_raw = candidate_raw
            best_final = candidate_final
            best_results = candidate_results
        if best_score == (0, 0):
            break  # perfección alcanzada.

    return PipelineResult(
        request=request, raw_text=best_raw, final_text=best_final,
        generation=first, retry_generation=last_retry,
        validation_results=best_results, used_retry=used_retry,
    )
