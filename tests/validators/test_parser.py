"""Tests del parser de guiones."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators.parser import (  # noqa: E402
    count_words,
    parse_script,
    speaker_share,
)

SAMPLE = """\
# HOOK
IAGO: [directo] Esto es una intervención inicial del hook.
MARIA: [analitica] Y esta es la segunda intervención.

# INTRO_SONIDO
[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]

# SALUDO_Y_PRESENTACION
IAGO: [calido] Bienvenidos. Soy Yago.
MARIA: [calido] Y yo soy Maria.
IAGO: [serio] Antes de empezar, este es un sistema automatico que puede
contener errores.
"""


def test_parse_extracts_sections_in_order():
    p = parse_script(SAMPLE)
    assert p.section_order == ["HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION"]
    assert "HOOK" in p.sections
    assert "INTRO_SONIDO" in p.sections


def test_parse_extracts_interventions_per_section():
    p = parse_script(SAMPLE)
    hook = p.interventions("HOOK")
    assert len(hook) == 2
    assert hook[0].speaker == "IAGO"
    assert hook[1].speaker == "MARIA"
    saludo = p.interventions("SALUDO_Y_PRESENTACION")
    assert len(saludo) == 3


def test_parse_handles_multiline_intervention():
    p = parse_script(SAMPLE)
    last = p.interventions("SALUDO_Y_PRESENTACION")[-1]
    assert "sistema automatico" in last.text
    assert "puede" in last.text


def test_first_speaker_of_returns_opener():
    p = parse_script(SAMPLE)
    assert p.first_speaker_of("HOOK") == "IAGO"


def test_intervention_texts_filter_by_section():
    p = parse_script(SAMPLE)
    texts = p.intervention_texts("HOOK")
    assert len(texts) == 2
    assert all(t.startswith("[") for t in texts)


def test_count_words_excludes_tag():
    assert count_words("[didactico] Hola mundo") == 2


def test_count_words_handles_accents():
    assert count_words("inteligencia artificial") == 2
    assert count_words("[tag] análisis y producción") == 3


def test_speaker_share_proportional():
    p = parse_script(SAMPLE)
    saludo = p.interventions("SALUDO_Y_PRESENTACION")
    yago_share = speaker_share(saludo, "IAGO")
    maria_share = speaker_share(saludo, "MARIA")
    assert 0.0 < yago_share < 1.0
    assert 0.0 < maria_share < 1.0
    assert abs(yago_share + maria_share - 1.0) < 1e-9


def test_empty_text_returns_empty_parts():
    p = parse_script("")
    assert p.sections == {}
    assert p.all_interventions == []


def test_parse_handles_maria_with_accent():
    text = "# HOOK\nMARÍA: [tag] Hola."
    p = parse_script(text)
    ivs = p.interventions("HOOK")
    assert len(ivs) == 1
    assert ivs[0].speaker == "MARIA"
