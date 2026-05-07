"""
Paso 05 - Generacion de subtitulos SRT con keywords resaltados.

Whisper devuelve segments con texto y timestamps. Convertimos a SRT
agrupando palabras en bloques de ~7 palabras / 3 segundos.
Las keywords definidas en content_data se envuelven en <font color>.
"""

import json
import re
from pathlib import Path

from .logger import get_logger


def _format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _highlight(text: str, keywords: list[str], color: str = "#F5C400") -> str:
    """Envuelve cada keyword en <font color="..."> ... </font>."""
    if not keywords:
        return text
    out = text
    for kw in sorted(keywords, key=len, reverse=True):
        if not kw or len(kw) < 2:
            continue
        pattern = re.compile(r"(?<!\w)(" + re.escape(kw) + r")(?!\w)", re.IGNORECASE)
        out = pattern.sub(rf'<font color="{color}">\1</font>', out)
    return out


def generate_srt(transcription: dict, content: dict,
                 output_folder: str | Path,
                 episode_id: str,
                 max_words: int = 7,
                 max_duration: float = 3.0,
                 force: bool = False) -> str:
    """Genera EP-MODXXX_subtitulos.srt y devuelve la ruta."""
    log = get_logger("05_subtitle_generator")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    srt_path = output_folder / f"{episode_id}_subtitulos.srt"

    if srt_path.exists() and not force:
        log.info(f"SRT cacheado: {srt_path.name}")
        return str(srt_path)

    keywords = content.get("keywords", [])
    words = transcription.get("words", [])

    if not words:
        # Fallback: usar segments
        segments = transcription.get("segments", [])
        lines = []
        for i, seg in enumerate(segments, start=1):
            lines.append(str(i))
            lines.append(f"{_format_timestamp(seg['start'])} --> {_format_timestamp(seg['end'])}")
            lines.append(_highlight(seg.get("text", "").strip(), keywords))
            lines.append("")
        srt_path.write_text("\n".join(lines), encoding="utf-8")
        log.info(f"SRT (segments) generado: {srt_path.name}")
        return str(srt_path)

    chunks = []
    current = []
    current_start = None
    for w in words:
        if current_start is None:
            current_start = w["start"]
        current.append(w)
        chunk_dur = w["end"] - current_start
        end_punct = w["word"].rstrip().endswith((".", "?", "!"))
        if (len(current) >= max_words or chunk_dur >= max_duration or end_punct) and current:
            chunks.append({
                "start": current_start,
                "end":   w["end"],
                "text":  " ".join(c["word"] for c in current).strip(),
            })
            current = []
            current_start = None
    if current:
        chunks.append({
            "start": current_start,
            "end":   current[-1]["end"],
            "text":  " ".join(c["word"] for c in current).strip(),
        })

    lines = []
    for i, ck in enumerate(chunks, start=1):
        lines.append(str(i))
        lines.append(f"{_format_timestamp(ck['start'])} --> {_format_timestamp(ck['end'])}")
        lines.append(_highlight(ck["text"], keywords))
        lines.append("")
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"SRT generado: {len(chunks)} bloques en {srt_path.name}")
    return str(srt_path)
