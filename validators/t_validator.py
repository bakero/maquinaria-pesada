"""Validador específico de episodios T (Tema) — spec v6.

Composición: llama a `base_validator.validate_common()` con los parámetros de T
y añade las reglas específicas del formato (6 bloques de contenido, CASOS,
LIMITES, FUENTES, leader shares).
"""
from __future__ import annotations

import re

from validators import base_validator as bv
from validators.parser import ScriptParts, count_words, parse_script, speaker_share
from validators.result import ValidationResult, fail, ok

REQUIRED_SECTIONS: list[str] = [
    "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
    "BLOQUE_PANORAMA", "BLOQUE_COMO", "BLOQUE_CASOS", "BLOQUE_LIMITES",
    "BLOQUE_FUENTES", "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES",
]
FORBIDDEN_SECTIONS: list[str] = [
    "BLOQUE_1", "BLOQUE_2", "BLOQUE_3", "BLOQUE_4",
    "BLOQUE_QUE", "BLOQUE_TEMAS_CLAVE", "BLOQUE_DESTACADO", "BLOQUE_REALIDAD",
    "INSERCION_1", "INSERCION_2", "INSERCION_3", "INSERCION_EMPRESA",
    "APLICACION_PRACTICA",
]

WORD_COUNT_HARD = (2925, 4485)
WORD_COUNT_TARGET = (3700, 4500)

CONCEPTS_COUNT_EXACT = 3
FUENTES_COUNT_EXACT = 3

LEADER_SHARE_PANORAMA_MIN = 0.65
LEADER_SHARE_COMO_BAND = (0.40, 0.60)
LEADER_SHARE_CASOS_MIN = 0.60
LEADER_SHARE_LIMITES_MIN = 0.55

CASOS_MIN_COMPANY_CASES = 2

# Patrones semánticos esperados en BLOQUE_LIMITES.
LIMITES_SEMANTIC_PATTERNS = (
    "no es", "no debe confundirse", "el error común es", "el error comun es",
    "cuando no", "no aplica", "no sirve", "no vale", "se confunde con",
)


def _count_concepts(parts: ScriptParts) -> int:
    return len(parts.interventions("CIERRE_CONCEPTOS"))


def check_concepts_exact_3(parts: ScriptParts) -> ValidationResult:
    n = _count_concepts(parts)
    if n == CONCEPTS_COUNT_EXACT:
        return ok("t_concepts_count_exact_3", "HARD",
                  "CIERRE_CONCEPTOS tiene exactamente 3 conceptos")
    return fail("t_concepts_count_exact_3", "HARD",
                f"CIERRE_CONCEPTOS tiene {n} conceptos; T exige exactamente 3",
                count=n)


def check_concepts_opening(parts: ScriptParts) -> ValidationResult:
    from validators.shared import canonical_phrases
    return canonical_phrases.check_concepts_opening(
        parts.section_text("CIERRE_CONCEPTOS"))


def check_final_closing(parts: ScriptParts) -> ValidationResult:
    from validators.shared import canonical_phrases
    return canonical_phrases.check_final_closing(
        parts.section_text("CIERRE_FINAL"))


