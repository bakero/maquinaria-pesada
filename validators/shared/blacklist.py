"""Lista negra de interjecciones (anti-NotebookLM) y frases-placeholder.

Regla A.1 del cuadro consolidado v6. Aplica a M, T y S.

Las 8 interjecciones prohibidas son interjecciones de validación-coro: el
problema no es la palabra en sí (puede aparecer dentro de una frase con
sentido), sino su uso como intervención-eco que valida lo que dijo el otro
presentante. La detección es por intervención corta dominada por la
interjección.
"""
from __future__ import annotations

import re
import unicodedata

from validators.result import ValidationResult, fail, ok

# Las 8 interjecciones prohibidas (sin acentos para comparación normalizada).
BLACKLIST_INTERJECTIONS: tuple[str, ...] = (
    "exactamente",
    "claro que si",
    "muy bien dicho",
    "tienes toda la razon",
    "exacto",
    "por supuesto",
    "eso es",
    "totalmente",
)

# Frases-placeholder: textos genéricos de relleno que el generador a veces
# emite cuando no tiene material real. Coincidencia por prefijo normalizado.
BLACKLIST_PLACEHOLDER_PHRASES: tuple[str, ...] = (
    "Bien apuntado. Déjame añadir la perspectiva técnica aquí. Hay una capa de implementación",
    "La pregunta que planteas toca algo crítico del diseño. El contexto cambia todo en estos sistemas distribuidos",
    "Hay algo que me genera curiosidad en este punto. ¿Cómo conecta esto con lo que acabamos de ver? Porque la secuencia conceptual importa mucho aquí",
    "Eso me plantea una pregunta concreta. ¿Cómo se traslada esto al entorno real de producción? Hay una distancia entre el diseño en papel",
    "Déjame entender bien este punto antes de seguir. ¿Qué implica esto en la práctica concreta para las organizaciones",
)


def _normalize(text: str) -> str:
    """Minúsculas + sin acentos, para comparación robusta."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _is_coro_interjection(intervention: str) -> str | None:
    """Devuelve la interjección prohibida si la intervención es un eco-coro.

    Una intervención cuenta como coro si, quitando puntuación y la etiqueta
    [tag] inicial, su contenido es esencialmente la interjección (≤6 palabras
    y empieza por ella).
    """
    body = re.sub(r"^\s*\[[^\]]+\]\s*", "", intervention).strip()
    norm = _normalize(body)
    norm = re.sub(r"[^\w\s]", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    if not norm:
        return None
    words = norm.split()
    for term in BLACKLIST_INTERJECTIONS:
        if norm == term or norm.startswith(term + " "):
            if len(words) <= 6:
                return term
    return None


def check_interjections(interventions: list[str]) -> ValidationResult:
    """Hard-fail si alguna intervención es un eco-coro de la lista negra.

    `interventions` es la lista de textos de intervención del guion (una por
    turno de speaker), en orden.
    """
    offenders: list[dict] = []
    for idx, text in enumerate(interventions):
        term = _is_coro_interjection(text)
        if term is not None:
            offenders.append({"index": idx, "term": term, "text": text[:80]})
    if offenders:
        return fail(
            "blacklist_interjection", "HARD",
            f"{len(offenders)} interjección(es) de validación-coro prohibidas: "
            + ", ".join(sorted({o['term'] for o in offenders})),
            offenders=offenders,
        )
    return ok("blacklist_interjection", "HARD",
              "Sin interjecciones de validación-coro")


def check_placeholder_phrases(full_text: str) -> ValidationResult:
    """Hard-fail si aparece una frase-placeholder de relleno."""
    norm_text = _normalize(full_text)
    found: list[str] = []
    for phrase in BLACKLIST_PLACEHOLDER_PHRASES:
        if _normalize(phrase) in norm_text:
            found.append(phrase[:60])
    if found:
        return fail(
            "blacklist_placeholder_phrase", "HARD",
            f"{len(found)} frase(s)-placeholder de relleno detectadas",
            phrases=found,
        )
    return ok("blacklist_placeholder_phrase", "HARD",
              "Sin frases-placeholder de relleno")


def check_all(interventions: list[str], full_text: str) -> list[ValidationResult]:
    """Aplica las dos comprobaciones de lista negra."""
    return [
        check_interjections(interventions),
        check_placeholder_phrases(full_text),
    ]
