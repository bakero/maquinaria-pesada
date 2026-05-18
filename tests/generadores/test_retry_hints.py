"""Tests del módulo `generadores/retry_hints.py`."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores import retry_hints as rh  # noqa: E402


def test_hints_are_consolidated_to_12_or_fewer():
    """La filosofía v7: 12 hints consolidados (vs 28 originales)."""
    assert len(rh.HINTS) <= 12


def test_get_hint_for_canonical_rule_returns_formatted():
    out = rh.get_hint("word_count")
    assert out is not None
    assert "ACCIÓN" in out


def test_get_hint_unknown_rule_returns_none():
    assert rh.get_hint("regla_inexistente_xyz") is None


def test_balance_rules_NOT_aliased_fall_through_to_legacy():
    """Tras la regresión v7, los hints granulares de balance se gestionan en
    base_generator._RULE_ACTION_HINTS (no aquí). Esta función devuelve None
    para que el caller use el fallback granular.
    """
    for rule in ("m_leader_aplicacion", "m_leader_destacado",
                 "t_leader_como", "t_leader_casos", "t_leader_limites"):
        assert rh.get_hint(rule) is None, f"{rule} no debería resolver aquí"


def test_s_word_count_NOT_aliased_falls_through_to_legacy():
    """s_word_count tiene un hint MUY específico en base_generator (la rama
    'Si <157 añade dos frases concretas...'). No queremos diluirlo."""
    assert rh.get_hint("s_word_count") is None


def test_canonical_phrases_aliases_resolve():
    for rule in ("canonical_hook_closing", "canonical_concepts_opening",
                 "canonical_final_closing", "canonical_s_closing"):
        assert rh.get_hint(rule) is not None


def test_hint_format_includes_severity_label():
    hint = rh.HINTS_BY_NAME["m_fuentes_count"]
    out = hint.format()
    assert "HARD" in out
    assert "ACCIÓN" in out
    # Hint con ejemplo incluye EJEMPLO.
    assert "EJEMPLO" in out


def test_soft_hint_has_soft_label():
    hint = rh.HINTS_BY_NAME["pingpong"]
    out = hint.format()
    assert "SOFT" in out
