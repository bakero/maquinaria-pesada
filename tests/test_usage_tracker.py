"""Tests del tracker de uso de IA (sin red ni API keys)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import usage_tracker  # noqa: E402


def test_estimate_cost_usd_para_sonnet_es_correcto():
    # Sonnet 4.6: 3 USD/M input, 15 USD/M output.
    cost = usage_tracker.estimate_cost_usd("claude-sonnet-4-6", 1_000_000, 0)
    assert cost == 3.0
    cost = usage_tracker.estimate_cost_usd("claude-sonnet-4-6", 0, 1_000_000)
    assert cost == 15.0


def test_estimate_cost_usd_modelo_desconocido_devuelve_cero():
    assert usage_tracker.estimate_cost_usd("modelo-X", 1000, 1000) == 0.0


def test_record_y_iter_events_roundtrip(tmp_path):
    log = tmp_path / "u.jsonl"
    ev = usage_tracker.UsageEvent(
        timestamp="2026-05-12T10:00:00",
        kind="improvement",
        provider="anthropic",
        model="claude-sonnet-4-6",
        source="test",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.001,
        latency_ms=420,
        ok=True,
    )
    usage_tracker.record(ev, log_path=log)
    usage_tracker.record(ev, log_path=log)

    events = list(usage_tracker.iter_events(log))
    assert len(events) == 2
    assert events[0]["kind"] == "improvement"
    assert events[0]["input_tokens"] == 100


def test_aggregate_calcula_totales_y_buckets(tmp_path):
    log = tmp_path / "u.jsonl"
    for src, model, ti, to, cost in [
        ("page:estado", "claude-haiku-4-5", 10, 20, 0.0001),
        ("page:estado", "claude-haiku-4-5", 5, 5, 0.00005),
        ("page:tokens", "claude-sonnet-4-6", 100, 200, 0.0033),
    ]:
        usage_tracker.record(
            usage_tracker.UsageEvent(
                timestamp="t",
                kind="update",
                provider="anthropic",
                model=model,
                source=src,
                input_tokens=ti,
                output_tokens=to,
                cost_usd=cost,
            ),
            log_path=log,
        )

    agg = usage_tracker.aggregate(usage_tracker.iter_events(log))
    assert agg["total_calls"] == 3
    assert agg["total_input_tokens"] == 115
    assert agg["total_output_tokens"] == 225
    assert "claude-haiku-4-5" in agg["by_model"]
    assert agg["by_model"]["claude-haiku-4-5"]["calls"] == 2
    assert agg["by_source"]["page:estado"]["calls"] == 2


def test_iter_events_ignora_lineas_corruptas(tmp_path):
    log = tmp_path / "u.jsonl"
    log.write_text(
        json.dumps({"kind": "ok", "input_tokens": 1, "output_tokens": 1}) + "\n"
        "no-es-json\n"
        + json.dumps({"kind": "ok", "input_tokens": 2, "output_tokens": 2}) + "\n",
        encoding="utf-8",
    )
    events = list(usage_tracker.iter_events(log))
    assert len(events) == 2  # la línea corrupta se ignora


def test_iter_events_log_inexistente_es_vacio(tmp_path):
    assert list(usage_tracker.iter_events(tmp_path / "no-existe.jsonl")) == []
