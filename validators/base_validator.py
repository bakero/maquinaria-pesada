"""Validador base: reglas comunes a los tres formatos (M, T, S).

Composición: los especialistas (`m_validator`, `t_validator`, `s_validator`)
llaman a `validate_common(parts)` y le añaden sus reglas específicas. No usa
herencia.
"""
from __future__ import annotations

import re

from validators.parser import ScriptParts, count_words
from validators.result import ValidationResult, fail, ok
from validators.shared import audio_rules, blacklist, canonical_phrases, parity

# Etiquetas TTS permitidas (lista cerrada — regla A.8).
ALLOWED_TTS_TAGS: frozenset[str] = frozenset({
    "didactico", "didactica", "explicativo", "explicativa",
    "directo", "directa", "serio", "seria", "firme",
    "contundente", "grave", "tenso", "tensa",
    "conversacional", "reflexivo", "reflexiva",
    "curioso", "curiosa", "ironico", "ironica",
    "esceptico", "esceptica", "natural", "pausado", "pausada",
    "calido", "calida", "claro", "clara",
    "analitico", "analitica",
})


def check_required_sections(parts: ScriptParts,
                            required: list[str]) -> ValidationResult:
    """Hard-fail si falta alguna sección obligatoria."""
    missing = [s for s in required if s not in parts.sections]
    if missing:
        return fail("required_sections", "HARD",
                    f"Faltan secciones obligatorias: {', '.join(missing)}",
                    missing=missing)
    return ok("required_sections", "HARD",
              f"Todas las secciones obligatorias presentes ({len(required)})")


def check_forbidden_sections(parts: ScriptParts,
                              forbidden: list[str]) -> ValidationResult:
    """Hard-fail si alguna sección prohibida aparece en el guion."""
    found = [s for s in forbidden if s in parts.sections]
    if found:
        return fail("forbidden_sections", "HARD",
                    f"Secciones prohibidas presentes: {', '.join(found)}",
                    found=found)
    return ok("forbidden_sections", "HARD", "Sin secciones prohibidas")


def check_section_order(parts: ScriptParts,
                         expected_order: list[str]) -> ValidationResult:
    """Hard-fail si las secciones no aparecen en el orden esperado."""
    actual = [s for s in parts.section_order if s in expected_order]
    if actual == expected_order:
        return ok("section_order", "HARD", "Orden de secciones correcto")
    return fail("section_order", "HARD",
                f"Orden esperado {expected_order}, encontrado {actual}",
                expected=expected_order, actual=actual)


def check_word_count(parts: ScriptParts, *, min_words: int,
                     max_words: int) -> ValidationResult:
    """Hard-fail si el total de palabras está fuera del rango duro del formato."""
    # Suma palabras de todas las intervenciones (excluye headers de sección).
    total = sum(count_words(i.text) for i in parts.all_interventions)
    if min_words <= total <= max_words:
        return ok("word_count", "HARD",
                  f"Word count {total} dentro de [{min_words}, {max_words}]")
    return fail("word_count", "HARD",
                f"Word count {total} fuera de [{min_words}, {max_words}]",
                total=total, min=min_words, max=max_words)


def check_tts_tags_allowed(parts: ScriptParts) -> ValidationResult:
    """Soft-warn si una intervención usa una etiqueta TTS fuera de la lista."""
    tag_re = re.compile(r"^\s*\[([^\]]+)\]")
    offenders: list[dict] = []
    for iv in parts.all_interventions:
        m = tag_re.match(iv.text)
        if m:
            tag = m.group(1).strip().lower()
            normalized = tag.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            if normalized not in ALLOWED_TTS_TAGS:
                offenders.append({"section": iv.section, "tag": tag})
    if offenders:
        return fail("tts_tags_allowed", "SOFT",
                    f"{len(offenders)} etiqueta(s) TTS fuera de la lista permitida",
                    offenders=offenders[:10])
    return ok("tts_tags_allowed", "SOFT",
              "Todas las etiquetas TTS están en la lista permitida")


def check_saludo_format(parts: ScriptParts) -> ValidationResult:
    """Hard-fail si SALUDO_Y_PRESENTACION colapsa en una sola intervención.

    Debe tener mínimo 3 intervenciones separadas y los dos nombres no pueden
    aparecer en la misma intervención.
    """
    saludo = parts.interventions("SALUDO_Y_PRESENTACION")
    if not saludo:
        return ok("saludo_format", "HARD",
                  "SALUDO_Y_PRESENTACION no presente (se valida en required_sections)")
    if len(saludo) < 3:
        return fail("saludo_format", "HARD",
                    f"SALUDO_Y_PRESENTACION tiene {len(saludo)} intervenciones; "
                    "se requieren al menos 3 separadas")
    pattern = re.compile(r"soy\s+(maria|maría|yago).*?(y\s+yo\s+soy|soy)\s+(maria|maría|yago)",
                          re.IGNORECASE | re.DOTALL)
    for iv in saludo:
        if pattern.search(iv.text):
            return fail("saludo_format", "HARD",
                        "Los dos nombres aparecen en la misma intervención del saludo")
    return ok("saludo_format", "HARD", "Formato de SALUDO_Y_PRESENTACION correcto")


