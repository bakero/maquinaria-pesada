"""Tests de validators/base_validator.py — reglas comunes a M/T/S."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators import base_validator as bv  # noqa: E402
from validators.parser import parse_script  # noqa: E402

# Guion mínimo válido para M (4 bloques de contenido + saludo + cierre + verif).
MIN_M_REQUIRED = [
    "HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
    "BLOQUE_PANORAMA", "BLOQUE_DESTACADO", "APLICACION_PRACTICA",
    "BLOQUE_FUENTES", "CIERRE_CONCEPTOS", "CIERRE_FINAL", "VERIFICACIONES",
]
MIN_M_FORBIDDEN = ["BLOQUE_LIMITES", "BLOQUE_REALIDAD", "BLOQUE_CASOS"]


def _build_guion(opener: str = "IAGO", sections: list[str] | None = None,
                 extra_body: str = "") -> str:
    """Construye un guion sintético con todas las secciones requeridas mínimas."""
    sections = sections or MIN_M_REQUIRED
    parts = []
    for sec in sections:
        parts.append(f"# {sec}")
        if sec == "HOOK":
            other = "MARIA" if opener == "IAGO" else "IAGO"
            parts.append(f"{opener}: [directo] Frase inicial del hook que sostiene la atención del oyente con un dato concreto sobre la inteligencia artificial moderna.")
            parts.append(f"{other}: [curioso] Una pregunta de matiz para abrir el episodio. Esto es MaquinarIA Pesada. Arrancamos.")
        elif sec == "INTRO_SONIDO":
            parts.append("[INTRO - SONIDO DE MAQUINAS ARRANCANDO - 8-10 segundos]")
        elif sec == "SALUDO_Y_PRESENTACION":
            other = "MARIA" if opener == "IAGO" else "IAGO"
            parts.append(f"{opener}: [calido] Bienvenidos al episodio. Soy {'Yago' if opener == 'IAGO' else 'Maria'}.")
            parts.append(f"{other}: [calido] Y yo soy {'Maria' if other == 'MARIA' else 'Yago'}.")
            parts.append(f"{opener}: [serio] Antes de empezar lo de siempre. Este episodio lo genera un sistema automatico de inteligencia artificial que puede contener errores. Contrastalo si algo no te cuadra.")
        elif sec == "CIERRE_CONCEPTOS":
            parts.append("IAGO: [directo] No te puedes ir de este capitulo sin haber entendido estos conceptos. Primero el concepto número uno con claridad técnica para la audiencia.")
            parts.append("MARIA: [analitica] Segundo concepto que aterriza el bloque anterior y conecta con la aplicación práctica del módulo de hoy.")
            parts.append("IAGO: [firme] Tercer concepto que cierra el capítulo con una idea fuerte y memorable para el oyente.")
        elif sec == "CIERRE_FINAL":
            parts.append("MARIA: [calido] Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A.")
        elif sec == "VERIFICACIONES":
            parts.append("[verificaciones internas del generador]")
        else:
            # Bloque de contenido genérico con dos intervenciones de desarrollo.
            parts.append("IAGO: [explicativo] Esta intervención de desarrollo cubre el bloque con la profundidad técnica necesaria para sostener la promesa del episodio. Aterriza los conceptos con ejemplos cotidianos antes de pasar al detalle.")
            parts.append("MARIA: [analitica] La pregunta de matiz que aterriza el ejemplo anterior en la realidad del oyente. Conecta la teoría con un caso que cualquier profesional puede reconocer en su día a día.")
    if extra_body:
        parts.append(extra_body)
    return "\n\n".join(parts) + "\n"


def test_validate_common_passes_on_minimal_valid_m():
    text = _build_guion(opener="MARIA", sections=MIN_M_REQUIRED)
    parts = parse_script(text)
    expected_order = ["HOOK", "INTRO_SONIDO", "SALUDO_Y_PRESENTACION",
                      "BLOQUE_PANORAMA", "BLOQUE_DESTACADO", "APLICACION_PRACTICA",
                      "BLOQUE_FUENTES", "CIERRE_CONCEPTOS", "CIERRE_FINAL",
                      "VERIFICACIONES"]
    results = bv.validate_common(
        parts, episode_id="M0", kind="M",
        required_sections=MIN_M_REQUIRED,
        forbidden_sections=MIN_M_FORBIDDEN,
        expected_order=expected_order,
        word_min=200, word_max=10000,  # rango amplio para test
    )
    blocking = [r for r in results if r.is_blocking]
    assert blocking == [], f"Reglas duras fallando: {[r.rule_name for r in blocking]}"


def test_required_section_missing_fails_hard():
    sections = [s for s in MIN_M_REQUIRED if s != "BLOQUE_FUENTES"]
    text = _build_guion(opener="MARIA", sections=sections)
    parts = parse_script(text)
    r = bv.check_required_sections(parts, MIN_M_REQUIRED)
    assert r.passed is False
    assert "BLOQUE_FUENTES" in r.context["missing"]


def test_forbidden_section_present_fails_hard():
    sections = MIN_M_REQUIRED + ["BLOQUE_LIMITES"]
    text = _build_guion(opener="MARIA", sections=sections)
    text += "\n# BLOQUE_LIMITES\nIAGO: [directo] No deberia estar aqui.\n"
    parts = parse_script(text)
    r = bv.check_forbidden_sections(parts, MIN_M_FORBIDDEN)
    assert r.passed is False


def test_section_order_swapped_fails():
    swapped = list(MIN_M_REQUIRED)
    swapped[3], swapped[4] = swapped[4], swapped[3]
    text = _build_guion(opener="MARIA", sections=swapped)
    parts = parse_script(text)
    r = bv.check_section_order(parts, MIN_M_REQUIRED)
    assert r.passed is False


def test_word_count_below_min_fails():
    parts = parse_script("# HOOK\nIAGO: [directo] Una.")
    r = bv.check_word_count(parts, min_words=100, max_words=200)
    assert r.passed is False


def test_word_count_above_max_fails():
    big = "palabra " * 500
    text = f"# HOOK\nIAGO: [directo] {big}"
    parts = parse_script(text)
    r = bv.check_word_count(parts, min_words=100, max_words=300)
    assert r.passed is False


def test_tts_tag_not_in_allowed_list_soft_warns():
    parts = parse_script("# HOOK\nIAGO: [inventado] Texto.")
    r = bv.check_tts_tags_allowed(parts)
    assert r.passed is False
    assert r.severity == "SOFT"


def test_tts_allowed_tags_pass():
    parts = parse_script(
        "# HOOK\nIAGO: [didactico] Uno.\nMARIA: [analitica] Dos.")
    r = bv.check_tts_tags_allowed(parts)
    assert r.passed is True


def test_saludo_collapsed_in_single_intervention_fails():
    bad_saludo = (
        "# SALUDO_Y_PRESENTACION\n"
        "IAGO: [calido] Soy Yago. Y yo soy Maria. Antes de empezar...\n"
    )
    parts = parse_script(bad_saludo)
    r = bv.check_saludo_format(parts)
    assert r.passed is False


def test_saludo_with_three_blocks_passes():
    saludo = (
        "# SALUDO_Y_PRESENTACION\n"
        "IAGO: [calido] Soy Yago.\n"
        "MARIA: [calido] Y yo soy Maria.\n"
        "IAGO: [serio] Antes de empezar el aviso del sistema automatico que puede contener errores.\n"
    )
    parts = parse_script(saludo)
    r = bv.check_saludo_format(parts)
    assert r.passed is True


def test_ia_warning_missing_keywords_fails():
    saludo = (
        "# SALUDO_Y_PRESENTACION\n"
        "IAGO: [calido] Soy Yago.\n"
        "MARIA: [calido] Y yo soy Maria.\n"
        "IAGO: [serio] Bienvenidos al episodio de hoy.\n"
    )
    parts = parse_script(saludo)
    r = bv.check_ia_warning(parts, opener="IAGO")
    assert r.passed is False


def test_ia_warning_said_by_wrong_speaker_fails():
    saludo = (
        "# SALUDO_Y_PRESENTACION\n"
        "IAGO: [calido] Soy Yago.\n"
        "MARIA: [calido] Y yo soy Maria.\n"
        "MARIA: [serio] El sistema automatico puede contener errores.\n"
    )
    parts = parse_script(saludo)
    r = bv.check_ia_warning(parts, opener="IAGO")
    assert r.passed is False


def test_pingpong_excess_support_soft_warns():
    block = "# BLOQUE_PANORAMA\n"
    # Líder Yago: 1 intervención. Apoyo Maria: 2 → ratio 2.0 > 1/3.
    block += "IAGO: [directo] Una sola intervención del líder.\n"
    block += "MARIA: [curioso] Pregunta.\n"
    block += "MARIA: [analitica] Otra pregunta.\n"
    parts = parse_script(block)
    r = bv.check_pingpong(parts, "BLOQUE_PANORAMA", "IAGO")
    assert r.passed is False
    assert r.severity == "SOFT"


def test_pingpong_balanced_passes():
    block = "# BLOQUE_PANORAMA\n"
    # 3 intervenciones de Yago, 1 de Maria → ratio 1/3.
    for _ in range(3):
        block += "IAGO: [directo] Intervención del líder con suficiente cuerpo.\n"
    block += "MARIA: [curioso] Una pregunta de matiz puntual.\n"
    parts = parse_script(block)
    r = bv.check_pingpong(parts, "BLOQUE_PANORAMA", "IAGO")
    assert r.passed is True
