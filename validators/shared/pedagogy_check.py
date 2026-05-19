"""Validación pedagógica: primera mención de términos técnicos en inglés
o siglas debe ir acompañada de su expansión o traducción cercana.

Regla SOFT (no bloqueante): si una primera mención no tiene expansión en
las ~200 chars circundantes, se reporta como warning para que el modelo
pueda corregir en retry.

Aplicable a M, T y S (cualquier formato). Usa el texto POST-OVERRIDES
(es decir, busca los términos en su forma fonética como aparecen en el
.txt final).
"""
from __future__ import annotations

import re

from validators.result import ValidationResult, fail, ok

# (regex_termino_post_override, regex_expansion_cerca, friendly_name)
# Lista curada de términos críticos. Si un término no aparece en el guion,
# la regla no se evalúa para él (no es fail por ausencia).
_CHECKS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    # Términos post-override (siglas deletreadas en castellano).
    ("ele ele eme",
     ("modelos de lenguaje", "grandes modelos", "large language", "language model"), "LLM"),
    ("rag",
     ("retrieval", "recuperaci[oó]n", "aumentad", "generaci[oó]n aumentada"), "RAG"),
    ("fain tiuning",
     ("ajuste fino", "ajustar", "afinar"), "fine-tuning"),
    ("embedin",
     ("representaci[oó]n", "vector", "incrustaci[oó]n", "embedd"), "embedding"),
    ("ge pe te",
     ("generative pre", "transformador generativo", "modelo generativo"), "GPT"),
    ("paiplain",
     ("secuencia", "tuber[ií]a", "flujo", "cadena"), "pipeline"),
    ("a pe i",
     ("interfaz",), "API"),
    ("ge pe u",
     ("unidad de procesamiento", "tarjeta gráfica"), "GPU"),
    ("deitaset",
     ("conjunto de datos",), "dataset"),
    ("erre ele ache efe",
     ("reinforcement learning from human", "aprendizaje por refuerzo"), "RLHF"),
    ("eme ce pe",
     ("model context protocol", "protocolo"), "MCP"),
    ("ce o te",
     ("chain.of.thought", "cadena de pensamiento", "razonamiento paso a paso"), "CoT"),
    ("jota ese o ene",
     ("formato",), "JSON"),
    ("fréimuork",
     ("marco de trabajo",), "framework"),
    ("dropáut",
     ("apagado aleatorio", "regularizaci[oó]n"), "dropout"),
    ("fiu shot",
     ("pocos ejemplos",), "few-shot"),
    ("pe ce a",
     ("análisis de componentes", "principal component"), "PCA"),
    ("hache i te ele",
     ("humano en el bucle", "human.in.the.loop"), "HITL"),
)

_WINDOW_CHARS = 250  # caracteres a ambos lados de la primera mención


def _find_first(text: str, term: str) -> int | None:
    pattern = re.compile(rf'(?<![\w]){re.escape(term)}(?![\w])', re.IGNORECASE)
    m = pattern.search(text)
    return m.start() if m else None


def _expansion_near(text: str, pos: int, expansions: tuple[str, ...]) -> bool:
    chunk = text[max(0, pos - _WINDOW_CHARS): pos + _WINDOW_CHARS]
    for exp in expansions:
        if re.search(exp, chunk, re.IGNORECASE):
            return True
    return False


def check_first_mention_expansion(text: str) -> ValidationResult:
    """SOFT-fail si una primera mención de término técnico no tiene
    su expansión/traducción en las ~250 chars circundantes.

    Solo evalúa términos que efectivamente aparecen en el texto. Si un
    término no aparece, no se cuenta como fail.
    """
    if not text:
        return ok("pedagogy_first_mention", "SOFT",
                  "Sin texto que analizar")
    unexpanded: list[str] = []
    for term, expansions, friendly in _CHECKS:
        pos = _find_first(text, term)
        if pos is None:
            continue
        if not _expansion_near(text, pos, expansions):
            unexpanded.append(friendly)
    if not unexpanded:
        return ok(
            "pedagogy_first_mention", "SOFT",
            "Todas las primeras menciones tienen expansión cercana",
        )
    return fail(
        "pedagogy_first_mention", "SOFT",
        f"Primera mención sin expansión cercana: {', '.join(unexpanded)}",
        unexpanded=unexpanded,
    )
