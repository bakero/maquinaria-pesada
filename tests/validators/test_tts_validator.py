"""Tests de validators/shared/tts_validator.py.

Generan audio sintético con pydub (silencio + tono) para no depender de MP3s
reales del repo. Si pydub/ffmpeg no están, los tests se saltan.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from validators.shared import tts_validator as tv  # noqa: E402

pydub = pytest.importorskip("pydub")
from pydub import AudioSegment  # noqa: E402
from pydub.generators import Sine  # noqa: E402


@pytest.fixture
def audio_10s(tmp_path):
    """MP3 de 10 s con tono audible (para que tenga loudness medible)."""
    seg = Sine(220).to_audio_segment(duration=10_000).apply_gain(-20)
    path = tmp_path / "ep_10s.mp3"
    seg.export(str(path), format="mp3")
    return path


@pytest.fixture
def audio_3s(tmp_path):
    seg = Sine(220).to_audio_segment(duration=3_000).apply_gain(-20)
    path = tmp_path / "ep_3s.mp3"
    seg.export(str(path), format="mp3")
    return path


def test_duration_in_range_passes(audio_10s):
    r = tv.check_duration(audio_10s, min_seconds=5, max_seconds=20)
    assert r.passed is True
    assert r.severity == "HARD"


def test_duration_out_of_range_fails(audio_3s):
    r = tv.check_duration(audio_3s, min_seconds=5, max_seconds=20)
    assert r.passed is False
    assert r.severity == "HARD"
    assert r.context["duration_s"] < 5


def test_duration_missing_file_degrades_soft(tmp_path):
    r = tv.check_duration(tmp_path / "no_existe.mp3", min_seconds=5, max_seconds=20)
    # No revienta: degrada a SOFT explicando que no se pudo medir.
    assert r.severity == "SOFT"
    assert r.passed is False


def test_loudness_returns_hard_or_soft(audio_10s):
    # Con pyloudnorm instalado → HARD (pasa o no según el tono).
    # Sin pyloudnorm → SOFT no-bloqueante. Ambos son válidos; nunca revienta.
    r = tv.check_loudness(audio_10s, target_lufs=-14.0, tolerance=0.5)
    assert r.rule_name == "tts_audio_loudness"
    assert r.severity in ("HARD", "SOFT")


def test_silent_segments_on_silence_detected(tmp_path):
    seg = AudioSegment.silent(duration=4_000)
    path = tmp_path / "silencio.mp3"
    seg.export(str(path), format="mp3")
    r = tv.check_silent_segments(path, max_silence_s=2.0)
    assert r.passed is False
    assert r.severity == "SOFT"


def test_silent_segments_on_tone_passes(audio_10s):
    r = tv.check_silent_segments(audio_10s, max_silence_s=2.0)
    assert r.passed is True


def test_check_all_returns_three_results(audio_10s):
    results = tv.check_all(audio_10s, min_seconds=5, max_seconds=20)
    assert len(results) == 3
    assert {r.rule_name for r in results} == {
        "tts_audio_duration", "tts_audio_loudness", "tts_audio_silent_segments"}
