"""Tests del validador M (formato Módulo)."""
from __future__ import annotations

import sys
from pathlib import Path

from tests.validators.conftest import (
    _bloque_fuentes_m,
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

from validators import m_validator as mv  # noqa: E402
from validators.parser import parse_script  # noqa: E402


def _build_full_m(opener: str = "MARIA", n_concepts: int = 4) -> str:
    """Construye un M con todas las secciones obligatorias en orden."""
    return (
        _hook(opener)
        + _intro_sonido()
        + _saludo(opener)
        + _dev_block("BLOQUE_PANORAMA", "IAGO", n_leader=5, n_support=1, words_per=80)
        + _dev_block("BLOQUE_DESTACADO", "IAGO", n_leader=3, n_support=2, words_per=80)
        # APLICACION_PRACTICA con Maria abriendo/cerrando, Yago detallando.
        + "# APLICACION_PRACTICA\n"
        + "MARIA: [analitica] Ahora veamos cómo todo esto se aplica en un sistema real. La pregunta operativa es concreta para este módulo, conectada con el sistema.\n"
        + ("IAGO: [explicativo] " + " ".join(["palabra"] * 100) + " Aquí Yago detalla con peso de palabras el funcionamiento high-level del sistema.\n") * 3
        + "MARIA: [firme] Y cerramos conectando con el módulo entero. Bien aterrizado el concepto en una aplicación real con cifras concretas verificables.\n"
        + _bloque_fuentes_m()
        + _cierre_conceptos(n_concepts)
        + _cierre_final(opener)
        + _verificaciones()
    )


def test_m_validator_smoke_runs_without_exception():
    text = _build_full_m()
    results = mv.validate(text, "M0", repo_root=Path("/tmp/nonexistent"))
    assert isinstance(results, list)
    assert all(hasattr(r, "rule_name") for r in results)


def test_m_concepts_count_in_range_passes():
    parts = parse_script(_build_full_m(n_concepts=4))
    r = mv.check_concepts_count(parts)
    assert r.passed is True


def test_m_concepts_count_below_3_fails():
    parts = parse_script(_build_full_m(n_concepts=2))
    r = mv.check_concepts_count(parts)
    assert r.passed is False


def test_m_concepts_count_above_5_fails():
    parts = parse_script(_build_full_m(n_concepts=6))
    r = mv.check_concepts_count(parts)
    assert r.passed is False


def test_m_concepts_opening_canonical_present():
    parts = parse_script(_build_full_m())
    r = mv.check_concepts_opening(parts)
    assert r.passed is True


def test_m_final_closing_canonical_present():
    parts = parse_script(_build_full_m())
    r = mv.check_final_closing(parts)
    assert r.passed is True


def test_m_leader_panorama_yago_lidera():
    parts = parse_script(_build_full_m())
    results = mv.check_leader_shares(parts)
    panorama = next(r for r in results if r.rule_name == "m_leader_panorama")
    assert panorama.passed is True


def test_m_leader_panorama_fails_if_yago_below_65():
    text = (
        _hook("MARIA")
        + _intro_sonido()
        + _saludo("MARIA")
        # Panorama dominado por Maria (mal).
        + _dev_block("BLOQUE_PANORAMA", "MARIA", n_leader=5, n_support=1, words_per=80)
    )
    parts = parse_script(text)
    results = mv.check_leader_shares(parts)
    panorama = next(r for r in results if r.rule_name == "m_leader_panorama")
    assert panorama.passed is False


def test_m_aplicacion_in_hook_fails():
    text = (
        "# HOOK\n"
        "MARIA: [directo] Hoy hablamos del sistema que genera este podcast. "
        "Esto es MaquinarIA Pesada. Arrancamos.\n"
    )
    parts = parse_script(text)
    r = mv.check_aplicacion_not_in_hook(parts)
    assert r.passed is False


def test_m_aplicacion_not_in_hook_passes():
    text = _build_full_m()
    parts = parse_script(text)
    r = mv.check_aplicacion_not_in_hook(parts)
    assert r.passed is True


def test_m_fuentes_count_in_range_passes():
    parts = parse_script(_build_full_m())
    r = mv.check_fuentes_count(parts)
    assert r.passed is True


def test_m_fuentes_count_zero_fails():
    text = _build_full_m()
    # Vaciamos BLOQUE_FUENTES
    text = text.replace(_bloque_fuentes_m(),
                         "# BLOQUE_FUENTES\nIAGO: [serio] Sin fuentes claras.\n")
    parts = parse_script(text)
    r = mv.check_fuentes_count(parts)
    assert r.passed is False


def test_m_fuentes_marco_file_missing(tmp_path):
    r = mv.check_fuentes_marco_file("M3", repo_root=tmp_path)
    assert r.passed is False
    assert r.severity == "HARD"


def test_m_fuentes_marco_file_exists(tmp_path):
    (tmp_path / "PDFs" / "auxiliares").mkdir(parents=True)
    (tmp_path / "PDFs" / "auxiliares" / "fuentes_marco_modulo_M3.md").write_text(
        "# Fuentes M3\n", encoding="utf-8")
    r = mv.check_fuentes_marco_file("M3", repo_root=tmp_path)
    assert r.passed is True


def test_m_no_urls_in_fuentes_clean_passes():
    parts = parse_script(_build_full_m())
    r = mv.check_no_urls_in_fuentes(parts)
    assert r.passed is True


def test_m_no_urls_in_fuentes_detects_url():
    text = ("# BLOQUE_FUENTES\nIAGO: [serio] La fuente está en https://example.com.\n")
    parts = parse_script(text)
    r = mv.check_no_urls_in_fuentes(parts)
    assert r.passed is False


def test_m_aviso_duration_in_range(tmp_path):
    parts = parse_script(_build_full_m())
    r = mv.check_aviso_duration(parts)
    # Con el saludo construido (~50 palabras) cae en el rango 45-75.
    assert r.passed is True


def test_m_validate_returns_list_with_no_unparseable_rule_names():
    text = _build_full_m()
    results = mv.validate(text, "M0", repo_root=Path("/tmp/nonexistent"))
    # Todos los resultados tienen rule_name no vacío.
    assert all(r.rule_name for r in results)
    # Hay al menos las reglas específicas de M y de común.
    names = {r.rule_name for r in results}
    assert "m_concepts_count" in names
    assert "m_leader_panorama" in names
    assert "required_sections" in names
