"""Tests de episode_state.py — estado persistido de generación por episodio.

Sin red ni ffmpeg: solo JSON en un REPO_ROOT temporal.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """REPO_ROOT temporal — episode_state escribe en logs/episode_state/ dentro."""
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    # episode_state lee REPO_ROOT en cada llamada, no hace falta recargar el módulo
    import episode_state
    return episode_state


def test_load_missing_returns_none(repo):
    assert repo.load("M3") is None


def test_save_and_load_roundtrip(repo):
    st = repo.EpisodeState(ep_id="M3", status="running", blocks_total=10)
    path = repo.save(st)
    assert path.exists()
    assert path.name == "M3.json"
    loaded = repo.load("M3")
    assert loaded is not None
    assert loaded.ep_id == "M3"
    assert loaded.status == "running"
    assert loaded.blocks_total == 10
    assert loaded.updated_at is not None  # save() lo rellena


def test_mark_running_sets_started_at(repo):
    st = repo.mark_running("M5_T1", blocks_total=8)
    assert st.status == "running"
    assert st.blocks_total == 8
    assert st.started_at is not None
    # persistido
    assert repo.load("M5_T1").status == "running"


def test_mark_finished_ok(repo):
    st = repo.mark_running("M7", blocks_total=6)
    repo.mark_finished(st, blocks_done=6, blocks_failed=0,
                       duration_s=123.4, ok=True)
    loaded = repo.load("M7")
    assert loaded.status == "ok"
    assert loaded.blocks_done == 6
    assert loaded.blocks_failed == 0
    assert loaded.duration_s == pytest.approx(123.4)
    assert loaded.error is None


def test_mark_finished_failed_keeps_error(repo):
    st = repo.mark_running("M9", blocks_total=4)
    repo.mark_finished(st, blocks_done=1, blocks_failed=3,
                       duration_s=None, ok=False, error="boom")
    loaded = repo.load("M9")
    assert loaded.status == "failed"
    assert loaded.blocks_failed == 3
    assert loaded.error == "boom"


def test_load_corrupt_json_returns_none(repo):
    path = repo.state_path("M0")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ esto no es json", encoding="utf-8")
    assert repo.load("M0") is None


def test_load_json_without_ep_id_returns_none(repo):
    path = repo.state_path("M1")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"status": "ok"}', encoding="utf-8")
    assert repo.load("M1") is None


def test_load_ignores_unknown_keys(repo):
    """Un JSON con claves de más (versiones futuras) se carga sin reventar."""
    path = repo.state_path("M2")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"ep_id": "M2", "status": "ok", "campo_futuro": 42}',
                    encoding="utf-8")
    loaded = repo.load("M2")
    assert loaded is not None
    assert loaded.ep_id == "M2"
    assert loaded.status == "ok"
