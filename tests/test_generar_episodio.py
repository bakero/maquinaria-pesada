"""Tests de generar_episodio_v2.py — lógica pura, sin red ni ElevenLabs.

Cubre:
  - build_atempo_chain: cadena de filtros ffmpeg válida para cualquier velocidad.
  - setup_ffmpeg: portabilidad (sin rutas hardcodeadas a un usuario concreto).
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import generar_episodio_v2 as gen  # noqa: E402


@pytest.mark.parametrize(
    "mult,expected",
    [
        (1.0, "atempo=1.0000"),
        (1.5, "atempo=1.5000"),
        (0.5, "atempo=0.5000"),
        (2.0, "atempo=2.0000"),
        (3.0, "atempo=2.0,atempo=1.5000"),
        (4.0, "atempo=2.0,atempo=2.0000"),
        (0.25, "atempo=0.5,atempo=0.5000"),
    ],
)
def test_build_atempo_chain_valid(mult, expected):
    assert gen.build_atempo_chain(mult) == expected


@pytest.mark.parametrize("bad", [0.0, 0.05, 10.5, 100.0, -1.0])
def test_build_atempo_chain_out_of_range(bad):
    with pytest.raises(ValueError, match="fuera del rango"):
        gen.build_atempo_chain(bad)


def test_build_atempo_chain_product_matches_multiplier():
    """El producto de los factores de la cadena debe reconstruir el multiplicador."""
    for mult in (0.3, 0.75, 2.7, 3.0, 6.5, 8.0):
        chain = gen.build_atempo_chain(mult)
        factors = [float(part.split("=")[1]) for part in chain.split(",")]
        product = 1.0
        for f in factors:
            product *= f
        assert product == pytest.approx(mult, rel=1e-3)
        # cada factor individual está dentro del rango legal de ffmpeg
        for f in factors:
            assert 0.5 <= f <= 2.0


def test_setup_ffmpeg_no_hardcoded_username():
    """setup_ffmpeg no debe contener rutas atadas a un usuario concreto."""
    src = inspect.getsource(gen.setup_ffmpeg)
    assert "C:\\Users\\Asus" not in src
    assert "C:/Users/Asus" not in src
    assert "Users\\Asus" not in src


def test_setup_ffmpeg_honors_env_override(tmp_path, monkeypatch):
    """FFMPEG_PATH apuntando a una carpeta se antepone al PATH."""
    fake_dir = tmp_path / "ffmpeg" / "bin"
    fake_dir.mkdir(parents=True)
    monkeypatch.setenv("FFMPEG_PATH", str(fake_dir))
    monkeypatch.setenv("PATH", "")
    gen.setup_ffmpeg()
    import os
    assert str(fake_dir) in os.environ["PATH"]
