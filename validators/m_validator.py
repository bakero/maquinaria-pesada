"""Validador específico de episodios M (Módulo) — spec v6.

Composición: llama a `base_validator.validate_common()` con los parámetros de M
y añade las reglas específicas del formato.
"""
from __future__ import annotations

import re
from pathlib import Path

from validators import base_validator as bv
from validators.parser import ScriptParts, count_words, parse_script, speaker_share
from validators.result import ValidationResult, fail, ok

REQUIRED_SECTIONS: list[str] = [
    "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
    "BLOQUE_PANORAMA", "BLOQUE_DESTACADO", "APLICACION_PRACTICA",
    "BLOQUE_FUENTES", "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES",
]
FORBIDDEN_SECTIONS: list[str] = [
    "BLOQUE_1", "BLOQUE_2", "BLOQUE_3", "BLOQUE_4",
    "BLOQUE_QUE", "BLOQUE_COMO", "BLOQUE_LIMITES",
    "BLOQUE_TEMAS_CLAVE", "BLOQUE_REALIDAD", "BLOQUE_CASOS",
    "INSERCION_1", "INSERCION_2", "INSERCION_3", "INSERCION_EMPRESA",
]

WORD_COUNT_HARD = (2400, 3680)  # rango duro
WORD_COUNT_TARGET = (2700, 3300)

# Mínimo / máximo de conceptos en CIERRE_CONCEPTOS
CONCEPTS_MIN = 3
CONCEPTS_MAX = 5

# Reparto de líderes por bloque (palabras del líder / total del bloque).
LEADER_SHARE_PANORAMA_MIN = 0.65  # Yago lidera
LEADER_SHARE_DESTACADO_BAND = (0.40, 0.60)  # compartido
LEADER_SHARE_APLICACION = {
    "MARIA": (0.30, 0.40),
    "IAGO": (0.60, 0.70),
}

FUENTES_COUNT_MIN = 3
FUENTES_COUNT_MAX = 4


def _count_concepts(parts: ScriptParts) -> int:
    """Cuenta conceptos en CIERRE_CONCEPTOS: una intervención = un concepto."""
    return len(parts.interventions("CIERRE_CONCEPTOS"))


def check_concepts_count(parts: ScriptParts) -> ValidationResult:
    """Hard-fail si CIERRE_CONCEPTOS no tiene entre 3 y 5 conceptos."""
    n = _count_concepts(parts)
    if CONCEPTS_MIN <= n <= CONCEPTS_MAX:
        return ok("m_concepts_count", "HARD",
                  f"CIERRE_CONCEPTOS tiene {n} conceptos (rango 3-5)")
    return fail("m_concepts_count", "HARD",
                f"CIERRE_CONCEPTOS tiene {n} conceptos; M exige entre "
                f"{CONCEPTS_MIN} y {CONCEPTS_MAX}",
                count=n)


def check_concepts_opening(parts: ScriptParts) -> ValidationResult:
    """Hard-fail si CIERRE_CONCEPTOS no abre con la frase canónica."""
    from validators.shared import canonical_phrases
    return canonical_phrases.check_concepts_opening(
        parts.section_text("CIERRE_CONCEPTOS"))


def check_final_closing(parts: ScriptParts) -> ValidationResult:
    """Hard-fail si CIERRE_FINAL no incluye la frase canónica."""
    from validators.shared import canonical_phrases
    return canonical_phrases.check_final_closing(
        parts.section_text("CIERRE_FINAL"))


