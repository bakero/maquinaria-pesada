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
    assert state.spends == []
    assert state.subscriptions == []


def test_add_remove_spend(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    economics.add_spend("kling", 12.5, "test gasto")
    economics.add_spend("kling", 5.0)
    state = economics.load()
    assert len(state.spends) == 2
    assert state.spends[0].provider == "kling"
    assert state.spends[0].amount_usd == 12.5
    economics.remove_spend(0)
    state = economics.load()
    assert len(state.spends) == 1
    assert state.spends[0].amount_usd == 5.0


def test_add_remove_subscription(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    economics.add_subscription("Claude Max", "anthropic", 100.0,
                               started_on="2026-04", note="plan x5")
    economics.add_subscription("ElevenLabs Starter", "elevenlabs", 5.0)
    state = economics.load()
    assert len(state.subscriptions) == 2
    assert state.subscriptions[0].name == "Claude Max"
    assert state.subscriptions[0].monthly_usd == 100.0
    economics.remove_subscription(1)
    state = economics.load()
    assert len(state.subscriptions) == 1


def test_summary_integra_manual_spend(tmp_path, monkeypatch):
    eco_log = tmp_path / "economics.json"
    usage_log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(economics, "economics_path", lambda: eco_log)
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: usage_log)

    economics.add_topup("kling", 50.0)
    economics.add_spend("kling", 40.0, "iteraciones")
    summary = economics.summary()
    assert summary["kling"]["topped_up"] == 50.0
    assert summary["kling"]["spent_manual"] == 40.0
    assert summary["kling"]["spent_tracked"] == 0.0
    assert summary["kling"]["spent"] == 40.0
    assert summary["kling"]["balance"] == 10.0


def test_summary_integra_subscription_monthly(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    economics.add_subscription("Claude Max", "anthropic", 100.0)
    economics.add_subscription("ElevenLabs Starter", "elevenlabs", 5.0)
    summary = economics.summary()
    assert summary["anthropic"]["subscription_monthly"] == 100.0
    assert summary["anthropic"]["subscriptions"] == 1
    assert summary["elevenlabs"]["subscription_monthly"] == 5.0
    assert economics.total_subscription_monthly() == 105.0


def test_subscription_inactive_no_cuenta(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    economics.add_subscription("Claude Max", "anthropic", 100.0)
    # Marcar inactiva directamente
    state = economics.load()
    state.subscriptions[0].active = False
    economics.save(state)
    assert economics.total_subscription_monthly() == 0.0


def test_seed_snapshot_real(tmp_path, monkeypatch):
    eco_log = tmp_path / "economics.json"
    usage_log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(economics, "economics_path", lambda: eco_log)
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: usage_log)

    state = economics.seed_snapshot(replace=True)
    # 2 anthropic + 2 elevenlabs + 4 kling = 8 topups
    assert len(state.topups) == 8
    # 3 gastos manuales
    assert len(state.spends) == 3
    # 2 suscripciones
    assert len(state.subscriptions) == 2

    summary = economics.summary()
    # Anthropic: 24.20 + 30.25 = 54.45 topups
    assert round(summary["anthropic"]["topped_up"], 2) == 54.45
    # Anthropic: 29.62 consumido manual → saldo 24.83
    assert round(summary["anthropic"]["balance"], 2) == 24.83
    # Kling: 11.86 + 16.94*3 = 62.68 topups y 62.68 gasto → saldo 0
    assert round(summary["kling"]["topped_up"], 2) == 62.68
    assert round(summary["kling"]["balance"], 2) == 0.0
    # ElevenLabs: 48.40 topups y 48.40 gasto → saldo 0
    assert round(summary["elevenlabs"]["topped_up"], 2) == 48.40
    assert round(summary["elevenlabs"]["balance"], 2) == 0.0
    # Suscripciones mensuales: Claude Max 100 + Starter 5 = 105
    assert economics.total_subscription_monthly() == 105.0


def test_seed_snapshot_acumula_por_defecto(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    monkeypatch.setattr(
        usage_tracker.paths, "ai_usage_log", lambda: tmp_path / "usage.jsonl"
    )

    economics.add_topup("anthropic", 100.0, "preexistente")
    economics.seed_snapshot(replace=False)
    state = economics.load()
    # 1 preexistente + 8 del snapshot
    assert len(state.topups) == 9


def test_seed_snapshot_replace_borra_estado(tmp_path, monkeypatch):
    log = tmp_path / "economics.json"
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    monkeypatch.setattr(
        usage_tracker.paths, "ai_usage_log", lambda: tmp_path / "usage.jsonl"
    )

    economics.add_topup("anthropic", 100.0, "preexistente")
    economics.seed_snapshot(replace=True)
    state = economics.load()
    # Solo los 8 del snapshot, el preexistente fue reemplazado
    assert len(state.topups) == 8


def test_state_retrocompat_solo_topups(tmp_path, monkeypatch):
    """Un economics.json antiguo solo con topups debe cargarse sin errores."""
    log = tmp_path / "economics.json"
    log.write_text(
        '{"topups": [{"timestamp": "2026-01-01", "provider": "anthropic", '
        '"amount_usd": 10.0, "note": "old"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(economics, "economics_path", lambda: log)
    state = economics.load()
    assert len(state.topups) == 1
    assert state.spends == []
    assert state.subscriptions == []
