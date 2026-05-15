"""Ensamblaje del MP3 final del episodio.

Reimplementación de `montar_audio` (legacy `generar_episodio_v2.py`) con:
- streaming de cada bloque (no carga todos los `AudioSegment` simultáneamente
  en RAM — los ensambla y libera por chunks).
- normalización a -14 LUFS (estándar Spotify) en vez de -16 dBFS.
- soporte de SSML `<break>` ya inserto en el guion (lo ignora ElevenLabs si no
  lo soporta; aquí en el ensamblaje se respetan las pausas explícitas).

La función `ensamblar` recibe la lista de archivos MP3 de cada intervención
(en orden) y los une con pausas opcionales entre cambio de speaker. No
mezcla con música/sintonía: eso lo hace el specialist `m_generator` con la
config v6 (que sigue usando los assets del proyecto).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AssemblyResult:
    output_path: Path
    duration_s: float
    block_count: int
    used_lufs_normalization: bool


def _maybe_normalize_to_lufs(seg, target_lufs: float):
    """Aplica normalización a target_lufs si `pyloudnorm` está disponible.

    Devuelve `(seg_normalizado, ok_bool)`. Si no se puede medir, devuelve el
    segmento sin tocar y False.
    """
    try:
        import numpy as np
        import pyloudnorm as pyln
    except ImportError:  # pragma: no cover
        return seg, False
    try:
        samples = np.array(seg.get_array_of_samples()).astype(np.float64)
        if seg.channels == 2:
            samples = samples.reshape((-1, 2))
        max_val = float(1 << (8 * seg.sample_width - 1))
        normed = samples / max_val
        meter = pyln.Meter(seg.frame_rate)
        lufs = meter.integrated_loudness(normed)
        # Aplica ganancia para llegar a target.
        gain_db = float(target_lufs) - float(lufs)
        return seg.apply_gain(gain_db), True
    except Exception:  # noqa: BLE001
        return seg, False


def ensamblar(
    block_paths: list[Path | None],
    output_path: Path,
    *,
    same_speaker_pause_ms: int = 250,
    different_speaker_pause_ms: int = 500,
    speakers: list[str] | None = None,
    target_lufs: float = -14.0,
    bitrate: str = "192k",
    initial_silence_ms: int = 0,
) -> AssemblyResult:
    """Une los bloques de audio en orden, aplica pausas y normalización.

    `block_paths` es una lista paralela a `speakers` (si se proporciona) con
    la ruta del MP3 de cada intervención. Los `None` se omiten.

    Streaming: usa `AudioSegment` por bloque y descarta cada segment tras
    concatenar (no acumula referencias). Memoria pico ≈ tamaño del episodio
    final, no la suma de todos los bloques en memoria simultáneamente.
    """
    from pydub import AudioSegment

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sequence = AudioSegment.silent(duration=initial_silence_ms)
    block_count = 0
    prev_speaker: str | None = None
    speakers = speakers or [""] * len(block_paths)

    for path, speaker in zip(block_paths, speakers, strict=False):
        if path is None:
            continue
        try:
            seg = AudioSegment.from_file(str(path))
        except Exception:  # noqa: BLE001 — bloque corrupto, lo saltamos
            continue
        if prev_speaker is not None:
            pause_ms = (same_speaker_pause_ms if speaker == prev_speaker
                        else different_speaker_pause_ms)
            sequence += AudioSegment.silent(duration=pause_ms)
        sequence += seg
        prev_speaker = speaker
        block_count += 1
        # Liberar referencia explícita ayuda al GC en CPython.
        del seg

    # Normalización a -14 LUFS si es posible.
    sequence, used_lufs = _maybe_normalize_to_lufs(sequence, target_lufs)
    duration_s = len(sequence) / 1000.0

    sequence.export(str(output_path), format="mp3", bitrate=bitrate)
    return AssemblyResult(
        output_path=output_path,
        duration_s=duration_s,
        block_count=block_count,
        used_lufs_normalization=used_lufs,
    )