def check_leader_shares(parts: ScriptParts) -> list[ValidationResult]:
    """Conteo de líderes por bloque según el spec M."""
    results: list[ValidationResult] = []

    # PANORAMA → Yago ≥65%
    panorama = parts.interventions("BLOQUE_PANORAMA")
    if panorama:
        share = speaker_share(panorama, "IAGO")
        if share + 1e-9 >= LEADER_SHARE_PANORAMA_MIN:
            results.append(ok("m_leader_panorama", "HARD",
                              f"BLOQUE_PANORAMA: Yago {share:.0%} ≥ 65%"))
        else:
            results.append(fail("m_leader_panorama", "HARD",
                                f"BLOQUE_PANORAMA: Yago {share:.0%} < 65%"))

    # DESTACADO → compartido 40-60%
    destacado = parts.interventions("BLOQUE_DESTACADO")
    if destacado:
        share_y = speaker_share(destacado, "IAGO")
        lo, hi = LEADER_SHARE_DESTACADO_BAND
        if lo - 1e-9 <= share_y <= hi + 1e-9:
            results.append(ok("m_leader_destacado", "HARD",
                              f"BLOQUE_DESTACADO: balance {share_y:.0%} en banda 40-60%"))
        else:
            results.append(fail("m_leader_destacado", "HARD",
                                f"BLOQUE_DESTACADO: balance {share_y:.0%} fuera de 40-60%"))

    # APLICACION_PRACTICA → Maria 30-40%, Yago 60-70%
    aplic = parts.interventions("APLICACION_PRACTICA")
    if aplic:
        share_m = speaker_share(aplic, "MARIA")
        lo, hi = LEADER_SHARE_APLICACION["MARIA"]
        if lo - 1e-9 <= share_m <= hi + 1e-9:
            results.append(ok("m_leader_aplicacion", "HARD",
                              f"APLICACION_PRACTICA: Maria {share_m:.0%} en 30-40%"))
        else:
            results.append(fail("m_leader_aplicacion", "HARD",
                                f"APLICACION_PRACTICA: Maria {share_m:.0%} fuera de 30-40%"))

    return results


_APLIC_KEYWORDS = (
    "sistema que produce", "sistema que genera", "pipeline", "generador",
    "ese sistema", "este sistema",
)


def check_aplicacion_not_in_hook(parts: ScriptParts) -> ValidationResult:
    """Hard-fail si la aplicación práctica del sistema aparece ya en el HOOK."""
    hook = parts.section_text("HOOK").lower()
    if any(k in hook for k in _APLIC_KEYWORDS):
        return fail("m_aplicacion_in_hook", "HARD",
                    "La aplicación práctica del sistema NO debe aparecer en HOOK")
    return ok("m_aplicacion_in_hook", "HARD",
              "HOOK no contiene la aplicación práctica del sistema")


_YEAR_PATTERN = re.compile(
    r"\b(?:19\d{2}|20\d{2}|dos\s+mil(?:\s+\w+){0,3})\b",
    re.IGNORECASE,
)


def _count_fuentes(parts: ScriptParts) -> int:
    """Cuenta fuentes en BLOQUE_FUENTES por años distintos mencionados.

    Cada fuente cita en audio canónicamente un año (paper/informe/encuesta).
    Contamos años distintos (digit o "dos mil veintitres") como proxy de
    número de fuentes citadas.
    """
    text = parts.section_text("BLOQUE_FUENTES")
    if not text:
        return 0
    matches = [m.group(0).strip().lower() for m in _YEAR_PATTERN.finditer(text)]
    return len(set(matches))


def check_fuentes_count(parts: ScriptParts) -> ValidationResult:
    """Hard-fail si BLOQUE_FUENTES no tiene entre 3 y 4 fuentes detectables."""
    if "BLOQUE_FUENTES" not in parts.sections:
        return ok("m_fuentes_count", "HARD",
                  "BLOQUE_FUENTES no presente (lo valida required_sections)")
    n = _count_fuentes(parts)
    if FUENTES_COUNT_MIN <= n <= FUENTES_COUNT_MAX:
        return ok("m_fuentes_count", "HARD",
                  f"BLOQUE_FUENTES tiene {n} fuentes (rango 3-4)")
    return fail("m_fuentes_count", "HARD",
                f"BLOQUE_FUENTES detecta {n} fuentes; M exige entre "
                f"{FUENTES_COUNT_MIN} y {FUENTES_COUNT_MAX}",
                count=n)


