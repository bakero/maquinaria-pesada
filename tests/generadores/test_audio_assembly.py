"""Tests de generadores/shared/audio_assembly.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

pydub = pytest.importorskip("pydub")
from pydub.generators import Sine  # noqa: E402

from generadores.shared import audio_assembly as aa  # noqa: E402


def _make_block(tmp_path: Path, name: str, duration_ms: int = 1000):
    seg = Sine(220).to_audio_segment(duration=duration_ms).apply_gain(-15)
    path = tmp_path / name
    seg.export(str(path), format="mp3")
    return path


def test_ensamblar_concatenates_blocks(tmp_path):
    b1 = _make_block(tmp_path, "b1.mp3", 1000)
    b2 = _make_block(tmp_path, "b2.mp3", 1000)
    out_path = tmp_path / "ep.mp3"
    result = aa.ensamblar([b1, b2], out_path, speakers=["IAGO", "MARIA"])
    assert out_path.exists()
    assert result.block_count == 2
    # 1s + 1s + 500ms pausa entre speakers distintos ≈ 2.5s.
    assert 2.0 <= result.duration_s <= 3.5


def test_ensamblar_same_speaker_uses_short_pause(tmp_path):
    b1 = _make_block(tmp_path, "b1.mp3", 1000)
    b2 = _make_block(tmp_path, "b2.mp3", 1000)
    out_path = tmp_path / "ep.mp3"
    result = aa.ensamblar([b1, b2], out_path, speakers=["IAGO", "IAGO"],
                          same_speaker_pause_ms=100,
                          different_speaker_pause_ms=500)
    # 1s + 100ms + 1s = 2.1s
    assert 1.9 <= result.duration_s <= 2.3


def test_ensamblar_skips_none_paths(tmp_path):
    b1 = _make_block(tmp_path, "b1.mp3", 1000)
    out_path = tmp_path / "ep.mp3"
    result = aa.ensamblar([b1, None, None], out_path,
                          speakers=["IAGO", "MARIA", "IAGO"])
    assert result.block_count == 1


def test_ensamblar_handles_corrupt_block_gracefully(tmp_path):
    b1 = _make_block(tmp_path, "b1.mp3", 800)
    bad = tmp_path / "broken.mp3"
    bad.write_bytes(b"no soy un mp3 valido")
    out_path = tmp_path / "ep.mp3"
    result = aa.ensamblar([b1, bad], out_path, speakers=["IAGO", "MARIA"])
    # Solo el válido se cuenta.
    assert result.block_count == 1


def test_ensamblar_returns_used_lufs_flag(tmp_path):
    b1 = _make_block(tmp_path, "b1.mp3", 1000)
    out_path = tmp_path / "ep.mp3"
    result = aa.ensamblar([b1], out_path, speakers=["IAGO"])
    # Si pyloudnorm está disponible: True; si no: False. Ambos válidos.
    assert isinstance(result.used_lufs_normalization, bool)


def test_ensamblar_initial_silence(tmp_path):
    b1 = _make_block(tmp_path, "b1.mp3", 1000)
    out_path = tmp_path / "ep.mp3"
    result = aa.ensamblar([b1], out_path, speakers=["IAGO"],
                          initial_silence_ms=2000)
    # 2s silencio + 1s = 3s.
    assert 2.7 <= result.duration_s <= 3.5
