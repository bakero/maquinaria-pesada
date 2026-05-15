"""Tests del validador T (formato Tema)."""
from __future__ import annotations

import sys
from pathlib import Path

from tests.validators.conftest import (
    _bloque_casos_t,
    _bloque_fuentes_t,
    _bloque_limites_t,
    _cierre_conceptos,
    _cierre_final,
    _dev_block,
    _hook,
    _intro_sonido,
    _saludo,
    _verificaciones,
)

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators import t_validator as tv  # noqa: E402
from validators.parser import parse_script  # noqa: E402


def _build_full_t(opener: str = "IAGO", n_concepts: int = 3) -> str:
    """Construye un T con todas las secciones obligatorias en orden."""
    return (
        _hook(opener)
        + _intro_sonido()
        + _saludo(opener, n_words=35)
        + _dev_block("BLOQUE_PANORAMA", "IAGO", n_leader=5, n_support=1, words_per=80)
        + _dev_block("BLOQUE_COMO", "IAGO", n_leader=3, n_support=3, words_per=80)
        + _bloque_casos_t()
        + _bloque_limites_t()
        + _bloque_fuentes_t()
        + _cierre_conceptos(n_concepts)
        + _cierre_final(opener)
        + _verificaciones()
    )


def test_t_validator_smoke_runs_without_exception():
    results = tv.validate(_build_full_t(), "M3_T1")
    assert isinstance(results, list)


def test_t_concepts_exact_3_passes():
    parts = parse_script(_build_full_t(n_concepts=3))
    r = tv.check_concepts_exact_3(parts)
    assert r.passed is True


def test_t_concepts_4_fails():
    parts = parse_script(_build_full_t(n_concepts=4))
    r = tv.check_concepts_exact_3(parts)
    assert r.passed is False


def test_t_concepts_2_fails():
    parts = parse_script(_build_full_t(n_concepts=2))
    r = tv.check_concepts_exact_3(parts)
    assert r.passed is False


def test_t_leader_panorama_yago():
    parts = parse_script(_build_full_t())
    results = tv.check_leader_shares(parts)
    panorama = next(r for r in results if r.rule_name == "t_leader_panorama")
    assert panorama.passed is True


def test_t_leader_casos_maria_passes():
    parts = parse_script(_build_full_t())
    results = tv.check_leader_shares(parts)
    casos = next(r for r in results if r.rule_name == "t_leader_casos")
    assert casos.passed is True


def test_t_leader_limites_yago_passes():
    parts = parse_script(_build_full_t())
    results = tv.check_leader_shares(parts)
    limites = next(r for r in results if r.rule_name == "t_leader_limites")
    assert limites.passed is True


def test_t_casos_company_count_passes_with_two_companies():
    parts = parse_script(_build_full_t())
    r = tv.check_casos_company_count(parts)
    assert r.passed is True


def test_t_casos_no_companies_fails():
    text = (
        "# BLOQUE_CASOS\n"
        "MARIA: [analitica] Una observación sin nombres propios de empresa. "
        "Solo abstracción.\n"
    )
    parts = parse_script(text)
    r = tv.check_casos_company_count(parts)
    assert r.passed is False


def test_t_limites_semantic_patterns_present():
    parts = parse_script(_build_full_t())
    r = tv.check_limites_semantic_patterns(parts)
    assert r.passed is True


def test_t_limites_without_pattern_soft_warns():
    text = (
        "# BLOQUE_LIMITES\n"
        "IAGO: [serio] Aquí ampliamos la idea con más profundidad técnica.\n"
    )
    parts = parse_script(text)
    r = tv.check_limites_semantic_patterns(parts)
    assert r.passed is False
    assert r.severity == "SOFT"


def test_t_fuentes_count_exact_3_passes():
    parts = parse_script(_build_full_t())
    r = tv.check_fuentes_count_exact_3(parts)
    assert r.passed is True


def test_t_fuentes_count_2_fails():
    text = (
        "# BLOQUE_FUENTES\n"
        "IAGO: [explicativo] El paper de Vaswani de 2017 sigue siendo la referencia.\n"
        "MARIA: [analitica] Y el informe McKinsey de dos mil veintitrés sobre adopción real.\n"
    )
    parts = parse_script(text)
    r = tv.check_fuentes_count_exact_3(parts)
    assert r.passed is False


def test_t_no_urls_in_fuentes_clean():
    parts = parse_script(_build_full_t())
    r = tv.check_no_urls_in_fuentes(parts)
    assert r.passed is True


def test_t_aviso_duration_in_range():
    parts = parse_script(_build_full_t())
    r = tv.check_aviso_duration(parts)
    assert r.passed is True


def test_t_validate_includes_t_specific_rules():
    results = tv.validate(_build_full_t(), "M3_T1")
    names = {r.rule_name for r in results}
    for required in ("t_concepts_count_exact_3", "t_leader_casos",
                     "t_leader_limites", "t_casos_company_count",
                     "t_fuentes_count_exact_3"):
        assert required in names
