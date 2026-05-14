"""Tests del logger estructurado JSONL para pipelines top-level."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import runlog  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_global():
    yield
    runlog._GLOBAL = None


def _read(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_event_emite_linea_con_campos_requeridos(tmp_path):
    log = runlog.RunLogger(episode="EP1", module="M3", script="test.py", events_dir=tmp_path)
    log.event("phase1", category="audio", block=7)
    log.close()
    entries = _read(tmp_path / "EP1_events.jsonl")
    assert len(entries) == 1
    e = entries[0]
    assert e["episode"] == "EP1"
    assert e["module"] == "M3"
    assert e["script"] == "test.py"
    assert e["phase"] == "phase1"
    assert e["category"] == "audio"
    assert e["level"] == "info"
    assert e["block"] == 7
    assert "ts" in e and "pid" in e


def test_warn_y_error_marcan_level(tmp_path):
    log = runlog.RunLogger("EP1", "M3", events_dir=tmp_path)
    log.warn("retry", attempt=2)
    log.error("fail", reason="boom")
    log.close()
    entries = _read(tmp_path / "EP1_events.jsonl")
    assert entries[0]["level"] == "warn"
    assert entries[1]["level"] == "error"
    assert entries[1]["reason"] == "boom"


def test_level_invalido_cae_a_info(tmp_path):
    log = runlog.RunLogger("EP1", "M3", events_dir=tmp_path)
    log.event("x", level="bogus")
    log.close()
    entries = _read(tmp_path / "EP1_events.jsonl")
    assert entries[0]["level"] == "info"


def test_category_invalida_cae_a_log(tmp_path):
    log = runlog.RunLogger("EP1", "M3", events_dir=tmp_path)
    log.event("x", category="inventada")
    log.close()
    entries = _read(tmp_path / "EP1_events.jsonl")
    assert entries[0]["category"] == "log"


def test_kwargs_no_machacan_campos_requeridos(tmp_path):
    log = runlog.RunLogger("EP1", "M3", events_dir=tmp_path)
    # Intentar machacar episode/module vía kwargs no debe colarse: la guardia
    # en RunLogger.event ignora cualquier kwarg que choque con campos requeridos.
    log.event("x", episode="OTRO", module="M0", pid=99999)
    log.close()
    entries = _read(tmp_path / "EP1_events.jsonl")
    assert entries[0]["episode"] == "EP1"
    assert entries[0]["module"] == "M3"
    assert entries[0]["phase"] == "x"
    assert entries[0]["pid"] != 99999


def test_context_manager_emite_start_y_end(tmp_path):
    with runlog.RunLogger("EP1", "M3", events_dir=tmp_path) as log:
        log.event("middle")
    entries = _read(tmp_path / "EP1_events.jsonl")
    assert entries[0]["phase"] == "start"
    assert entries[-1]["phase"] == "end"
    assert entries[-1]["status"] == "ok"
    assert "elapsed_s" in entries[-1]


def test_context_manager_captura_excepciones(tmp_path):
    with pytest.raises(ValueError):
        with runlog.RunLogger("EP1", "M3", events_dir=tmp_path) as log:
            log.event("antes")
            raise ValueError("boom")
    entries = _read(tmp_path / "EP1_events.jsonl")
    last = entries[-1]
    assert last["phase"] == "end"
    assert last["level"] == "error"
    assert last["exc_type"] == "ValueError"
    assert "boom" in last["exc"]


def test_events_dir_usa_repo_root_si_set(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    monkeypatch.delenv("EVENTS_DIR", raising=False)
    assert runlog._events_dir() == tmp_path / "episodios"


def test_events_dir_prefiere_events_dir_env(tmp_path, monkeypatch):
    custom = tmp_path / "custom"
    monkeypatch.setenv("EVENTS_DIR", str(custom))
    monkeypatch.setenv("REPO_ROOT", "/should-be-ignored")
    assert runlog._events_dir() == custom


def test_init_y_helpers_globales(tmp_path, monkeypatch):
    monkeypatch.setenv("EVENTS_DIR", str(tmp_path))
    runlog.init(episode="EP1", module="M3", script="t.py")
    runlog.event("p1", x=1)
    runlog.warn("p2", reason="r")
    runlog.error("p3", err="e")
    runlog.close_global()

    entries = _read(tmp_path / "EP1_events.jsonl")
    phases = [e["phase"] for e in entries]
    assert phases[0] == "start"
    assert "p1" in phases
    assert "p2" in phases
    assert "p3" in phases
    assert phases[-1] == "end"


def test_path_property_devuelve_ruta_correcta(tmp_path):
    log = runlog.RunLogger("EP_X", "M0", events_dir=tmp_path)
    assert log.path == tmp_path / "EP_X_events.jsonl"


def test_now_iso_termina_en_Z():
    s = runlog._now_iso()
    assert s.endswith("Z")
    assert "T" in s
