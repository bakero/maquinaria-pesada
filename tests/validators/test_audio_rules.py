"""Tests de validators/shared/audio_rules.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators.shared import audio_rules as ar  # noqa: E402

_LONG = ("Esta intervención de desarrollo tiene varias frases de longitud media "
         "para no disparar ninguna advertencia del validador de audio. "
         "Cada frase se mantiene por encima del umbral corto y por debajo del "
         "límite largo de treinta y dos palabras que marca el invariante. "
         "El conjunto supera de sobra el umbral de lo que sería una reacción.")


def test_digits_in_speech_detected():
    r = ar.check_digits_in_speech(["[directo] El 80 por ciento... no, el 80%."])
    assert r.passed is False
    assert r.severity == "SOFT"


def test_digits_in_speech_clean_passes():
    r = ar.check_digits_in_speech(
        ["[directo] El ochenta por ciento de las empresas usa inteligencia "
         "artificial de alguna forma."])
    assert r.passed is True


def test_digits_allowed_with_publication_marker():
    # Año de paper con marcador previo: permitido.
    r = ar.check_digits_in_speech(
        ["[explicativo] El paper de Vaswani de 2017 introdujo los Transformers."])
    assert r.passed is True


def test_reaction_over_limit_fails():
    # ≤2 frases pero claramente más de 15 palabras: reacción demasiado larga.
    intervention = ("Pues mira, eso que dices me parece bastante discutible la "
                    "verdad, y la mayoría de la gente tampoco lo ve nada claro.")
    r = ar.check_reaction_length([intervention])
    assert r.passed is False
    assert r.severity == "HARD"


def test_reaction_within_limit_passes():
    r = ar.check_reaction_length(["¿Y eso por qué pasa?"])
    assert r.passed is True


def test_long_development_intervention_not_flagged_as_reaction():
    # Intervención larga (>2 frases) no es reacción: no la marca reaction_length.
    text = _LONG + " Y aquí añadimos otra frase más. Y una tercera para cerrar."
    r = ar.check_reaction_length([text])
    assert r.passed is True


def test_intervention_over_max_words_soft_warn():
    huge = " ".join(["palabra"] * 250)
    r = ar.check_intervention_max_words([huge], max_words=200)
    assert r.passed is False
    assert r.severity == "SOFT"


def test_intervention_under_max_words_passes():
    r = ar.check_intervention_max_words([_LONG], max_words=200)
    assert r.passed is True


def test_long_sentence_soft_warn():
    long_sentence = " ".join(["x"] * 40) + "."
    r = ar.check_long_sentences([long_sentence], max_words_per_sentence=32)
    assert r.passed is False
    assert r.severity == "SOFT"


def test_short_sentences_within_limit_pass():
    text = "Una. Dos cosas. Tres aquí."
    r = ar.check_consecutive_short_sentences([text], max_consecutive=3)
    assert r.passed is True


def test_too_many_consecutive_short_sentences_soft_warn():
    text = "Una. Dos. Tres. Cuatro. Cinco."
    r = ar.check_consecutive_short_sentences([text], max_consecutive=3)
    assert r.passed is False
    assert r.severity == "SOFT"


def test_check_all_returns_five_results():
    results = ar.check_all([_LONG])
    assert len(results) == 5
    # con una intervención limpia de desarrollo, todas pasan
    assert all(r.passed for r in results)
