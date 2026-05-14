"""Validación post-TTS del audio generado.

Regla A.14 + Audio-Regla 7 (v6). Comprueba el MP3 final: duración dentro de
rango, loudness a -14 LUFS y ausencia de silencios largos.

Usa pydub para medir; si pydub/ffmpeg no están disponibles, las comprobaciones
devuelven un SOFT no-bloqueante explicando que no se pudo medir (degradación
honesta, no se inventa un OK).
"""
from __future__ import annotations

from pathlib import Path

from validators.result import ValidationResult, fail, ok


def _load_segment(audio_path: str | Path):
    """Carga el audio con pydub. Devuelve (segment, error)."""
    try:
        from pydub import AudioSegment
    except ImportError as exc:  # noqa: BLE001
        return None, f"pydub no disponible: {exc}"
    path = Path(audio_path)
    if not path.exists():
        return None, f"el audio no existe: {path}"
    try:
        return AudioSegment.from_file(str(path)), None
    except Exception as exc:  # noqa: BLE001
        return None, f"no se pudo abrir el audio: {exc}"


def check_duration(audio_path: str | Path, min_seconds: float,
                   max_seconds: float) -> ValidationResult:
    """Hard-fail si la duración del audio está fuera de rango."""
    seg, err = _load_segment(audio_path)
    if seg is None:
        return fail("tts_audio_duration", "SOFT",
                    f"No se pudo medir la duración: {err}")
    duration_s = len(seg) / 1000.0
    if min_seconds <= duration_s <= max_seconds:
        return ok("tts_audio_duration", "HARD",
                  f"Duración {duration_s:.1f}s dentro de "
                  f"[{min_seconds}, {max_seconds}]")
    return fail(
        "tts_audio_duration", "HARD",
        f"Duración {duration_s:.1f}s fuera de [{min_seconds}, {max_seconds}]",
        duration_s=duration_s, min_seconds=min_seconds, max_seconds=max_seconds,
    )


def measure_lufs(audio_path: str | Path) -> tuple[float | None, str | None]:
    """Mide el loudness integrado en LUFS.

    Usa `pyloudnorm` si está disponible (estándar EBU R128). Devuelve
    (lufs, error). Si no se puede medir, lufs=None.
    """
    seg, err = _load_segment(audio_path)
    if seg is None:
        return None, err
    try:
        import numpy as np
        import pyloudnorm as pyln
    except ImportError as exc:  # noqa: BLE001
        return None, f"pyloudnorm/numpy no disponible: {exc}"
    try:
        samples = np.array(seg.get_array_of_samples()).astype(np.float64)
        if seg.channels == 2:
            samples = samples.reshape((-1, 2))
        # Normalizar a [-1, 1] según el ancho de muestra.
        max_val = float(1 << (8 * seg.sample_width - 1))
        samples = samples / max_val
        meter = pyln.Meter(seg.frame_rate)
        return float(meter.integrated_loudness(samples)), None
    except Exception as exc:  # noqa: BLE001
        return None, f"error midiendo LUFS: {exc}"


def check_loudness(audio_path: str | Path, target_lufs: float = -14.0,
                   tolerance: float = 0.5) -> ValidationResult:
    """Hard-fail si el loudness integrado no está en target ± tolerance."""
    lufs, err = measure_lufs(audio_path)
    if lufs is None:
        return fail("tts_audio_loudness", "SOFT",
                    f"No se pudo medir el loudness: {err}")
    if abs(lufs - target_lufs) <= tolerance:
        return ok("tts_audio_loudness", "HARD",
                  f"Loudness {lufs:.2f} LUFS dentro de "
                  f"{target_lufs} ± {tolerance}")
    return fail(
        "tts_audio_loudness", "HARD",
        f"Loudness {lufs:.2f} LUFS fuera de {target_lufs} ± {tolerance}",
        lufs=lufs, target_lufs=target_lufs, tolerance=tolerance,
    )


def check_silent_segments(audio_path: str | Path,
                          max_silence_s: float = 2.0,
                          silence_thresh_dbfs: float = -45.0) -> ValidationResult:
    """Soft-warn si hay silencios más largos que `max_silence_s`."""
    seg, err = _load_segment(audio_path)
    if seg is None:
        return fail("tts_audio_silent_segments", "SOFT",
                    f"No se pudo analizar silencios: {err}")
    try:
        from pydub.silence import detect_silence
    except ImportError as exc:  # noqa: BLE001
        return fail("tts_audio_silent_segments", "SOFT",
                    f"pydub.silence no disponible: {exc}")
    silences = detect_silence(
        seg, min_silence_len=int(max_silence_s * 1000),
        silence_thresh=silence_thresh_dbfs,
    )
    if silences:
        longest = max((end - start) for start, end in silences) / 1000.0
        return fail(
            "tts_audio_silent_segments", "SOFT",
            f"{len(silences)} silencio(s) de más de {max_silence_s}s "
            f"(el más largo: {longest:.1f}s)",
            count=len(silences), longest_s=longest,
        )
    return ok("tts_audio_silent_segments", "SOFT",
              f"Sin silencios de más de {max_silence_s}s")


def check_all(audio_path: str | Path, *, min_seconds: float, max_seconds: float,
              target_lufs: float = -14.0, lufs_tolerance: float = 0.5,
              max_silence_s: float = 2.0) -> list[ValidationResult]:
    """Aplica todas las validaciones post-TTS sobre el MP3 final."""
    return [
        check_duration(audio_path, min_seconds, max_seconds),
        check_loudness(audio_path, target_lufs, lufs_tolerance),
        check_silent_segments(audio_path, max_silence_s),
    ]
