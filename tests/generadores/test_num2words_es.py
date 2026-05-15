"""Tests de generadores/shared/num2words_es.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import num2words_es as n2w  # noqa: E402


@pytest.mark.parametrize("n,expected_contains", [
    (0, "cero"), (1, "uno"), (10, "diez"), (15, "quince"),
    (21, "veinti"), (100, "cien"), (123, "ciento"),
    (1000, "mil"), (2024, "dos mil"),
])
def test_spell_integer_known_values(n, expected_contains):
    s = n2w.spell_integer(n)
    assert expected_contains in s.lower()


def test_spell_decimal_dot():
    assert "punto" in n2w.spell_decimal("3.7")
    assert "tres" in n2w.spell_decimal("3.7")


def test_spell_decimal_comma():
    assert "punto" in n2w.spell_decimal("3,7")


def test_replace_numbers_simple_percent():
    out = n2w.replace_numbers_in_text("El 80% de empresas")
    assert "ochenta" in out.lower()
    assert "por ciento" in out
    assert "80%" not in out


def test_replace_numbers_decimal_percent():
    out = n2w.replace_numbers_in_text("3.7% adopta IA")
    assert "tres" in out.lower()
    assert "punto" in out.lower()
    assert "siete" in out.lower()
    assert "por ciento" in out


def test_replace_numbers_dollar_millions():
    out = n2w.replace_numbers_in_text("invirtió $3M en R&D")
    assert "tres" in out.lower()
    assert "millones" in out.lower()
    assert "$3M" not in out


def test_replace_numbers_year_kept_as_words():
    out = n2w.replace_numbers_in_text("el paper de 2017 introdujo")
    assert "2017" not in out
    assert "dos mil diecisiete" in out.lower() or "diecisiete" in out.lower()


def test_replace_numbers_leaves_plain_text_alone():
    text = "Sin cifras, solo texto plano sobre inteligencia artificial."
    assert n2w.replace_numbers_in_text(text) == text
