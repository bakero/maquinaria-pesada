"""Tests del módulo economics."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import economics, usage_tracker  # noqa: E402


def test_topup_save_load_roundtrip(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)

    state = economics.add_topup("anthropic", 20.0, "test")
    assert len(state.topups) == 1

    fresh = economics.load()
    assert fresh.topups[0].provider == "anthropic"
    assert fresh.topups[0].amount_usd == 20.0
    assert fresh.topups[0].note == "test"


def test_remove_topup(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)

    economics.add_topup("openai", 5.0)
    economics.add_topup("openai", 10.0)
    economics.remove_topup(0)
    state = economics.load()
    assert len(state.topups) == 1
    assert state.topups[0].amount_usd == 10.0


def test_remove_topup_idx_invalido_no_rompe(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)

    economics.add_topup("openai", 5.0)
    economics.remove_topup(99)  # out of range, debe ser no-op
    state = economics.load()
    assert len(state.topups) == 1


def test_summary_calcula_balance(tmp_path, monkeypatch):
    eco_log = tmp_path / "economics.json"
    usage_log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(economics, "economics_path", lambda: eco_log)
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: usage_log)

    economics.add_topup("anthropic", 10.0)
    usage_tracker.record(
        usage_tracker.UsageEvent(
            timestamp="t",
            kind="improvement",
            provider="anthropic",
            model="claude-sonnet-4-6",
            source="x",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.5,
        ),
        log_path=usage_log,
    )
    summary = economics.summary()
    assert "anthropic" in summary
    assert summary["anthropic"]["topped_up"] == 10.0
    assert summary["anthropic"]["spent"] == 0.5
    assert summary["anthropic"]["balance"] == 9.5
    assert summary["anthropic"]["calls"] == 1


def test_load_corrupto_devuelve_estado_vacio(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    log.write_text("not-json", encoding="utf-8")
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    state = economics.load()
    assert state.topups == []
