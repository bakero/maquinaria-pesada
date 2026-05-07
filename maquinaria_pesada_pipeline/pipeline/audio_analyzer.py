"""
Analiza la estructura temporal del audio del episodio.

Patron esperado:
  [0.0 .. silencio_inicial .. HOOK .. silencio .. SINTONIA .. silencio .. CONTENIDO .. silencio_final]

Usa ffmpeg silencedetect para identificar los limites de cada bloque.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

from .logger import get_logger

# Umbrales por defecto para silencedetect.
# El audio del podcast lleva musica de fondo durante el contenido, por lo
# que los "silencios" reales son caidas de volumen de ~-20dB sostenidas
# durante 1.5-3s. Estos valores estan calibrados con el M0.
DEFAULT_SILENCE_THRESHOLD_DB = "-20dB"
DEFAULT_MIN_SILENCE_S = 1.5


def detect_silences(audio_path: str | Path,
                    threshold_db: str = DEFAULT_SILENCE_THRESHOLD_DB,
                    min_silence_s: float = DEFAULT_MIN_SILENCE_S) -> list[dict]:
    """
    Devuelve lista de silencios: [{"start": s, "end": s, "duration": s}, ...]
    """
    log = get_logger("audio_analyzer")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg no esta en PATH")

    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(audio_path),
        "-af", f"silencedetect=noise={threshold_db}:d={min_silence_s}",
        "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stderr or "") + (proc.stdout or "")

    silences = []
    starts = [float(m.group(1)) for m in re.finditer(
        r"silence_start:\s*([\d.]+)", output)]
    ends_durs = [
        (float(m.group(1)), float(m.group(2)))
        for m in re.finditer(
            r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)",
            output)
    ]

    for i, start in enumerate(starts):
        if i < len(ends_durs):
            end, dur = ends_durs[i]
            silences.append({
                "start":    round(start, 3),
                "end":      round(end, 3),
                "duration": round(dur, 3),
            })
    log.info(f"Detectados {len(silences)} silencios "
             f"(threshold={threshold_db}, min={min_silence_s}s)")
    return silences


def get_audio_duration(audio_path: str | Path) -> float:
    if shutil.which("ffprobe") is None:
        return 0.0
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
        ], text=True).strip()
        return float(out)
    except Exception:
        return 0.0


def analyze_episode_audio(audio_path: str | Path,
                          intro_video_path: str | Path | None,
                          output_folder: str | Path,
                          force: bool = False) -> dict:
    """
    Detecta los hitos del audio del episodio:
      - lead_silence_end: fin del silencio inicial (~2s)
      - hook_end:         comienzo del silencio post-hook
      - sintonia_start:   comienzo de la sintonia
      - sintonia_end:     fin de la sintonia
      - content_start:    comienzo del contenido del episodio
      - content_end:      ultimo silencio (3s finales)

    El algoritmo:
      1. Detecta los silencios (>=1.2s).
      2. El silencio que empiece en t<=1.5s y dure ~2s -> lead silence.
      3. El primer silencio post-lead marca el final del HOOK.
      4. Si conocemos la duracion del intro_video, podemos identificar la
         sintonia: bloque entre dos silencios cuya duracion sea similar a
         la del intro_video.
      5. El siguiente silencio post-sintonia marca el inicio del CONTENIDO.
    """
    log = get_logger("audio_analyzer")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    cache = output_folder / "audio_structure.json"

    if cache.exists() and not force:
        log.info(f"audio_structure cacheado: {cache.name}")
        return json.loads(cache.read_text(encoding="utf-8"))

    duration = get_audio_duration(audio_path)
    silences = detect_silences(audio_path)

    intro_dur = get_audio_duration(intro_video_path) if intro_video_path else 0.0
    log.info(f"  duracion_audio={duration:.2f}s · duracion_intro_video={intro_dur:.2f}s")

    structure = {
        "audio_duration":   round(duration, 3),
        "intro_video_duration": round(intro_dur, 3),
        "silences":         silences,
        "lead_silence_end": 0.0,
        "hook_start":       0.0,
        "hook_end":         None,
        "sintonia_start":   None,
        "sintonia_end":     None,
        "content_start":    None,
        "content_end":      round(duration, 3),
    }

    if not silences:
        log.warning("No se detectaron silencios significativos.")
        cache.write_text(json.dumps(structure, indent=2, ensure_ascii=False),
                         encoding="utf-8")
        return structure

    # 1) Lead silence (silencio inicial cerca de t=0)
    if silences[0]["start"] <= 1.5:
        structure["lead_silence_end"] = silences[0]["end"]
        structure["hook_start"] = silences[0]["end"]
        remaining = silences[1:]
    else:
        # No hay lead silence claro
        remaining = silences

    if not remaining:
        # Solo hay un silencio inicial; el resto es hook + nada mas
        structure["hook_end"] = structure["audio_duration"]
        cache.write_text(json.dumps(structure, indent=2, ensure_ascii=False),
                         encoding="utf-8")
        return structure

    # 2) Hook end = primer silencio despues del lead
    hook_end_silence = remaining[0]
    structure["hook_end"] = hook_end_silence["start"]
    sintonia_start = hook_end_silence["end"]
    structure["sintonia_start"] = sintonia_start

    # 3) Sintonia end: el siguiente silencio cuya duracion del bloque previo
    #    sea similar a la del intro_video (tolerancia ±25%).
    sintonia_end = None
    if len(remaining) >= 2 and intro_dur > 0:
        for sil in remaining[1:]:
            block_dur = sil["start"] - sintonia_start
            if abs(block_dur - intro_dur) / max(intro_dur, 1) < 0.25:
                sintonia_end = sil["start"]
                content_start = sil["end"]
                break
    if sintonia_end is None and len(remaining) >= 2:
        # Fallback: usar el siguiente silencio
        sintonia_end = remaining[1]["start"]
        content_start = remaining[1]["end"]

    if sintonia_end is not None:
        structure["sintonia_end"] = round(sintonia_end, 3)
        structure["content_start"] = round(content_start, 3)
    else:
        structure["sintonia_end"] = round(sintonia_start + intro_dur, 3) if intro_dur else None
        structure["content_start"] = round(structure["sintonia_end"] or sintonia_start, 3)

    # NO extendemos sintonia_end mas alla del rango detectado en el audio:
    # si lo extendieramos, el intro_video se mostraria mientras el audio ya
    # esta en silencio (desfase visual/audio). El compositor recortara el
    # intro_video al sintonia_dur real con `-t`.

    # 4) Content end: si hay silencio final largo (>2s), excluirlo
    if silences and silences[-1]["end"] >= duration - 0.5 and silences[-1]["duration"] >= 2.0:
        structure["content_end"] = round(silences[-1]["start"], 3)

    log.info(
        f"  hook=[{structure['hook_start']:.2f},{structure['hook_end']:.2f}] · "
        f"sintonia=[{structure['sintonia_start']},{structure['sintonia_end']}] · "
        f"contenido=[{structure['content_start']},{structure['content_end']}]"
    )

    cache.write_text(json.dumps(structure, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    return structure
