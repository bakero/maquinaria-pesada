"""Tests de `generadores/shared/pre_writing_llm.py`.

Sin red: mockeamos `anthropic.Anthropic` para evitar llamadas reales.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import pre_writing_llm as pwl  # noqa: E402


def test_is_enabled_reads_env(monkeypatch):
    monkeypatch.delenv("MP_PREWRITING_LLM", raising=False)
    assert pwl.is_enabled() is False
    monkeypatch.setenv("MP_PREWRITING_LLM", "1")
    assert pwl.is_enabled() is True
    monkeypatch.setenv("MP_PREWRITING_LLM", "true")
    assert pwl.is_enabled() is True
    monkeypatch.setenv("MP_PREWRITING_LLM", "0")
    assert pwl.is_enabled() is False


def test_extract_with_llm_falls_back_to_regex_if_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    res = pwl.extract_with_llm("Texto con 80% de empresas. OpenAI publicó.")
    # Regex fallback debe poblar datos numéricos.
    assert any("80" in d for d in res.datos_numericos)


def test_extract_with_llm_uses_tool_call(monkeypatch):
    """Verifica que el flow Haiku tool_use se parsea a PreWriting."""
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            tool_use = SimpleNamespace(
                type="tool_use",
                input={
                    "datos_numericos": ["88%", "10x"],
                    "casos_nombre_propio": ["Anthropic", "Morgan Stanley"],
                    "frase_fuerza": "Los datos limpios son la mitad del problema.",
                    "contraintuitivos": ["A pesar del hype, el ROI tarda 18 meses."],
                },
            )
            return SimpleNamespace(content=[tool_use])

    class FakeAnthropic:
        def __init__(self, api_key):
            self.messages = FakeMessages()

    class FakeMod:
        Anthropic = FakeAnthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setitem(sys.modules, "anthropic", FakeMod)

    res = pwl.extract_with_llm("PDF dummy text")
    assert res.datos_numericos == ["88%", "10x"]
    assert "Anthropic" in res.casos_nombre_propio
    assert "limpios" in res.frase_fuerza
    assert len(res.contraintuitivos) == 1
    # El tool fue forzado.
    assert captured["kwargs"]["tool_choice"]["name"] == "extract_pre_writing"
    assert captured["kwargs"]["model"] == "claude-haiku-4-5-20251001"


def test_extract_with_llm_falls_back_on_exception(monkeypatch):
    class FakeMessages:
        def create(self, **kwargs):
            raise RuntimeError("boom")

    class FakeAnthropic:
        def __init__(self, api_key):
            self.messages = FakeMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=FakeAnthropic))

    res = pwl.extract_with_llm("80% de empresas usan IA")
    # Regex fallback funciona.
    assert any("80" in d for d in res.datos_numericos)


def test_extract_cached_llm_writes_distinct_cache_file(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # forzará regex
    pwl.extract_cached_llm("texto con 50%", tmp_path)
    files = list(tmp_path.glob("*_llm.json"))
    assert len(files) == 1, "el cache LLM debe usar sufijo _llm"


def test_extract_auto_respects_env_flag(monkeypatch, tmp_path):
    # Sin flag → usa extract_pre_writing_cached del módulo regex.
    monkeypatch.delenv("MP_PREWRITING_LLM", raising=False)
    pwl.extract_auto("texto con 50%", tmp_path)
    files = list(tmp_path.glob("*.json"))
    # Cache regex: archivo SIN sufijo _llm.
    assert any("_llm" not in f.name for f in files)
