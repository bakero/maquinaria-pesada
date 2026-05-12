"""Tests del sandbox de paths."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import paths, sandbox  # noqa: E402


@pytest.fixture(autouse=True)
def _repo_root_to_actual(monkeypatch):
    monkeypatch.setattr(paths, "repo_root", lambda: ROOT)


def test_guiones_path_permitido():
    ok, _ = sandbox.is_write_allowed(ROOT / "Guiones" / "M3_test.txt")
    assert ok is True


def test_episodios_path_permitido():
    ok, _ = sandbox.is_write_allowed(ROOT / "episodios" / "EP001.mp3")
    assert ok is True


def test_components_map_permitido():
    ok, reason = sandbox.is_write_allowed(ROOT / "cockpit" / "components_map.json")
    assert ok is True, reason


def test_cockpit_py_prohibido():
    ok, reason = sandbox.is_write_allowed(ROOT / "cockpit" / "app.py")
    assert ok is False
    assert "cockpit/" in reason


def test_workflow_prohibido():
    ok, _ = sandbox.is_write_allowed(ROOT / ".github" / "workflows" / "ci.yml")
    assert ok is False


def test_pipeline_py_prohibido():
    # Top-level .py del repo NO está en allowed_dirs.
    ok, _ = sandbox.is_write_allowed(ROOT / "generar_guion.py")
    assert ok is False


def test_env_prohibido():
    ok, _ = sandbox.is_write_allowed(ROOT / ".env")
    assert ok is False


def test_archivo_prohibido_aunque_dentro_de_allowed():
    # Si _archivo aparece en la ruta, queda fuera.
    ok, _ = sandbox.is_write_allowed(ROOT / "_archivo" / "old.txt")
    assert ok is False


def test_fuera_del_repo():
    ok, reason = sandbox.is_write_allowed("/etc/passwd")
    assert ok is False
    assert "Fuera del repo" in reason


def test_filter_paths_separa_correctamente():
    ok, rejected = sandbox.filter_paths(
        [
            ROOT / "Guiones" / "a.txt",
            ROOT / "cockpit" / "app.py",
            ROOT / "escaletas" / "b.json",
        ]
    )
    assert len(ok) == 2
    assert len(rejected) == 1
    assert "cockpit/" in rejected[0][1]