def check_leader_shares(parts: ScriptParts) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    panorama = parts.interventions("BLOQUE_PANORAMA")
    if panorama:
        s = speaker_share(panorama, "IAGO")
        if s + 1e-9 >= LEADER_SHARE_PANORAMA_MIN:
            results.append(ok("t_leader_panorama", "HARD",
                              f"PANORAMA: Yago {s:.0%} ≥ 65%"))
        else:
            results.append(fail("t_leader_panorama", "HARD",
                                f"PANORAMA: Yago {s:.0%} < 65%"))

    como = parts.interventions("BLOQUE_COMO")
    if como:
        s = speaker_share(como, "IAGO")
        lo, hi = LEADER_SHARE_COMO_BAND
        if lo - 1e-9 <= s <= hi + 1e-9:
            results.append(ok("t_leader_como", "HARD",
                              f"COMO: balance {s:.0%} en 40-60%"))
        else:
            results.append(fail("t_leader_como", "HARD",
                                f"COMO: balance {s:.0%} fuera de 40-60%"))

    casos = parts.interventions("BLOQUE_CASOS")
    if casos:
        s = speaker_share(casos, "MARIA")
        if s + 1e-9 >= LEADER_SHARE_CASOS_MIN:
            results.append(ok("t_leader_casos", "HARD",
                              f"CASOS: Maria {s:.0%} ≥ 60%"))
        else:
            results.append(fail("t_leader_casos", "HARD",
                                f"CASOS: Maria {s:.0%} < 60%"))

    limites = parts.interventions("BLOQUE_LIMITES")
    if limites:
        s = speaker_share(limites, "IAGO")
        if s + 1e-9 >= LEADER_SHARE_LIMITES_MIN:
            results.append(ok("t_leader_limites", "HARD",
                              f"LIMITES: Yago {s:.0%} ≥ 55%"))
        else:
            results.append(fail("t_leader_limites", "HARD",
                                f"LIMITES: Yago {s:.0%} < 55%"))

    return results


def _count_company_names(text: str) -> int:
    """Cuenta nombres de empresas con mayúscula inicial en el bloque CASOS.

    Heurística: tokens capitalizados frecuentes en el corpus tech (OpenAI,
    Anthropic, Google, etc.) o nombres en CamelCase que no sean inicio de frase.
    """
    # Lista de empresas habituales para detección directa.
    known = (
        "OpenAI", "Anthropic", "Google", "Meta", "Microsoft", "IBM", "Amazon",
        "Apple", "DeepMind", "Hugging Face", "Stability AI", "Cohere", "Mistral",
        "Stanford", "MIT", "Gartner", "McKinsey", "Forrester", "IDC",
        "Spotify", "Netflix", "Airbnb", "Uber", "Tesla", "Salesforce",
        "Oracle", "SAP", "Adobe", "BBVA", "Santander", "Telefonica",
        "Telefónica", "Banco", "Repsol", "Iberdrola",
    )
    found = set()
    for company in known:
        if re.search(rf"\b{re.escape(company)}\b", text):
            found.add(company)
    return len(found)


def check_casos_company_count(parts: ScriptParts) -> ValidationResult:
    """Hard-fail si BLOQUE_CASOS no menciona ≥2 empresas con nombre propio."""
    text = parts.section_text("BLOQUE_CASOS")
    if not text:
        return ok("t_casos_company_count", "HARD",
                  "BLOQUE_CASOS no presente (validado aparte)")
    n = _count_company_names(text)
    if n >= CASOS_MIN_COMPANY_CASES:
        return ok("t_casos_company_count", "HARD",
                  f"BLOQUE_CASOS menciona {n} empresas reconocibles")
    return fail("t_casos_company_count", "HARD",
                f"BLOQUE_CASOS menciona {n} empresas; se requieren al menos "
                f"{CASOS_MIN_COMPANY_CASES} con nombre propio",
                count=n)


def check_limites_semantic_patterns(parts: ScriptParts) -> ValidationResult:
    """Soft-warn si BLOQUE_LIMITES no contiene ningún patrón semántico esperado."""
    text = parts.section_text("BLOQUE_LIMITES").lower()
    if not text:
        return ok("t_limites_semantic", "SOFT",
                  "BLOQUE_LIMITES no presente (validado aparte)")
    if any(p in text for p in LIMITES_SEMANTIC_PATTERNS):
        return ok("t_limites_semantic", "SOFT",
                  "BLOQUE_LIMITES contiene patrones de 'qué NO es'")
    return fail("t_limites_semantic", "SOFT",
                "BLOQUE_LIMITES no contiene patrones tipo 'no es', "
                "'no debe confundirse con', 'el error común es'")


