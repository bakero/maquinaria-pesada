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


# ---- generar_bloques: secuencial vs concurrente ----------------------


def _fake_blocks(n: int) -> list[dict]:
    return [
        {"index": i, "speaker": "IAGO" if i % 2 else "MARIA", "text": f"bloque {i}"}
        for i in range(1, n + 1)
    ]


@pytest.fixture
def patched_generar_bloque(monkeypatch):
    """Sustituye generar_bloque por un stub determinista (sin red ni ficheros)."""
    calls = []

    def stub(client, bloque, ep, temp_dir, spec):
        calls.append(bloque["index"])
        # index par → simula fallo (None); impar → ruta fake
        if bloque["index"] % 4 == 0:
            return None
        return Path(temp_dir) / f"{ep}_{bloque['index']:03d}.mp3"

    monkeypatch.setattr(gen, "generar_bloque", stub)
    return calls


@pytest.mark.parametrize("workers", [1, 2, 5])
def test_generar_bloques_resultado_igual_con_o_sin_concurrencia(
    workers, patched_generar_bloque, monkeypatch, tmp_path,
):
    """workers=1 y workers>1 deben producir el mismo dict de resultados."""
    monkeypatch.setattr(gen.time, "sleep", lambda *_: None)  # sin pausas reales
    bloques = _fake_blocks(7)
    out = gen.generar_bloques(None, bloques, "M3", tmp_path, {}, workers=workers)
    assert set(out.keys()) == {b["index"] for b in bloques}
    # los índices múltiplos de 4 fallan (ruta None), el resto tiene Path
    for idx, (ruta, bloque) in out.items():
        assert bloque["index"] == idx
        if idx % 4 == 0:
            assert ruta is None
        else:
            assert ruta is not None


def test_generar_bloques_secuencial_respeta_orden(patched_generar_bloque, monkeypatch, tmp_path):
    monkeypatch.setattr(gen.time, "sleep", lambda *_: None)
    bloques = _fake_blocks(5)
    gen.generar_bloques(None, bloques, "M3", tmp_path, {}, workers=1)
    assert patched_generar_bloque == [1, 2, 3, 4, 5]


# ---- build_spoken_sequence: lógica de pausas y timestamps ------------


def test_build_spoken_sequence_timestamps(monkeypatch, tmp_path):
    """Con from_mp3 mockeado a 1 s de silencio, valida offsets y pausas."""
    from pydub import AudioSegment

    monkeypatch.setattr(
        gen.AudioSegment, "from_mp3",
        staticmethod(lambda _p: AudioSegment.silent(duration=1000)),
    )
    spec = {"audio_rules": {"same_speaker_pause_ms": 200,
                            "different_speaker_pause_ms": 500}}
    bloques = [
        {"index": 1, "speaker": "IAGO", "section": "X"},
        {"index": 2, "speaker": "IAGO", "section": "X"},   # mismo speaker → +200
        {"index": 3, "speaker": "MARIA", "section": "X"},  # distinto → +500
    ]
    archivos = [(tmp_path / f"b{b['index']}.mp3", b) for b in bloques]
    sequence, timestamps = gen.build_spoken_sequence(archivos, spec)

    assert len(timestamps) == 3
    offsets = [off for off, _ in timestamps]
    assert offsets[0] == 0
    assert offsets[1] == 1000 + 200       # bloque1 (1 s) + pausa mismo speaker
    assert offsets[2] == offsets[1] + 1000 + 500  # + bloque2 + pausa distinto
    # los bloques None se saltan
    sequence2, ts2 = gen.build_spoken_sequence([(None, bloques[0])], spec)
    assert ts2 == []
    assert len(sequence2) == 0
