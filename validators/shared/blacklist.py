"""Lista negra de interjecciones (anti-NotebookLM) y frases-placeholder.

Reglas A.1 + §13 editorial del cuadro consolidado v6.1. Aplica a M, T y S.

Las 8 interjecciones-coro originales detectan validación-eco entre speakers
(intervención corta dominada por la interjección). Desde v6.1 se añaden 3
listas más (AI bro, coach, intriga manufacturada) provenientes de la capa
editorial; éstas se detectan al inicio de intervención sin requisito de
brevedad cuando la frase prohibida tiene ≥3 palabras.

Ver `EVALUADOR_EDITORIAL_GUIONES.md §1.4` y `PODCAST_MASTER_SPEC.md §13.2`.
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

# v6.1 — frases AI-bro pomposas. HARD-FAIL si una intervención empieza con
# alguna de éstas (tras opcional [tag]). Lista extensible.
BLACKLIST_AI_BRO_PHRASES: tuple[str, ...] = (
    "en el mundo actual de la ia",
    "sin mas preambulos",   # "sin más preámbulos" normalizado
    "es importante destacar que",
    "cabe mencionar",
)

# v6.1 — frases coach motivacional. HARD-FAIL en mismo formato.
# ("tienes toda la razón" ya cubierta por BLACKLIST_INTERJECTIONS).
BLACKLIST_COACH_PHRASES: tuple[str, ...] = (
    "excelente pregunta",
    "espero que esto te ayude",
    "adelante con tu proyecto",
)

# v6.1 — cliffhangers artificiales. HARD-FAIL si la intervención empieza con
# uno de éstos sin referenciar un T concreto del módulo a continuación.
BLACKLIST_CLIFFHANGER_PHRASES: tuple[str, ...] = (
    "stay tuned",
    "lo veremos en proximos episodios",  # "próximos" normalizado
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


def _starts_with_phrase(intervention: str, phrase_norm: str,
                        require_short_max_words: int = 6) -> bool:
    """Verifica si una intervención empieza por una frase prohibida.

    Reglas v6.1:
    - Se quita el `[tag]` inicial y se normaliza el cuerpo (sin acentos,
      minúsculas, sin puntuación lateral).
    - Si la frase prohibida tiene ≥3 palabras, basta con que la intervención
      empiece por ella, sin requisito de brevedad.
    - Si la frase prohibida tiene ≤2 palabras (caso "exacto", "stay tuned"),
      la intervención completa debe tener como máximo `require_short_max_words`
      palabras — coherente con el patrón de interjecciones-coro.
    """
    body = re.sub(r"^\s*\[[^\]]+\]\s*", "", intervention).strip()
    norm = _normalize(body)
    norm = re.sub(r"[^\w\s]", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    if not norm:
        return False
    if not (norm == phrase_norm or norm.startswith(phrase_norm + " ")):
        return False
    n_phrase_words = len(phrase_norm.split())
    if n_phrase_words >= 3:
        return True
    # 1-2 palabras → exigir intervención corta.
    return len(norm.split()) <= require_short_max_words


def _check_phrase_list(
    interventions: list[str],
    phrases: tuple[str, ...],
    rule_name: str,
    label: str,
) -> ValidationResult:
    """Helper común para AI-bro / coach / cliffhanger."""
    offenders: list[dict] = []
    for idx, text in enumerate(interventions):
        for phrase in phrases:
            if _starts_with_phrase(text, phrase):
                offenders.append({
                    "index": idx,
                    "phrase": phrase,
                    "text": text[:80],
                })
                break
    if offenders:
        return fail(
            rule_name, "HARD",
            f"{len(offenders)} intervención(es) empiezan con frase prohibida "
            f"({label}): "
            + ", ".join(sorted({o['phrase'] for o in offenders})),
            offenders=offenders,
        )
    return ok(rule_name, "HARD", f"Sin frases prohibidas de {label}")


def check_ai_bro_phrases(interventions: list[str]) -> ValidationResult:
    """Hard-fail si una intervención empieza con frase AI-bro pomposa."""
    return _check_phrase_list(
        interventions, BLACKLIST_AI_BRO_PHRASES,
        "blacklist_ai_bro", "AI-bro",
    )


def check_coach_phrases(interventions: list[str]) -> ValidationResult:
    """Hard-fail si una intervención empieza con frase coach motivacional."""
    return _check_phrase_list(
        interventions, BLACKLIST_COACH_PHRASES,
        "blacklist_coach", "coach motivacional",
    )


def check_cliffhanger_phrases(interventions: list[str]) -> ValidationResult:
    """Hard-fail si una intervención empieza con cliffhanger artificial."""
    return _check_phrase_list(
        interventions, BLACKLIST_CLIFFHANGER_PHRASES,
        "blacklist_cliffhanger", "intriga manufacturada",
    )


def check_all(interventions: list[str], full_text: str) -> list[ValidationResult]:
    """Aplica las 5 comprobaciones de lista negra (2 originales + 3 editoriales v6.1)."""
    return [
        check_interjections(interventions),
        check_placeholder_phrases(full_text),
        check_ai_bro_phrases(interventions),
        check_coach_phrases(interventions),
        check_cliffhanger_phrases(interventions),
    ]
