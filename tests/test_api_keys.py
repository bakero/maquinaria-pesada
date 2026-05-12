"""Tests del módulo api_keys (sin red: provider ausente)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import api_keys  # noqa: E402


def test_keystatus_dataclass_acepta_minimo():
    s = api_keys.KeyStatus(provider="X", env_var="X_KEY", present=False, ok=False)
    assert s.detail == ""
    assert s.latency_ms == 0


def test_providers_registry_tiene_los_tres_proveedores():
    names = [p[0] for p in api_keys.PROVIDERS]
    assert names == ["Anthropic", "OpenAI", "ElevenLabs"]
    for _, var, fn in api_keys.PROVIDERS:
        assert var.endswith("_API_KEY")
        assert callable(fn)


def test_check_all_marca_ausente_sin_keys(monkeypatch, tmp_path):
    # Limpia entorno y .env del repo.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(api_keys, "CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr(api_keys.paths, "env_file", lambda: tmp_path / "no-env")

    items = api_keys.check_all(force=True)
    assert len(items) == 3
    for item in items:
        assert item.present is False
        assert item.ok is False
        assert "no definido" in item.detail
