"""
Detecta el offset EXACTO donde la sintonia (Sintonia Maquinaria pesada.mp3)
empieza dentro del audio del episodio, usando correlacion cruzada.

Funciona aunque la sintonia este mezclada con efectos o haya silencio
imperfecto alrededor: la firma de la sintonia es unica.

Uso:
    from pipeline.sintonia_detector import detect_sintonia_offset
    offset_s, conf = detect_sintonia_offset(
        episode_audio_path, sintonia_audio_path)
    # offset_s = segundo donde empieza la sintonia en el episodio
    # conf = 0..1, mayor = mas seguro

Robusto: si scipy/numpy no estan, devuelve None.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from .logger import get_logger


def _decode_to_mono_pcm(audio_path: str | Path, out_path: Path,
                       sample_rate: int = 16000) -> bool:
    """ffmpeg: convierte a WAV mono 16kHz para correlacion (16k es suficiente)."""
    if shutil.which("ffmpeg") is None:
        return False
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(audio_path),
        "-ac", "1", "-ar", str(sample_rate),
        "-c:a", "pcm_s16le",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return out_path.exists() and out_path.stat().st_size > 100
    except subprocess.CalledProcessError:
        return False


def detect_sintonia_offset(episode_audio: str | Path,
                            sintonia_audio: str | Path,
                            sample_rate: int = 16000,
                            search_max_seconds: float = 90.0) -> tuple[float | None, float]:
    """
    Devuelve (offset_seg_en_episode, confianza_0_1).

    Strategy:
      1. Convierte ambos a mono 16kHz PCM.
      2. Lee solo los primeros `search_max_seconds` del episodio (la
         sintonia esta en el primer minuto seguro).
      3. Correlacion cruzada normalizada de la sintonia contra el episodio.
      4. El pico de correlacion es el offset.

    Si scipy/numpy faltan o falla: (None, 0.0).
    """
    log = get_logger("sintonia_detector")

    try:
        import wave

        import numpy as np
        from scipy.signal import correlate
    except ImportError as exc:
        log.warning(f"numpy/scipy no disponible: {exc}")
        return None, 0.0

    if not (Path(episode_audio).exists() and Path(sintonia_audio).exists()):
        log.warning("episode o sintonia audio no existen")
        return None, 0.0

    with tempfile.TemporaryDirectory() as tmpdir:
        ep_wav = Path(tmpdir) / "ep.wav"
        sin_wav = Path(tmpdir) / "sin.wav"

        if not _decode_to_mono_pcm(episode_audio, ep_wav, sample_rate):
            return None, 0.0
        if not _decode_to_mono_pcm(sintonia_audio, sin_wav, sample_rate):
            return None, 0.0

        # Leer episodio limitado a search_max_seconds
        with wave.open(str(ep_wav), "rb") as w:
            sr = w.getframerate()
            n_frames_total = w.getnframes()
            n_frames_read = min(n_frames_total, int(search_max_seconds * sr))
            ep_bytes = w.readframes(n_frames_read)
        ep = np.frombuffer(ep_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        with wave.open(str(sin_wav), "rb") as w:
            sin_bytes = w.readframes(w.getnframes())
            sr_sin = w.getframerate()
        sin = np.frombuffer(sin_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        if sr != sr_sin:
            log.warning(f"sample rates difieren: ep={sr}, sin={sr_sin}")
            return None, 0.0

        # Normalizar amplitud (centrar y unitarizar) para correlacion robusta
        ep -= ep.mean()
        sin -= sin.mean()
        sin_norm = sin / (np.linalg.norm(sin) + 1e-12)

        # Correlacion cruzada: usamos modo 'valid' para que el pico sea el offset
        # de inicio. (sin debe caber dentro de ep para que sea valido).
        if len(sin) >= len(ep):
            log.warning("sintonia mas larga que la ventana del episodio")
            return None, 0.0

        # FFT-based correlacion eficiente
        log.info(f"  correlacionando {len(sin)/sr:.1f}s sintonia contra "
                 f"{len(ep)/sr:.1f}s episodio...")
        corr = correlate(ep, sin_norm, mode="valid", method="fft")

        # El pico es el offset en samples
        peak_idx = int(np.argmax(corr))
        peak_value = float(corr[peak_idx])

        # Confianza: ratio peak / mediana(|corr|)
        # Pico claro >> mediana => ratio alto, distinguible del ruido
        median_abs = float(np.median(np.abs(corr)) + 1e-12)
        confidence = peak_value / max(median_abs, 1e-12)
        # Normalizar a 0..1 con saturacion: ratio>=20 => conf=1.0
        confidence_norm = min(1.0, max(0.0, (confidence - 3.0) / 17.0))

        offset_seconds = peak_idx / float(sr)
        log.info(f"  offset detectado = {offset_seconds:.3f}s, "
                 f"peak/median ratio={confidence:.1f}, conf_norm={confidence_norm:.2f}")
        return offset_seconds, confidence_norm


def detect_sintonia_range(episode_audio: str | Path,
                           sintonia_audio: str | Path,
                           min_confidence: float = 0.4
                           ) -> tuple[float, float] | None:
    """
    Devuelve (sintonia_start, sintonia_end) en segundos del episodio.
    None si no se detecta con suficiente confianza.
    """
    log = get_logger("sintonia_detector")
    offset, conf = detect_sintonia_offset(episode_audio, sintonia_audio)
    if offset is None or conf < min_confidence:
        log.warning(f"Sintonia NO detectada con suficiente confianza "
                    f"(conf={conf:.2f} < {min_confidence}). Fallback a silencedetect.")
        return None

    # Duracion del archivo de sintonia
    if shutil.which("ffprobe") is None:
        return None
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(sintonia_audio),
        ], text=True).strip()
        sintonia_dur = float(out)
    except Exception:
        return None

    return (round(offset, 3), round(offset + sintonia_dur, 3))
