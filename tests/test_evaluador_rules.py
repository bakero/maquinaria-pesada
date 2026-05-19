"""Tests integrados de las reglas del evaluador."""

from __future__ import annotations

from pathlib import Path

import pytest

from evaluador.parser import parse_script
from evaluador.rules import evaluate_all


def _make_m_v6_passing() -> str:
    """Construye un M mínimo que pase la mayoría de reglas estructurales."""
    panorama = " ".join(["yago lidera aqui."] * 90)  # mucho texto para Yago
    panorama_maria = " ".join(["maria pregunta breve."] * 10)
    destacado = " ".join(["yago habla."] * 60) + " " + " ".join(["maria comenta."] * 60)
    aplicacion_yago = " ".join(["yago detalla muchas cosas."] * 100)
    aplicacion_maria = " ".join(["maria conecta el sistema."] * 50)
    fuentes = " ".join(["fuente uno dos tres y cuatro."] * 40)
    return f"""# HOOK
MARIA: [grave] El ochenta por ciento de las organizaciones usa IA, segun McKinsey en dos mil veinticinco. Pero solo el treinta por ciento la escala. La brecha entre uso y valor es el problema central de este episodio. Esto es MaquinarIA Pesada. Arrancamos.

# INTRO_SONIDO
[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]

# SALUDO_Y_PRESENTACION
MARIA: [natural] Bienvenidos a MaquinarIA Pesada. Soy Maria. Hoy hablamos del modulo cero del master.
IAGO: [natural] Y yo soy Yago. Vamos a recorrer los fundamentos de la IA en este episodio.
MARIA: [firme] Antes de empezar, aviso: este podcast lo genera un sistema automatico de IA y puede contener errores.

# BLOQUE_PANORAMA
IAGO: [didactico] {panorama}
MARIA: [conversacional] {panorama_maria}

# BLOQUE_DESTACADO
IAGO: [didactico] {destacado}

# APLICACION_PRACTICA
MARIA: [conversacional] {aplicacion_maria}
IAGO: [explicativo] {aplicacion_yago} Decidimos resolver este problema con cinco mil dolares de presupuesto.

# BLOQUE_FUENTES
IAGO: [didactico] {fuentes}

# CIERRE_CONCEPTOS
IAGO: [firme] No te puedes ir de este capitulo sin haber entendido estos conceptos. Primero esto. Segundo aquello. Tercero lo otro.

# CIERRE_FINAL
MARIA: [natural] Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A. Y al proximo episodio del modulo.
"""


def _parse(content: str, kind: str, tmp_path: Path, name: str) -> object:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return parse_script(p, kind)


