"""Tests de validators/shared/canonical_phrases.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators.shared import canonical_phrases as cp  # noqa: E402


def test_hook_closing_present():
    hook = "Una frase potente de gancho. Esto es MaquinarIA Pesada. Arrancamos."
    assert cp.check_hook_closing(hook).passed is True


def test_hook_closing_missing_fails():
    r = cp.check_hook_closing("Un hook sin la frase canónica de cierre.")
    assert r.passed is False
    assert r.severity == "HARD"


def test_concepts_opening_present():
    text = ("No te puedes ir de este capitulo sin haber entendido estos "
            "conceptos. Uno: los embeddings.")
    assert cp.check_concepts_opening(text).passed is True


def test_concepts_opening_missing_fails():
    assert cp.check_concepts_opening("Conceptos clave: uno, dos.").passed is False


def test_final_closing_present():
    text = ("Y hasta aqui ha llegado nuestro episodio de MaquinarIA Pesada. "
            "Siguenos para nuevos capitulos donde la I.A. crea contenido sobre I.A.")
    assert cp.check_final_closing(text).passed is True


def test_final_closing_missing_fails():
    assert cp.check_final_closing("Gracias por escuchar, hasta pronto.").passed is False


def test_s_closing_template_matches_with_variable_tema():
    assert cp.check_s_closing(
        "Más sobre RAG en el episodio T de MaquinarIA Pesada.").passed is True
    assert cp.check_s_closing(
        "Más sobre el módulo 5 en el episodio T de MaquinarIA Pesada.").passed is True


def test_s_closing_missing_fails():
    assert cp.check_s_closing("Y eso es todo por hoy.").passed is False


def test_no_surnames_clean_text_passes():
    text = "IAGO: Hola, soy Yago. MARIA: Y yo soy Maria."
    assert cp.check_no_surnames(text).passed is True


def test_no_surnames_detects_invented_surname():
    r = cp.check_no_surnames("Soy Maria Grandury y hoy hablamos de IA.")
    assert r.passed is False
    assert r.severity == "HARD"
    assert "Maria Grandury" in r.context["matches"]


def test_no_surnames_detects_yago_surname():
    r = cp.check_no_surnames("Aquí Yago Goyoaga con las notas del módulo.")
    assert r.passed is False


def test_no_surnames_allows_name_followed_by_lowercase():
    # "Maria explica" no es apellido (minúscula).
    assert cp.check_no_surnames("Maria explica el concepto.").passed is True