def check_fuentes_marco_file(episode_id: str,
                              repo_root: Path | None = None) -> ValidationResult:
    """Hard-fail si no existe `PDFs/auxiliares/fuentes_marco_modulo_M{n}.md`."""
    m = re.match(r"^M(\d+)$", episode_id)
    if not m:
        return fail("m_fuentes_marco_file", "HARD",
                    f"No se pudo extraer número de módulo de '{episode_id}'")
    n = int(m.group(1))
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "PDFs" / "auxiliares" / f"fuentes_marco_modulo_M{n}.md"
    if path.exists():
        return ok("m_fuentes_marco_file", "HARD",
                  f"Existe {path.relative_to(repo_root).as_posix()}")
    return fail("m_fuentes_marco_file", "HARD",
                f"Falta el fichero obligatorio {path.relative_to(repo_root).as_posix()}",
                path=str(path))


def check_no_urls_in_fuentes(parts: ScriptParts) -> ValidationResult:
    """Soft-warn si en BLOQUE_FUENTES aparecen URLs/protocolos en el habla."""
    text = parts.section_text("BLOQUE_FUENTES")
    if not text:
        return ok("m_fuentes_no_urls", "SOFT", "Sin BLOQUE_FUENTES")
    if re.search(r"https?://|www\.|punto\s+com", text, re.IGNORECASE):
        return fail("m_fuentes_no_urls", "SOFT",
                    "BLOQUE_FUENTES contiene URLs en el habla")
    return ok("m_fuentes_no_urls", "SOFT", "Sin URLs en BLOQUE_FUENTES")


def check_aviso_duration(parts: ScriptParts,
                         min_words: int = 45, max_words: int = 75) -> ValidationResult:
    """Soft-warn si el aviso de IA (enganche M) está fuera del rango de palabras
    aproximado para 18-25 segundos."""
    saludo = parts.interventions("SALUDO_Y_PRESENTACION")
    for iv in saludo:
        t = iv.text.lower()
        normalized = (t.replace("á", "a").replace("é", "e").replace("í", "i")
                      .replace("ó", "o").replace("ú", "u"))
        if "sistema automatico" in normalized and "puede contener errores" in normalized:
            wc = count_words(iv.text)
            if min_words <= wc <= max_words:
                return ok("m_aviso_duration", "SOFT",
                          f"Aviso IA enganche con {wc} palabras (~18-25s)")
            return fail("m_aviso_duration", "SOFT",
                        f"Aviso IA con {wc} palabras (objetivo 45-75 = 18-25s)",
                        words=wc)
    return fail("m_aviso_duration", "SOFT",
                "No se encontró la intervención del aviso para medir su duración")


def validate(script_text: str, episode_id: str,
             repo_root: Path | None = None) -> list[ValidationResult]:
    """Aplica todas las reglas v6 del formato M sobre el guion."""
    parts = parse_script(script_text)
    results = bv.validate_common(
        parts, episode_id=episode_id, kind="M",
        required_sections=REQUIRED_SECTIONS,
        forbidden_sections=FORBIDDEN_SECTIONS,
        expected_order=REQUIRED_SECTIONS,
        word_min=WORD_COUNT_HARD[0], word_max=WORD_COUNT_HARD[1],
        check_aviso_ia=True,
    )
    # Reglas específicas M
    results.append(check_concepts_count(parts))
    results.append(check_concepts_opening(parts))
    results.append(check_final_closing(parts))
    results.extend(check_leader_shares(parts))
    results.append(check_aplicacion_not_in_hook(parts))
    results.append(check_fuentes_count(parts))
    results.append(check_fuentes_marco_file(episode_id, repo_root))
    results.append(check_no_urls_in_fuentes(parts))
    results.append(check_aviso_duration(parts))
    # Anti-pingpong en bloques liderados
    results.append(bv.check_pingpong(parts, "BLOQUE_PANORAMA", "IAGO"))
    return results
