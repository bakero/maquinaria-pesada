"""Smoke tests de las CLIs v6 (validar_episodio_v6, lanzar_produccion_v6)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_validar_episodio_v6_help_runs():
    """La CLI muestra help sin errores."""
    import validar_episodio_v6 as cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0


def test_validar_episodio_v6_missing_guion_fails(tmp_path):
    import validar_episodio_v6 as cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--kind", "M", "--ep", "M0",
                  "--guion", str(tmp_path / "no_existe.txt")])
    assert exc.value.code != 0


def test_validar_episodio_v6_returns_nonzero_on_hard_fail(tmp_path):
    import validar_episodio_v6 as cli
    guion = tmp_path / "g.txt"
    guion.write_text("# HOOK\nIAGO: Hola.\n", encoding="utf-8")  # falta casi todo
    code = cli.main([
        "--kind", "M", "--ep", "M3",
        "--guion", str(guion),
        "--repo-root", str(tmp_path),
    ])
    assert code == 1  # hay bloqueos hard


def test_lanzar_produccion_v6_help_runs():
    import lanzar_produccion_v6 as cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0


def test_lanzar_produccion_v6_s_requires_term(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    import lanzar_produccion_v6 as cli
    with pytest.raises(SystemExit) as exc:
        cli.main(["--kind", "S", "--ep", "S1", "--repo-root", str(tmp_path)])
    assert exc.value.code != 0
