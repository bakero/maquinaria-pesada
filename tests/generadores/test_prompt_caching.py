"""Tests del soporte de prompt caching en anthropic_client.

Sin red: mockeamos `anthropic.Anthropic` para inspeccionar el `system` que
se envía a la API y para devolver `usage` con campos de caching.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import anthropic_client as ac  # noqa: E402


def test_cacheable_block_to_anthropic_block_ttl_5m():
    block = ac.CacheableBlock(text="texto", ttl="5m")
    d = block.to_anthropic_block()
    assert d["type"] == "text"
    assert d["text"] == "texto"
    assert d["cache_control"] == {"type": "ephemeral", "ttl": "5m"}


def test_cacheable_block_to_anthropic_block_ttl_1h():
    block = ac.CacheableBlock(text="t", ttl="1h")
    assert block.to_anthropic_block()["cache_control"]["ttl"] == "1h"


def test_meets_cache_threshold_sonnet():
    # 1024 tokens * 3.5 chars/tok ≈ 3584 chars
    assert ac._meets_cache_threshold("x" * 4000, "claude-sonnet-4-5") is True
    assert ac._meets_cache_threshold("x" * 1000, "claude-sonnet-4-5") is False


def test_meets_cache_threshold_haiku_is_stricter():
    # Haiku: 4096 tokens * 3.5 ≈ 14336 chars
    assert ac._meets_cache_threshold("x" * 15000, "claude-haiku-4-5") is True
    assert ac._meets_cache_threshold("x" * 5000, "claude-haiku-4-5") is False


def test_build_system_param_str_passthrough():
    assert ac._build_system_param("system plain", "claude-sonnet-4-5") == "system plain"


def test_build_system_param_blocks_adds_cache_control_when_long():
    blocks = [
        ac.CacheableBlock(text="x" * 5000, ttl="1h"),
        ac.CacheableBlock(text="y" * 200, ttl="5m"),   # demasiado corto
    ]
    out = ac._build_system_param(blocks, "claude-sonnet-4-5")
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    # El bloque corto se envía sin cache_control.
    assert "cache_control" not in out[1]


def test_build_system_param_caps_cache_blocks_at_4():
    blocks = [ac.CacheableBlock(text="x" * 5000, ttl="5m") for _ in range(6)]
    out = ac._build_system_param(blocks, "claude-sonnet-4-5")
    cached = [b for b in out if "cache_control" in b]
    assert len(cached) == 4


def test_estimate_cost_includes_cache_create_premium():
    base = ac._estimate_cost("claude-sonnet-4-5", 10000, 0)
    with_create_5m = ac._estimate_cost(
        "claude-sonnet-4-5", 0, 0, cache_create_5m=10000)
    # 1.25× input price for 5m cache writes
    assert with_create_5m > base
    with_create_1h = ac._estimate_cost(
        "claude-sonnet-4-5", 0, 0, cache_create_1h=10000)
    assert with_create_1h > with_create_5m


def test_estimate_cost_cache_read_is_cheap():
    same_tokens = 10000
    base = ac._estimate_cost("claude-sonnet-4-5", same_tokens, 0)
    with_read = ac._estimate_cost(
        "claude-sonnet-4-5", 0, 0, cache_read=same_tokens)
    # cache_read = 0.1× input price → debería ser muchísimo más barato.
    assert with_read < base / 5


def test_track_cost_writes_v2_header(tmp_path):
    r = ac.GenerationResult(
        text="x", model="claude-haiku-4-5",
        input_tokens=100, output_tokens=50, cost_usd=0.001,
        cache_read_input_tokens=80, cache_creation_5m_tokens=200,
        latency_ms=1234,
    )
    ac.track_cost(tmp_path, "M", "M0", r, "ok",
                  attempt=2, hard_failed=0, soft_failed=1)
    log = tmp_path / "costes_generacion.log"
    rows = list(csv.reader(log.open(encoding="utf-8")))
    assert "cache_read" in rows[0]
    assert "cache_create_5m" in rows[0]
    assert "latency_ms" in rows[0]
    assert "hard_failed" in rows[0]
    # Datos de la fila.
    data = dict(zip(rows[0], rows[1], strict=False))
    assert data["cache_read"] == "80"
    assert data["cache_create_5m"] == "200"
    assert data["latency_ms"] == "1234"
    assert data["attempt"] == "2"
    assert data["soft_failed"] == "1"


def test_track_cost_migrates_legacy_csv(tmp_path):
    # Simula un CSV pre-v2 (sin columnas de cache).
    legacy = tmp_path / "costes_generacion.log"
    legacy.write_text(
        "timestamp,kind,episode_id,model,input_tokens,output_tokens,cost_usd,validation_result\n"
        "2026-01-01T00:00:00,M,M0,claude-sonnet-4-5,100,50,0.001,ok\n",
        encoding="utf-8",
    )
    r = ac.GenerationResult(
        text="x", model="claude-sonnet-4-5",
        input_tokens=10, output_tokens=5, cost_usd=0.0001)
    ac.track_cost(tmp_path, "M", "M1", r, "ok")
    # El antiguo se ha renombrado a v1.
    assert (tmp_path / "costes_generacion_v1.log").exists()
    # El nuevo tiene header v2.
    rows = list(csv.reader((tmp_path / "costes_generacion.log").open(encoding="utf-8")))
    assert "cache_read" in rows[0]


def test_generation_result_cache_hit_rate():
    r = ac.GenerationResult(
        text="t", model="m", input_tokens=30, output_tokens=5, cost_usd=0.0,
        cache_read_input_tokens=70,
    )
    # 70 / (70 + 30) = 0.7
    assert abs(r.cache_hit_rate - 0.7) < 1e-9


def test_generate_passes_blocks_with_cache_control(monkeypatch):
    """Verifica que `generate()` con `list[CacheableBlock]` envía el array
    con `cache_control` al SDK, y que extrae `cache_read_input_tokens`.
    """
    captured = {}

    class FakeStream:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        @property
        def text_stream(self):
            return iter(["hola "])
        def get_final_message(self):
            cache_creation = SimpleNamespace(
                ephemeral_5m_input_tokens=0,
                ephemeral_1h_input_tokens=4321,
            )
            usage = SimpleNamespace(
                input_tokens=100, output_tokens=10,
                cache_read_input_tokens=8765,
                cache_creation_input_tokens=4321,
                cache_creation=cache_creation,
            )
            return SimpleNamespace(usage=usage, stop_reason="end_turn")

    class FakeMessages:
        def stream(self, **kwargs):
            captured["kwargs"] = kwargs
            return FakeStream()

    class FakeAnthropic:
        def __init__(self, api_key):
            self.messages = FakeMessages()

    class FakeAnthropicMod:
        Anthropic = FakeAnthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setitem(sys.modules, "anthropic", FakeAnthropicMod)

    blocks = [ac.CacheableBlock(text="x" * 5000, ttl="1h")]
    r = ac.generate(
        system=blocks, user="u", model="claude-sonnet-4-5",
        max_output_tokens=100, temperature=0.0,
    )
    assert r.ok
    assert r.cache_read_input_tokens == 8765
    assert r.cache_creation_1h_tokens == 4321
    # El SDK recibió bloques con cache_control.
    sent = captured["kwargs"]["system"]
    assert isinstance(sent, list)
    assert sent[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
