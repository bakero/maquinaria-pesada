"""Tests del streaming + retry de ai_client.

No usa red. Sustituye `anthropic.Anthropic` por un cliente fake que
yields chunks predefinidos.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import ai_client, usage_tracker  # noqa: E402


class _FakeStream:
    def __init__(self, chunks: list[str], in_tok: int = 10, out_tok: int = 20):
        self._chunks = chunks
        self._in = in_tok
        self._out = out_tok

    @property
    def text_stream(self):
        yield from self._chunks

    def get_final_message(self):
        return types.SimpleNamespace(
            usage=types.SimpleNamespace(input_tokens=self._in, output_tokens=self._out),
        )

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class RateLimitError(RuntimeError):
    """Imita la excepción del SDK Anthropic para activar retry."""


class _FakeMessages:
    def __init__(self, chunks: list[str], fail_first_n: int = 0):
        self._chunks = chunks
        self._fail_remaining = fail_first_n

    def stream(self, **_kwargs):
        if self._fail_remaining > 0:
            self._fail_remaining -= 1
            raise RateLimitError("transient")
        return _FakeStream(self._chunks)


class _FakeAnthropic:
    def __init__(self, **kwargs):
        self.messages = _FakeMessages(chunks=kwargs.pop("__chunks__", ["hola"]))


@pytest.fixture
def _patch_anthropic(monkeypatch, tmp_path):
    # Redirigir el log de uso a tmp.
    monkeypatch.setattr(usage_tracker.paths, "ai_usage_log", lambda: tmp_path / "u.jsonl")
    monkeypatch.setattr(ai_client, "_load_anthropic_key", lambda: "fake-key")

    # Patch del import diferido.
    fake_mod = types.ModuleType("anthropic")

    def make_client(chunks: list[str], fails: int = 0):
        class _C:
            def __init__(self, *_a, **_k):
                self.messages = _FakeMessages(chunks, fail_first_n=fails)

        fake_mod.Anthropic = _C
        return _C

    monkeypatch.setitem(sys.modules, "anthropic", fake_mod)
    return make_client


def test_stream_cede_chunks_y_usage(_patch_anthropic):
    _patch_anthropic(["hola ", "mundo"])
    events = list(
        ai_client.improve_with_claude_stream(
            system="s", user="u", source="t", model="claude-haiku-4-5"
        )
    )
    text_events = [p for tag, p in events if tag == "text"]
    usage_events = [p for tag, p in events if tag == "usage"]
    assert text_events == ["hola ", "mundo"]
    assert len(usage_events) == 1
    assert usage_events[0].ok is True
    assert usage_events[0].input_tokens == 10
    assert usage_events[0].output_tokens == 20


def test_improve_with_claude_no_stream_concatena(_patch_anthropic):
    _patch_anthropic(["chunk1 ", "chunk2"])
    text, usage = ai_client.improve_with_claude(
        system="s", user="u", source="t", model="claude-haiku-4-5"
    )
    assert text == "chunk1 chunk2"
    assert usage.ok is True


def test_stream_retry_en_ratelimit(_patch_anthropic, monkeypatch):
    monkeypatch.setattr(ai_client, "RETRY_BACKOFF_S", (0, 0, 0, 0))
    _patch_anthropic(["ok"], fails=2)
    text, usage = ai_client.improve_with_claude(
        system="s", user="u", source="t", model="claude-haiku-4-5", max_retries=3
    )
    assert text == "ok"
    assert usage.ok is True


def test_stream_falla_si_supera_retries(_patch_anthropic, monkeypatch):
    monkeypatch.setattr(ai_client, "RETRY_BACKOFF_S", (0, 0))
    _patch_anthropic(["ok"], fails=5)
    with pytest.raises(ai_client.AIClientError):
        ai_client.improve_with_claude(
            system="s", user="u", source="t", model="claude-haiku-4-5", max_retries=1
        )


def test_stream_sin_anthropic_instalado(monkeypatch):
    monkeypatch.setitem(sys.modules, "anthropic", None)
    # Forzar ImportError: el módulo a importar.
    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

    def fake_import(name, *a, **kw):
        if name == "anthropic":
            raise ImportError("no anthropic")
        return real_import(name, *a, **kw)

    if isinstance(__builtins__, dict):
        monkeypatch.setitem(__builtins__, "__import__", fake_import)
    else:
        monkeypatch.setattr(__builtins__, "__import__", fake_import)

    monkeypatch.setattr(ai_client, "_load_anthropic_key", lambda: "fake")
    with pytest.raises(ai_client.AIClientError, match="anthropic SDK no instalado"):
        next(
            ai_client.improve_with_claude_stream(
                system="s", user="u", source="t", model="claude-haiku-4-5"
            )
        )
