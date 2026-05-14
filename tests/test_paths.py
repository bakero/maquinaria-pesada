"""Tests del módulo de paths."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import paths  # noqa: E402


def test_repo_root_respeta_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    assert paths.repo_root() == tmp_path.resolve()


def test_repo_root_default_si_no_hay_env(monkeypatch):
    monkeypatch.delenv("REPO_ROOT", raising=False)
    root = paths.repo_root()
    # No verificamos string exacto (Windows path), solo que sea un Path resoluble.
    assert isinstance(root, Path)
    assert root.is_absolute()


def test_p_compone_relativo_al_root(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    assert paths.p("sub", "file.txt") == tmp_path.resolve() / "sub" / "file.txt"


def test_helpers_devuelven_paths_esperados(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    assert paths.pdfs_dir() == tmp_path.resolve() / "PDFs"
    assert paths.guiones_dir() == tmp_path.resolve() / "Guiones"
    assert paths.episodios_dir() == tmp_path.resolve() / "episodios"
    assert paths.videos_dir() == tmp_path.resolve() / "Videos"
    assert paths.logos_dir() == tmp_path.resolve() / "Logos"
    assert paths.env_file() == tmp_path.resolve() / ".env"
    assert paths.logs_dir() == tmp_path.resolve() / "logs"
    assert paths.ai_usage_log() == tmp_path.resolve() / "logs" / "ai_usage.jsonl"


def test_modules_son_15(monkeypatch):
    assert paths.MODULES == [f"M{i}" for i in range(15)]
    assert len(paths.MODULES) == 15