def check_ia_warning(parts: ScriptParts, opener: str | None) -> ValidationResult:
    """Hard-fail si el aviso de IA no contiene las palabras clave o lo dice
    un speaker distinto del opener.

    Solo aplica a M y T (S no narra aviso — el spec S debe llamar a otra ruta).
    """
    saludo = parts.interventions("SALUDO_Y_PRESENTACION")
    if not saludo:
        return ok("ia_warning", "HARD", "Sin saludo (validado aparte)")
    keywords = ("sistema automatico", "puede contener errores")
    aviso_idx = None
    for idx, iv in enumerate(saludo):
        t = iv.text.lower()
        normalized = (t.replace("á", "a").replace("é", "e").replace("í", "i")
                      .replace("ó", "o").replace("ú", "u"))
        if all(k in normalized for k in keywords):
            aviso_idx = idx
            break
    if aviso_idx is None:
        return fail("ia_warning", "HARD",
                    "Falta el aviso de IA con las palabras clave obligatorias "
                    "'sistema automatico' y 'puede contener errores'")
    if opener and saludo[aviso_idx].speaker != opener:
        return fail("ia_warning", "HARD",
                    f"El aviso de IA lo dice {saludo[aviso_idx].speaker} pero "
                    f"debe decirlo el opener ({opener})")
    return ok("ia_warning", "HARD", "Aviso de IA correcto")


def check_pingpong(parts: ScriptParts, section: str, leader: str,
                   max_ratio: float = 1 / 3) -> ValidationResult:
    """Soft-warn si en un bloque liderado el apoyo interviene más de 1 cada 3
    veces que interviene el líder."""
    ivs = parts.interventions(section)
    if not ivs:
        return ok("pingpong", "SOFT", f"{section} no presente")
    leader_count = sum(1 for i in ivs if i.speaker == leader)
    support_count = sum(1 for i in ivs if i.speaker != leader)
    if leader_count == 0:
        return ok("pingpong", "SOFT", f"{section} sin líder presente")
    ratio = support_count / leader_count
    if ratio > max_ratio + 1e-9:
        return fail("pingpong", "SOFT",
                    f"{section}: ratio apoyo/líder = {ratio:.2f} (máximo {max_ratio:.2f})",
                    section=section, ratio=ratio)
    return ok("pingpong", "SOFT", f"{section}: ratio apoyo/líder OK")


def validate_common(parts: ScriptParts, *, episode_id: str, kind: str,
                    required_sections: list[str],
                    forbidden_sections: list[str],
                    expected_order: list[str],
                    word_min: int, word_max: int,
                    check_aviso_ia: bool = True) -> list[ValidationResult]:
    """Aplica las reglas comunes a los tres formatos. Devuelve la lista de
    `ValidationResult`.

    Los especialistas (`m_validator`, `t_validator`, `s_validator`) llaman a
    esta función y le concatenan sus reglas específicas.
    """
    results: list[ValidationResult] = []

    # Estructura del guion.
    results.append(check_required_sections(parts, required_sections))
    results.append(check_forbidden_sections(parts, forbidden_sections))
    results.append(check_section_order(parts, expected_order))
    results.append(check_word_count(parts, min_words=word_min, max_words=word_max))

    # Lista negra y placeholders.
    results.extend(blacklist.check_all(parts.intervention_texts(),
                                       parts.full_text))

    # Etiquetas TTS permitidas.
    results.append(check_tts_tags_allowed(parts))

    # Apellidos inventados.
    results.append(canonical_phrases.check_no_surnames(parts.full_text))

    # Paridad de apertura y aviso de IA (solo si hay HOOK y opener identificable).
    hook_ivs = parts.interventions("HOOK")
    opener = hook_ivs[0].speaker if hook_ivs else None
    if opener is not None:
        results.append(parity.check_opener(episode_id, kind, opener))

    # Reglas de audio sobre texto.
    results.extend(audio_rules.check_all(parts.intervention_texts()))

    # Frases canónicas (HOOK + CIERRE_FINAL aplican a M y T; S tiene su propio cierre).
    hook_text = parts.section_text("HOOK")
    if hook_text:
        results.append(canonical_phrases.check_hook_closing(hook_text))

    # Saludo y aviso (solo si el formato los lleva narrados).
    if check_aviso_ia:
        results.append(check_saludo_format(parts))
        results.append(check_ia_warning(parts, opener))

    return results
