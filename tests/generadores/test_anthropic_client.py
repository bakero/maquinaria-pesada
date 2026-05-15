"""Tests de generadores/shared/anthropic_client.py.

Sin red ni API keys reales: mockeamos generate() para verificar la lógica de
retry y tracking de coste.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import anthropic_client as ac  # noqa: E402


def test_generate_no_api_key_returns_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = ac.generate(system="x", user="y", model="claude-haiku-4-5",
                     api_key=None)
    assert r.ok is False
    assert "ANTHROPIC_API_KEY" in (r.error or "")


def test_estimate_cost_known_model():
    cost = ac._estimate_cost("claude-haiku-4-5", 100_000, 50_000)
    # 100K * 0.8 + 50K * 4.0 = 280_000 → /1M = 0.28 USD
    assert 0.27 <= cost <= 0.29


def test_estimate_cost_unknown_model_uses_default():
    cost = ac._estimate_cost("claude-otro", 0, 0)
    assert cost == 0.0


def test_track_cost_creates_csv_with_header(tmp_path):
    result = ac.GenerationResult(
        text="hola", model="claude-haiku-4-5",
        input_tokens=1000, output_tokens=500, cost_usd=0.0028,
    )
    ac.track_cost(tmp_path, "S", "S1_RAG", result, "ok")
    log = tmp_path / "costes_generacion.log"
    assert log.exists()
    with log.open(encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0][0] == "timestamp"
    assert rows[1][1] == "S"
    assert rows[1][2] == "S1_RAG"
    assert rows[1][3] == "claude-haiku-4-5"


def test_track_cost_appends_without_duplicating_header(tmp_path):
    result = ac.GenerationResult(
        text="x", model="claude-haiku-4-5",
        input_tokens=10, output_tokens=20, cost_usd=0.001,
    )
    ac.track_cost(tmp_path, "M", "M0", result, "ok")
    ac.track_cost(tmp_path, "T", "M0_T1", result, "ok")
    log = tmp_path / "costes_generacion.log"
    rows = list(csv.reader(log.open(encoding="utf-8")))
    # 1 header + 2 data rows
    assert len(rows) == 3
    assert rows[0][0] == "timestamp"
    assert rows[1][2] == "M0"
    assert rows[2][2] == "M0_T1"


def test_generation_result_ok_property():
    r = ac.GenerationResult("hola", "m", 1, 1, 0.0)
    assert r.ok is True
    r2 = ac.GenerationResult("", "m", 0, 0, 0.0, error="fallo")
    assert r2.ok is False


def test_generate_with_retry_passes_first_when_no_feedback(monkeypatch):
    captured = []

    def fake(*, system, user, model, **kw):
        captured.append((user,))
        return ac.GenerationResult("primer intento", model, 10, 5, 0.0)

    monkeypatch.setattr(ac, "generate", fake)
    first, second = ac.generate_with_retry(
        system="s", user="u", model="m", retry_feedback=None)
    assert first.text == "primer intento"
    assert second is None
    assert len(captured) == 1


def test_generate_with_retry_runs_second_with_feedback(monkeypatch):
    captured: list[str] = []

    def fake(*, system, user, model, **kw):
        captured.append(user)
        return ac.GenerationResult(f"resp {len(captured)}", model, 5, 5, 0.0)

    monkeypatch.setattr(ac, "generate", fake)
    first, second = ac.generate_with_retry(
        system="s", user="prompt original", model="m",
        retry_feedback="te faltó BLOQUE_FUENTES")
    assert first.text == "resp 1"
    assert second is not None
    assert second.text == "resp 2"
    # El segundo prompt incluye el feedback explícito.
    assert "BLOQUE_FUENTES" in captured[1]
    assert "FEEDBACK" in captured[1]
