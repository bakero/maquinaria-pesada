"""Tests del parser del evaluador."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluador.parser import parse_script


@pytest.fixture
def m_script(tmp_path: Path) -> Path:
    content = """# HOOK
MARIA: [grave] Esto es un hook. Esto es MaquinarIA Pesada. Arrancamos.

# INTRO_SONIDO
[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]

# SALUDO_Y_PRESENTACION
MARIA: [natural] Hola soy Maria.
IAGO: [natural] Y yo soy Yago.
MARIA: [firme] Este podcast lo genera un sistema automatico de IA y puede contener errores.

# BLOQUE_PANORAMA
IAGO: [didactico] Esto es panorama largo Yago lidera el bloque.
MARIA: [conversacional] Apoyo breve.
"""
    p = tmp_path / "M1.txt"
    p.write_text(content, encoding="utf-8")
    return p


def test_parse_m_sections(m_script: Path):
    script = parse_script(m_script, "M")
    assert [s.name for s in script.sections] == [
        "HOOK",
        "INTRO_SONIDO",
        "SALUDO_Y_PRESENTACION",
        "BLOQUE_PANORAMA",
    ]
    assert script.metadata["module_number"] == 1
    assert script.metadata["opener"] == "MARIA"


def test_parse_intervention_tags(m_script: Path):
    script = parse_script(m_script, "M")
    saludo = script.section_by_name("SALUDO_Y_PRESENTACION")
    assert saludo is not None
    assert len(saludo.interventions) == 3
    assert saludo.interventions[0].speaker == "MARIA"
    assert saludo.interventions[0].tag == "natural"
    assert "Hola soy Maria" in saludo.interventions[0].clean_text


def test_speaker_normalization(tmp_path: Path):
    content = """# HOOK
YAGO: [grave] Yo soy Yago. Esto es MaquinarIA Pesada. Arrancamos.
MARÍA: [natural] Hola.
"""
    p = tmp_path / "M1.txt"
    p.write_text(content, encoding="utf-8")
    script = parse_script(p, "M")
    hook = script.section_by_name("HOOK")
    assert hook.interventions[0].speaker == "IAGO"
    assert hook.interventions[1].speaker == "MARIA"


def test_parse_angle_bracket_tags(tmp_path: Path):
    content = """# HOOK
MARIA: <conversacional> Hook con angle brackets.
"""
    p = tmp_path / "M2.txt"
    p.write_text(content, encoding="utf-8")
    script = parse_script(p, "M")
    hook = script.section_by_name("HOOK")
    assert hook.interventions[0].tag == "conversacional"


def test_parse_s_paragraphs(tmp_path: Path):
    content = """¿Qué es rag? Es recuperación aumentada por generación. Una pregunta corta.

rag es una técnica que combina dos procesos. Primero búsqueda, luego generación. Más detalle aquí para llegar al rango.

Imagina un chatbot. Sin rag, repite patrones. Con rag, accede a datos reales y responde mejor. Eso es un ejemplo claro de su uso.

Empresas lo usan ya en producción. Más sobre rag en el episodio T de MaquinarIA Pesada.
"""
    p = tmp_path / "S99_test.txt"
    p.write_text(content, encoding="utf-8")
    script = parse_script(p, "S")
    assert len(script.sections) == 4
    assert script.sections[0].name == "HOOK"
    assert script.sections[3].name == "APLICACION_GANCHO"


def test_word_count(m_script: Path):
    script = parse_script(m_script, "M")
    assert script.total_word_count > 0
    # contar palabras en HOOK manualmente: "Esto es un hook Esto es MaquinarIA Pesada Arrancamos" = 9 palabras
    hook = script.section_by_name("HOOK")
    assert hook.word_count == 9


def test_break_and_comments_stripped_for_word_count(tmp_path: Path):
    content = """# HOOK
MARIA: [grave] Una <break time="500ms"/> dos [comentario] tres.
"""
    p = tmp_path / "M3.txt"
    p.write_text(content, encoding="utf-8")
    script = parse_script(p, "M")
    hook = script.section_by_name("HOOK")
    # Solo "Una dos tres" = 3 palabras
    assert hook.word_count == 3
