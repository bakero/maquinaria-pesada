"""Tests del advisor de optimización."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import optimization_advisor as oa  # noqa: E402


def _ev(**kw):
    base = dict(
        timestamp="t",
        kind="improvement",
        provider="anthropic",
        model="claude-sonnet-4-6",
        source="page:x",
        input_tokens=100,
        output_tokens=200,
        cost_usd=0.001,
        latency_ms=100,
        ok=True,
        error="",
    )
    base.update(kw)
    return base


def test_sin_eventos_no_recomienda():
    assert oa.analyze([]) == []


def test_detecta_modelo_caro_para_output_corto():
    events = [
        _ev(model="claude-opus-4-7", output_tokens=50, cost_usd=0.015) for _ in range(3)
    ]
    recs = oa.analyze(events)
    assert any(r.rule_id == "T01" for r in recs)


def test_no_dispara_T01_si_solo_dos_eventos():
    events = [_ev(model="claude-opus-4-7", output_tokens=50) for _ in range(2)]
    recs = oa.analyze(events)
    assert not any(r.rule_id == "T01" for r in recs)


def test_detecta_hot_source():
    events = [
        _ev(source="page:caro", cost_usd=0.5),
        _ev(source="page:caro", cost_usd=0.5),
        _ev(source="page:otro", cost_usd=0.05),
    ]
    recs = oa.analyze(events)
    assert any(r.rule_id == "HOT-SOURCE" and "page:caro" in r.title for r in recs)


def test_detecta_fallos():
    events = [_ev(ok=False, error="RateLimitError: 429") for _ in range(3)]
    recs = oa.analyze(events)
    assert any(r.rule_id == "FAILS" for r in recs)


def test_detecta_output_verboso():
    events = [_ev(input_tokens=50, output_tokens=300, cost_usd=0.01) for _ in range(5)]
    recs = oa.analyze(events)
    assert any(r.rule_id == "VERBOSE" for r in recs)


def test_savings_factor_es_positivo_cuando_bajamos_de_gama():
    # Opus → Sonnet debe ahorrar.
    factor = oa._savings_factor("claude-opus-4-7", "claude-sonnet-4-6")
    assert 0 < factor < 1


def test_recomendaciones_ordenadas_por_ahorro():
    events = [
        _ev(model="claude-opus-4-7", output_tokens=50, cost_usd=0.5) for _ in range(5)
    ] + [
        _ev(source="hot", cost_usd=2.0),
        _ev(source="hot", cost_usd=2.0),
        _ev(source="cold", cost_usd=0.01),
    ]
    recs = oa.analyze(events)
    assert recs == sorted(recs, key=lambda r: (-r.savings_estimate_usd, r.severity))
