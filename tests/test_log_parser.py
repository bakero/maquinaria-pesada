"""Tests del log_parser (JSONL preferido, fallback texto)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import log_parser  # noqa: E402


def test_categorysummary_status_inicial_es_no_data():
    s = log_parser.CategorySummary(module="M3", category="audio")
    assert s.status == "no-data"
    assert s.has_data is False


def test_categorysummary_status_fail_si_hay_errores():
    s = log_parser.CategorySummary(module="M3", category="audio")
    s.errors.append("ERROR: boom")
    s.matched_lines = 1
    assert s.status == "fail"


def test_categorysummary_status_ok_si_hay_matches_sin_errores():
    s = log_parser.CategorySummary(module="M3", category="audio")
    s.matched_lines = 5
    assert s.status == "ok"


def test_parse_text_extrae_errores_y_warnings(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    log = tmp_path / "M3_run.log"
    log.write_text(
        "2026-05-12 10:00:00 Audio synthesis started\n"
        "2026-05-12 10:00:01 ElevenLabs OK\n"
        "2026-05-12 10:00:05 WARNING: long block detected\n"
        "2026-05-12 10:00:10 ERROR: synthesis failed for block 7\n"
        "2026-05-12 10:00:11 mp3 saved\n",
        encoding="utf-8",
    )
    summary = log_parser.parse("M3", "audio", log_path=log)
    assert summary.source == "text"
    assert summary.matched_lines >= 3  # 'audio', 'mp3', 'elevenlabs'
    assert any("ERROR" in e for e in summary.errors)
    assert any("WARNING" in w for w in summary.warnings)
    assert summary.first_ts is not None
    assert summary.last_ts is not None


def test_parse_jsonl_clasifica_eventos(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    jsonl = tmp_path / "M3_audio_events.jsonl"
    jsonl.write_text(
        json.dumps({"ts": "2026-05-12T10:00:00", "level": "info", "phase": "start",
                    "category": "audio"}) + "\n"
        + json.dumps({"ts": "2026-05-12T10:00:01", "level": "error",
                      "phase": "synth_block", "category": "audio", "block": 7}) + "\n"
        + json.dumps({"ts": "2026-05-12T10:00:02", "level": "warn",
                      "phase": "synth_block", "category": "audio"}) + "\n"
        + json.dumps({"ts": "2026-05-12T10:00:03", "level": "info", "phase": "end",
                      "status": "ok", "category": "audio"}) + "\n",
        encoding="utf-8",
    )
    summary = log_parser.parse("M3", "audio", log_path=jsonl)
    assert summary.source == "jsonl"
    assert summary.matched_lines == 4
    assert len(summary.errors) == 1
    assert len(summary.warnings) == 1
    assert len(summary.ok_signals) == 1
    assert summary.phase_counts["synth_block"] == 2


def test_parse_jsonl_lineas_corruptas_se_ignoran(tmp_path):
    jsonl = tmp_path / "x_events.jsonl"
    jsonl.write_text(
        json.dumps({"ts": "t", "level": "info", "phase": "start", "category": "audio"}) + "\n"
        "no-es-json\n"
        + json.dumps({"ts": "t", "level": "info", "phase": "end",
                      "status": "ok", "category": "audio"}) + "\n",
        encoding="utf-8",
    )
    summary = log_parser.parse("M3", "audio", log_path=jsonl)
    assert summary.matched_lines == 2


def test_parse_fallback_a_none_sin_logs(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    (tmp_path / "episodios").mkdir()
    summary = log_parser.parse("M3", "audio")
    assert summary.source == "none"
    assert summary.matched_lines == 0


def test_latest_log_para_modulo_elige_mas_reciente(tmp_path, monkeypatch):
    import time

    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    epis = tmp_path / "episodios"
    epis.mkdir()
    old = epis / "M3_old.log"
    old.write_text("a")
    time.sleep(0.05)
    new = epis / "M3_new.log"
    new.write_text("b")
    latest = log_parser.latest_log_for_module("M3")
    assert latest == new
