"""Tests para los helpers `track_anthropic` / `track_openai` (instrumentación
de pipelines top-level).

Sin red. Mockean objetos response y verifican que el evento se escribe en
`ai_usage.jsonl`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import usage_tracker  # noqa: E402


def _read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_track_anthropic_records_event(tmp_path, monkeypatch):
    log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: log)

    fake_response = SimpleNamespace(usage=SimpleNamespace(input_tokens=200, output_tokens=80))
    usage_tracker.track_anthropic(
        fake_response, model="claude-sonnet-4-6", source="lanzar_produccion.py",
        kind="generation", latency_ms=1234,
    )

    events = _read_events(log)
    assert len(events) == 1
    ev = events[0]
    assert ev["provider"] == "anthropic"
    assert ev["model"] == "claude-sonnet-4-6"
    assert ev["source"] == "lanzar_produccion.py"
    assert ev["input_tokens"] == 200
    assert ev["output_tokens"] == 80
    assert ev["latency_ms"] == 1234
    assert ev["ok"] is True
    # Sonnet 4.6: $3/M in + $15/M out → (200*3 + 80*15)/1e6 = 0.0018
    assert ev["cost_usd"] == 0.0018


def test_track_openai_records_event(tmp_path, monkeypatch):
    log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: log)

    fake_response = SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=500, completion_tokens=120)
    )
    usage_tracker.track_openai(
        fake_response, model="gpt-4o-mini", source="dual_debate.py", kind="generation",
        latency_ms=42,
    )

    events = _read_events(log)
    assert len(events) == 1
    ev = events[0]
    assert ev["provider"] == "openai"
    assert ev["model"] == "gpt-4o-mini"
    assert ev["input_tokens"] == 500
    assert ev["output_tokens"] == 120


def test_track_anthropic_swallows_errors(tmp_path, monkeypatch):
    """Si la respuesta es malformada o el log falla, no debe lanzar excepción."""
    log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: log)

    # Response sin .usage → no debe romper
    usage_tracker.track_anthropic(
        SimpleNamespace(), model="claude-haiku-4-5", source="x",
    )
    # Aún así escribe un evento con tokens=0
    events = _read_events(log)
    assert len(events) == 1
    assert events[0]["input_tokens"] == 0
    assert events[0]["output_tokens"] == 0


def test_track_unknown_model_zero_cost(tmp_path, monkeypatch):
    log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: log)

    fake = SimpleNamespace(usage=SimpleNamespace(input_tokens=100, output_tokens=50))
    usage_tracker.track_anthropic(fake, model="modelo-desconocido-9", source="x")
    ev = _read_events(log)[0]
    assert ev["cost_usd"] == 0.0  # PRICING.get default → coste 0


def test_pipelines_aggregate_in_tokens_page(tmp_path, monkeypatch):
    """Verifica que tras instrumentar, la página de Tokens los ve."""
    log = tmp_path / "ai_usage.jsonl"
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: log)

    # Simulamos 2 llamadas del pipeline
    usage_tracker.track_anthropic(
        SimpleNamespace(usage=SimpleNamespace(input_tokens=1000, output_tokens=500)),
        model="claude-sonnet-4-6", source="lanzar_produccion.py",
    )
    usage_tracker.track_openai(
        SimpleNamespace(usage=SimpleNamespace(prompt_tokens=300, completion_tokens=150)),
        model="gpt-4o-mini", source="dual_debate.py",
    )

    events = list(usage_tracker.iter_events())
    agg = usage_tracker.aggregate(events)
    assert agg["total_calls"] == 2
    assert agg["total_input_tokens"] == 1300
    assert agg["total_output_tokens"] == 650
    assert "claude-sonnet-4-6" in agg["by_model"]
    assert "gpt-4o-mini" in agg["by_model"]
    assert "lanzar_produccion.py" in agg["by_source"]
    assert "dual_debate.py" in agg["by_source"]