def test_rule_iago_spelling(tmp_path: Path):
    content = """# HOOK
MARIA: [grave] Hola Iago, ¿cómo estás? Esto es MaquinarIA Pesada. Arrancamos.
"""
    script = _parse(content, "M", tmp_path, "M1.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "cast_all_yago_spelling" in codes


def test_rule_blacklist_interjection(tmp_path: Path):
    content = """# HOOK
MARIA: [grave] Hook. Esto es MaquinarIA Pesada. Arrancamos.

# BLOQUE_PANORAMA
IAGO: [didactico] Texto.
MARIA: [conversacional] Exacto. Eso es lo que pienso.
"""
    script = _parse(content, "M", tmp_path, "M1.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "cast_all_blacklist_interjection" in codes


def test_rule_digits_in_dialogue(tmp_path: Path):
    content = """# HOOK
MARIA: [grave] El 80% de las empresas. Esto es MaquinarIA Pesada. Arrancamos.
"""
    script = _parse(content, "M", tmp_path, "M1.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "audio_all_digits_in_dialogue" in codes


def test_rule_digits_exception_for_models(tmp_path: Path):
    content = """# HOOK
MARIA: [grave] Usamos GPT-4 y Claude Sonnet 4.5. Esto es MaquinarIA Pesada. Arrancamos.
"""
    script = _parse(content, "M", tmp_path, "M1.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "audio_all_digits_in_dialogue" not in codes


def test_rule_opener_parity_m_even(tmp_path: Path):
    # M0 par → Maria debe abrir
    content = """# HOOK
IAGO: [grave] Hook. Esto es MaquinarIA Pesada. Arrancamos.
"""
    script = _parse(content, "M", tmp_path, "M0.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "cast_m_opener_parity" in codes


def test_rule_opener_parity_m_odd_ok(tmp_path: Path):
    # M1 impar → Yago debe abrir
    content = """# HOOK
IAGO: [grave] Hook. Esto es MaquinarIA Pesada. Arrancamos.
"""
    script = _parse(content, "M", tmp_path, "M1.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "cast_m_opener_parity" not in codes


def test_rule_s_block_count(tmp_path: Path):
    content = """Esto es un S con solo dos parrafos.

Más sobre rag en el episodio T de MaquinarIA Pesada.
"""
    script = _parse(content, "S", tmp_path, "S1_test.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "struct_s_block_count" in codes


def test_rule_s_closing_phrase(tmp_path: Path):
    content = """¿Qué es rag? Una pregunta breve y rapida y directa.

rag es una técnica de recuperación aumentada por generación que combina busqueda y generación de respuestas más precisas usando datos externos.

Imagina un chatbot que usa rag para acceder a datos reales en lugar de inventar respuestas. Esa es la clave de su utilidad práctica en producción real.

Empresas como OpenAI ya lo usan a diario en sus productos. Esta es una conclusión sin la frase canónica.
"""
    script = _parse(content, "S", tmp_path, "S1_test.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "s_closing_phrase_literal" in codes or "struct_s_closing_literal" in codes


def test_rule_word_count_out_of_range(tmp_path: Path):
    # M demasiado corto
    content = """# HOOK
MARIA: [grave] Hook. Esto es MaquinarIA Pesada. Arrancamos.

# INTRO_SONIDO
[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]
"""
    script = _parse(content, "M", tmp_path, "M0.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "content_all_word_count_out_of_range" in codes


def test_missing_section_m(tmp_path: Path):
    content = """# HOOK
MARIA: [grave] Hook. Esto es MaquinarIA Pesada. Arrancamos.
"""
    script = _parse(content, "M", tmp_path, "M0.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "struct_all_missing_section" in codes


def test_t_forbidden_aplicacion(tmp_path: Path):
    content = """# HOOK
IAGO: [grave] Hook. Esto es MaquinarIA Pesada. Arrancamos.

# BLOQUE_COMO
IAGO: [didactico] Texto.

# BLOQUE_REALIDAD
MARIA: [analitica] Mas texto.

# APLICACION_PRACTICA
MARIA: [conversacional] Esto no debe estar en T.
"""
    script = _parse(content, "T", tmp_path, "M3_T1.txt")
    findings = evaluate_all(script)
    codes = [f.code for f in findings]
    assert "t_no_aplicacion_practica" in codes


def test_cli_runs_on_corpus():
    """Smoke test: el CLI debe correr sobre el corpus aprobado sin crash.

    `Guiones/` puede estar vacío (sus contenidos se mueven a
    `Guiones/entrenamiento v7/` o subdirectorios round*/iter_*), pero
    `Output_v6_aprobados/` es el corpus canónico con guiones reales.
    """
    from evaluador.cli import discover_scripts, evaluate_one

    corpus = Path(__file__).resolve().parent.parent / "Output_v6_aprobados" / "M"
    if not corpus.exists():
        pytest.skip("Output_v6_aprobados/M/ no disponible")
    scripts = discover_scripts(corpus)
    assert len(scripts) > 0
    # Evaluar al menos uno
    result = evaluate_one(scripts[0])
    assert "filename" in result
    assert "findings" in result
