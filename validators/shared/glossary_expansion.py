"""Regla §13.1 v6.1 — expansión castellana de siglas al primer uso.

Detecta que la PRIMERA mención de cada sigla del glosario en el guion va
acompañada de su expansión castellana en aposición con comas.

Formato canónico esperado:
    "los LLM, modelos de lenguaje grandes, han revolucionado..."
    "el RAG, generación aumentada por recuperación, permite..."

Aplicabilidad:
- M y T (no S — el Short cubre un único término ya definido en el body).

Permisividad:
- Si una entrada del glosario NO tiene expansión castellana disponible
  (ni campo `**ES:**` ni heading bilingüe `X / Y`), no se exige expansión
  para esa sigla → rollout gradual.

Tolerancia:
- La expansión esperada se compara por palabras-clave del campo `**ES:**`
  con normalización sin acentos. Acepta paráfrasis razonable cuando ≥70%
  de las palabras significativas (>3 caracteres) de la expansión esperada
  aparecen en la aposición detectada.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from generadores.shared.fuentes_loader import GlosarioEntry, load_glosario
from validators.result import ValidationResult, fail, ok

# Tags TTS que pueden preceder a una intervención.
_TAG_PREFIX_RE = re.compile(r"\[[^\]]+\]")

# Captura la sigla seguida de una aposición con comas: ", expansión, ".
# Aceptamos hasta 12 palabras dentro de la aposición y permitimos números,
# guiones y caracteres latinos con acentos.
_APPOSITION_TEMPLATE = (
    r"\b{sigla}\b"
    r"\s*,\s*"
    r"(?P<expansion>[\wáéíóúñüÁÉÍÓÚÑÜ\s\-]{{3,120}}?)"
    r"\s*,"
)

# Stopwords a descartar al comparar paráfrasis.
_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "y", "o", "u", "e", "en", "a", "por",
    "para", "con", "sin", "que", "lo", "se", "su", "sus",
    "es", "son", "ser", "estar",
}


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _significant_words(text: str) -> set[str]:
    norm = _normalize(text)
    norm = re.sub(r"[^\w\s\-]", " ", norm)
    words = norm.split()
    return {w for w in words if len(w) > 3 and w not in _STOPWORDS}


def _looks_like_expansion(detected: str, expected: str,
                          tolerance: float = 0.7) -> bool:
    """¿La aposición detectada se parece a la expansión esperada?

    Compara conjuntos de palabras significativas. Pasa si al menos `tolerance`
    de las palabras esperadas aparece en la detectada.
    """
    exp_words = _significant_words(expected)
    if not exp_words:
        return False
    det_words = _significant_words(detected)
    if not det_words:
        return False
    overlap = exp_words & det_words
    return len(overlap) / len(exp_words) >= tolerance


def _strip_tags(text: str) -> str:
    """Quita marcas [tag] de una intervención para análisis posterior."""
    return _TAG_PREFIX_RE.sub("", text)


def _candidate_siglas(entries: Iterable[GlosarioEntry]) -> list[tuple[str, str]]:
    """Devuelve los pares (sigla, expansion_castellana) candidatos a verificar.

    Solo aplica si la entrada tiene sigla canónica (paréntesis en heading)
    Y expansión castellana disponible (campo `**ES:**` o heading bilingüe).
    """
    out: list[tuple[str, str]] = []
    for entry in entries:
        if not entry.needs_first_use_expansion:
            continue
        expansion = entry.expansion_castellana
        if not expansion:
            continue
        sigla = entry.sigla or entry.name.split("/")[0].strip()
        # Las siglas suelen ser palabras-token clean; descartamos tokens raros.
        if not re.match(r"^[A-Za-z][A-Za-z0-9\-]{1,15}$", sigla):
            continue
        out.append((sigla, expansion))
    return out


def _find_first_occurrence(text: str, sigla: str) -> int:
    """Devuelve la posición del primer match de la sigla como palabra completa,
    o -1 si no aparece.
    """
    m = re.search(rf"\b{re.escape(sigla)}\b", text)
    return m.start() if m else -1


def check_glossary_term_first_use_expanded(
    full_text: str,
    glossary: list[GlosarioEntry] | None = None,
    excluded_sections: tuple[str, ...] = ("HOOK", "INTRO_SONIDO", "VERIFICACIONES"),
) -> ValidationResult:
    """Hard-fail si una sigla del glosario aparece sin expansión castellana
    en su primer uso del guion.

    Si `glossary` es None, carga el glosario por defecto.

    Las menciones dentro de las secciones `excluded_sections` no cuentan como
    "primer uso" (el hook puede usar la sigla sin expandir si se expande
    luego en SALUDO o PANORAMA).
    """
    if glossary is None:
        glossary = load_glosario()
    candidates = _candidate_siglas(glossary)
    if not candidates:
        return ok("glossary_term_first_use_expanded", "HARD",
                  "Sin siglas con expansión castellana en el glosario "
                  "(o todas pendientes de migración a **ES:**)")

    # Construir mapa sección → rango (start, end) en `full_text` para descartar
    # menciones en secciones excluidas.
    section_re = re.compile(r"^#\s+([A-Z_]+)\s*$", re.MULTILINE)
    section_spans: list[tuple[str, int, int]] = []
    matches = list(section_re.finditer(full_text))
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section_spans.append((name, start, end))

    def position_section(pos: int) -> str | None:
        for name, start, end in section_spans:
            if start <= pos < end:
                return name
        return None

    text_clean = _strip_tags(full_text)
    offenders: list[dict] = []

    for sigla, expansion in candidates:
        first_pos = _find_first_occurrence(text_clean, sigla)
        if first_pos < 0:
            continue
        # ¿La primera mención cae en una sección excluida? si es así, buscamos
        # la siguiente mención fuera de esas secciones.
        next_pos = first_pos
        while True:
            section = position_section(next_pos)
            if section is None or section not in excluded_sections:
                break
            # Buscar siguiente match.
            m_next = re.search(
                rf"\b{re.escape(sigla)}\b",
                text_clean[next_pos + len(sigla):],
            )
            if not m_next:
                next_pos = -1
                break
            next_pos = next_pos + len(sigla) + m_next.start()
        if next_pos < 0:
            # Solo aparece en secciones excluidas — no exigimos expansión.
            continue
        # Verificar si la aposición con comas aparece JUNTO a la primera
        # mención efectiva. Tomamos una ventana de 150 chars desde la sigla.
        window = text_clean[next_pos: next_pos + 200]
        appo_re = re.compile(_APPOSITION_TEMPLATE.format(sigla=re.escape(sigla)),
                              re.IGNORECASE)
        m_appo = appo_re.search(window)
        if m_appo and _looks_like_expansion(m_appo.group("expansion"), expansion):
            continue  # OK — se expandió correctamente al primer uso.
        # Sin expansión válida en el primer uso.
        offenders.append({
            "sigla": sigla,
            "expected_es": expansion,
            "position": next_pos,
            "context": text_clean[max(0, next_pos - 30): next_pos + 120],
        })

    if offenders:
        siglas_fail = sorted({o["sigla"] for o in offenders})
        return fail(
            "glossary_term_first_use_expanded", "HARD",
            f"{len(offenders)} sigla(s) del glosario sin expansión castellana "
            f"al primer uso: {', '.join(siglas_fail)}. "
            "Formato esperado: 'los <sigla>, <expansión castellana>, ...'",
            offenders=offenders,
        )
    return ok("glossary_term_first_use_expanded", "HARD",
              "Todas las siglas del glosario se expanden al primer uso")