def _count_fuentes(parts: ScriptParts) -> int:
    """Cuenta fuentes en BLOQUE_FUENTES por años distintos mencionados."""
    from validators.m_validator import _count_fuentes as _m_count
    return _m_count(parts)


def check_fuentes_count_exact_3(parts: ScriptParts) -> ValidationResult:
    if "BLOQUE_FUENTES" not in parts.sections:
        return ok("t_fuentes_count_exact_3", "HARD",
                  "BLOQUE_FUENTES no presente (validado aparte)")
    n = _count_fuentes(parts)
    if n == FUENTES_COUNT_EXACT:
        return ok("t_fuentes_count_exact_3", "HARD",
                  "BLOQUE_FUENTES tiene exactamente 3 fuentes")
    return fail("t_fuentes_count_exact_3", "HARD",
                f"BLOQUE_FUENTES detecta {n} fuentes; T exige exactamente 3",
                count=n)


def check_no_urls_in_fuentes(parts: ScriptParts) -> ValidationResult:
    text = parts.section_text("BLOQUE_FUENTES")
    if not text:
        return ok("t_fuentes_no_urls", "SOFT", "Sin BLOQUE_FUENTES")
    if re.search(r"https?://|www\.|punto\s+com", text, re.IGNORECASE):
        return fail("t_fuentes_no_urls", "SOFT",
                    "BLOQUE_FUENTES contiene URLs en el habla")
    return ok("t_fuentes_no_urls", "SOFT", "Sin URLs en BLOQUE_FUENTES")


def check_aviso_duration(parts: ScriptParts,
                         min_words: int = 30, max_words: int = 50) -> ValidationResult:
    """Soft-warn si el aviso (advertencia T) está fuera de rango 12-18s."""
    saludo = parts.interventions("SALUDO_Y_PRESENTACION")
    for iv in saludo:
        t = iv.text.lower()
        normalized = (t.replace("á", "a").replace("é", "e").replace("í", "i")
                      .replace("ó", "o").replace("ú", "u"))
        if "sistema automatico" in normalized and "puede contener errores" in normalized:
            wc = count_words(iv.text)
            if min_words <= wc <= max_words:
                return ok("t_aviso_duration", "SOFT",
                          f"Aviso IA advertencia con {wc} palabras (~12-18s)")
            return fail("t_aviso_duration", "SOFT",
                        f"Aviso IA con {wc} palabras (objetivo 30-50 = 12-18s)",
                        words=wc)
    return fail("t_aviso_duration", "SOFT",
                "No se encontró la intervención del aviso para medir su duración")


def validate(script_text: str, episode_id: str) -> list[ValidationResult]:
    """Aplica todas las reglas v6 del formato T sobre el guion."""
    parts = parse_script(script_text)
    results = bv.validate_common(
        parts, episode_id=episode_id, kind="T",
        required_sections=REQUIRED_SECTIONS,
        forbidden_sections=FORBIDDEN_SECTIONS,
        expected_order=REQUIRED_SECTIONS,
        word_min=WORD_COUNT_HARD[0], word_max=WORD_COUNT_HARD[1],
        check_aviso_ia=True,
    )
    # Reglas específicas T
    results.append(check_concepts_exact_3(parts))
    results.append(check_concepts_opening(parts))
    results.append(check_final_closing(parts))
    results.extend(check_leader_shares(parts))
    results.append(check_casos_company_count(parts))
    results.append(check_limites_semantic_patterns(parts))
    results.append(check_fuentes_count_exact_3(parts))
    results.append(check_no_urls_in_fuentes(parts))
    results.append(check_aviso_duration(parts))
    # Anti-pingpong en los bloques liderados claramente
    results.append(bv.check_pingpong(parts, "BLOQUE_PANORAMA", "IAGO"))
    results.append(bv.check_pingpong(parts, "BLOQUE_CASOS", "MARIA"))
    results.append(bv.check_pingpong(parts, "BLOQUE_LIMITES", "IAGO"))
    return results
