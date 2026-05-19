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


def test_check_all_returns_five_results():
    """v6.1: check_all devuelve 5 resultados (2 originales + 3 editoriales)."""
    results = blacklist.check_all(["[natural] Hola."], "texto completo")
    assert len(results) == 5
    assert {r.rule_name for r in results} == {
        "blacklist_interjection",
        "blacklist_placeholder_phrase",
        "blacklist_ai_bro",
        "blacklist_coach",
        "blacklist_cliffhanger",
    }


# ---------------------------------------------------------------------------
# v6.1 — listas negras editoriales (AI-bro, coach, cliffhanger)
# ---------------------------------------------------------------------------

def test_ai_bro_phrase_detected_at_start():
    interventions = [
        "[directo] En el mundo actual de la IA, todo cambia muy rápido.",
    ]
    r = blacklist.check_ai_bro_phrases(interventions)
    assert r.passed is False
    assert r.severity == "HARD"


def test_ai_bro_phrase_clean_passes():
    interventions = [
        "[explicativo] La cuestión técnica de fondo es cómo se entrena el modelo.",
    ]
    r = blacklist.check_ai_bro_phrases(interventions)
    assert r.passed is True


def test_ai_bro_long_phrase_detected_without_short_requirement():
    """Las frases prohibidas de ≥3 palabras se detectan al inicio aunque la
    intervención sea larga (a diferencia de la blacklist de interjecciones-
    coro). 'En el mundo actual de la IA' tiene 7 palabras y se bloquea
    aunque la intervención siga con contenido técnico legítimo."""
    interventions = [
        "[didactico] En el mundo actual de la IA, el entrenamiento de los "
        "modelos fundacionales requiere infraestructura especializada y "
        "datasets masivos curados en pipelines complejos.",
    ]
    r = blacklist.check_ai_bro_phrases(interventions)
    assert r.passed is False


def test_ai_bro_short_phrase_requires_short_intervention():
    """Las frases prohibidas de ≤2 palabras (caso 'Cabe mencionar') solo
    cuentan si la intervención es corta (≤6 palabras), igual que las
    interjecciones-coro. En frase larga 'cabe mencionar' es uso legítimo
    del idioma."""
    short = ["[directo] Cabe mencionar el caso."]
    long_intervention = [
        "[explicativo] Cabe mencionar también, antes de seguir, que el "
        "entrenamiento de un modelo de esta escala requiere recursos "
        "computacionales que la mayoría de empresas no tienen disponibles."
    ]
    assert blacklist.check_ai_bro_phrases(short).passed is False
    assert blacklist.check_ai_bro_phrases(long_intervention).passed is True


def test_coach_phrase_detected():
    interventions = ["[curioso] Excelente pregunta, vamos a verlo."]
    r = blacklist.check_coach_phrases(interventions)
    assert r.passed is False
    assert r.severity == "HARD"


def test_coach_phrase_clean_passes():
    r = blacklist.check_coach_phrases(["[directo] La diferencia clave es ésta."])
    assert r.passed is True


def test_cliffhanger_phrase_detected():
    interventions = ["[natural] Lo veremos en próximos episodios."]
    r = blacklist.check_cliffhanger_phrases(interventions)
    assert r.passed is False


def test_cliffhanger_clean_passes():
    """Mención a un T concreto NO debería marcarse — pero el detector actual
    solo mira el inicio. Un cliffhanger genuino siempre empieza con la frase
    prohibida; uno legítimo no."""
    r = blacklist.check_cliffhanger_phrases(
        ["[directo] Lo desarrollamos en el T sobre limitaciones de LLMs."]
    )
    assert r.passed is True


def test_short_blacklist_phrase_requires_short_intervention():
    """'Stay tuned' es ≤2 palabras, así que solo cuenta como cliffhanger si la
    intervención es corta (≤6 palabras), igual que las interjecciones-coro."""
    short = ["[directo] Stay tuned ahora."]
    long_intervention = [
        "[explicativo] Stay tuned no es un anglicismo que usemos aquí, "
        "porque el podcast cierra siempre con la frase canónica completa."
    ]
    assert blacklist.check_cliffhanger_phrases(short).passed is False
    # En frase larga "stay tuned" se considera mención legítima (mismo
    # criterio que 'exacto' dentro de una explicación técnica larga).
    assert blacklist.check_cliffhanger_phrases(long_intervention).passed is True


def test_blacklist_normalized_match_accents_and_case():
    """Los acentos en 'préambulos' / 'mas' se normalizan antes de comparar."""
    interventions = ["[natural] Sin más preámbulos, entramos al tema."]
    r = blacklist.check_ai_bro_phrases(interventions)
    assert r.passed is False
