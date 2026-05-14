"""Tests de validators/shared/blacklist.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators.shared import blacklist  # noqa: E402


def test_passes_with_clean_interventions():
    interventions = [
        "[didactico] Vamos a ver qué es un embedding y por qué importa tanto.",
        "[curioso] Pero entonces, ¿cómo se relaciona eso con la búsqueda semántica?",
    ]
    r = blacklist.check_interjections(interventions)
    assert r.passed is True


@pytest.mark.parametrize("term", list(blacklist.BLACKLIST_INTERJECTIONS))
def test_fails_on_each_blacklist_interjection(term):
    interventions = [f"[natural] {term}."]
    r = blacklist.check_interjections(interventions)
    assert r.passed is False
    assert r.severity == "HARD"


def test_fails_on_blacklist_with_tag_prefix():
    r = blacklist.check_interjections(["[analitica] Exactamente."])
    assert r.passed is False


def test_fails_on_capitalized_and_accented_variant():
    # "Claro que sí" con acento y mayúscula debe detectarse igual.
    r = blacklist.check_interjections(["Claro que sí, sin duda."])
    assert r.passed is False


def test_allows_blacklist_word_inside_real_sentence():
    # "exacto" dentro de una frase de desarrollo larga NO es coro.
    interventions = [
        "[explicativo] El modelo no devuelve un valor exacto sino una "
        "distribución de probabilidad sobre el vocabulario, y eso cambia "
        "cómo interpretamos su salida en producción real.",
    ]
    r = blacklist.check_interjections(interventions)
    assert r.passed is True


def test_placeholder_phrase_detected():
    text = (
        "IAGO: Bien apuntado. Déjame añadir la perspectiva técnica aquí. "
        "Hay una capa de implementación que no hemos cubierto."
    )
    r = blacklist.check_placeholder_phrases(text)
    assert r.passed is False
    assert r.severity == "HARD"


def test_placeholder_phrases_clean_text_passes():
    r = blacklist.check_placeholder_phrases("Un guion normal sin relleno.")
    assert r.passed is True


def test_check_all_returns_two_results():
    results = blacklist.check_all(["[natural] Hola."], "texto completo")
    assert len(results) == 2
    assert {r.rule_name for r in results} == {
        "blacklist_interjection", "blacklist_placeholder_phrase"}
