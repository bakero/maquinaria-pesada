"""
Paso 07 - Metadata YouTube + thumbnail.
"""

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .logger import get_logger
from .brand import SECTION_LABELS


def _format_ts(seconds: float) -> str:
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _build_chapters(content: dict, transcription: dict, intro_offset: float) -> list[dict]:
    duration = transcription.get("duration_seconds", 0.0) or 0.0
    sections = [s for s in content.get("sections", [])
                if s["name"] not in ("INTRO_SONIDO", "VERIFICACIONES")]
    if not sections:
        return [{"time": "0:00", "label": "Episodio"}]

    total_words = sum(
        sum(len(iv["text"].split()) or 1 for iv in s["interventions"]) or 1
        for s in sections
    ) or 1
    cursor = 0.0
    chapters = []
    for s in sections:
        ws = sum(len(iv["text"].split()) or 1 for iv in s["interventions"]) or 1
        share = ws / total_words
        chapters.append({
            "time": _format_ts(cursor + intro_offset),
            "label": SECTION_LABELS.get(s["name"], s["name"].replace("_", " ").title()),
        })
        cursor += duration * share
    if chapters and chapters[0]["time"] != "0:00":
        chapters.insert(0, {"time": "0:00", "label": "Intro"})
    return chapters


def _make_thumbnail(out_path: Path, episode_id: str, title: str,
                    resolution=(1920, 1080)) -> None:
    w, h = resolution
    img = Image.new("RGB", (w, h), (13, 13, 13))
    d = ImageDraw.Draw(img)
    # banda amarilla
    d.rectangle((0, h - 80, w, h), fill=(245, 196, 0))
    # rejilla
    for x in range(0, w, 80):
        d.line([(x, 0), (x, h - 80)], fill=(26, 26, 26))
    for y in range(0, h - 80, 80):
        d.line([(0, y), (w, y)], fill=(26, 26, 26))

    candidates = ["C:/Windows/Fonts/ariblk.ttf", "C:/Windows/Fonts/impact.ttf"]
    try:
        font_big = next(ImageFont.truetype(c, 130) for c in candidates if Path(c).exists())
        font_id = next(ImageFont.truetype(c, 70) for c in candidates if Path(c).exists())
        font_brand = next(ImageFont.truetype(c, 48) for c in candidates if Path(c).exists())
    except StopIteration:
        font_big = ImageFont.load_default()
        font_id = ImageFont.load_default()
        font_brand = ImageFont.load_default()

    d.text((80, 120), episode_id.upper(), font=font_id, fill=(245, 196, 0))
    # Titulo en varias lineas si es largo
    words = title.split()
    line, lines = "", []
    for w_ in words:
        if len(line + " " + w_) > 22:
            lines.append(line.strip())
            line = w_
        else:
            line = line + " " + w_
    lines.append(line.strip())
    y_text = 220
    for ln in lines[:4]:
        d.text((80, y_text), ln.upper(), font=font_big, fill=(232, 232, 232))
        y_text += 140
    d.text((80, h - 70), "MAQUINARIA PESADA", font=font_brand, fill=(13, 13, 13))
    img.save(out_path, "JPEG", quality=92)


def generate_metadata(config: dict, content: dict, transcription: dict,
                      output_folder: str | Path, episode_id: str,
                      intro_duration: float = 0.0) -> dict:
    log = get_logger("07_metadata_generator")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    title = (
        f"MaquinarIA Pesada · {episode_id} · "
        + ", ".join(content.get("concepts", [])[:3]).strip(", ")
    )

    chapters = _build_chapters(content, transcription, intro_duration)

    description_lines = [
        "🏗 MaquinarIA Pesada — Videopodcast de IA generado con IA.",
        "",
        "En este episodio:",
    ]
    for s in content.get("sections", []):
        if s["name"] in ("INTRO_SONIDO", "VERIFICACIONES"):
            continue
        description_lines.append(
            f"• {SECTION_LABELS.get(s['name'], s['name'].replace('_', ' ').title())}"
        )
    description_lines += ["", "⏱ Capítulos:"]
    for ch in chapters:
        description_lines.append(f"{ch['time']} {ch['label']}")
    description_lines += [
        "",
        "🤖 Producido al 100% con IA — guion, voces y vídeo.",
        "🎙 Voces: María (amarillo) e Iago (azul) generadas con ElevenLabs.",
    ]

    tags = list({
        "inteligencia artificial", "IA", "machine learning", "podcast",
        "tecnologia", "automatizacion", "maquinaria pesada",
        *content.get("concepts", [])[:15],
    })

    metadata = {
        "title":       title,
        "description": "\n".join(description_lines),
        "chapters":    chapters,
        "tags":        tags,
    }

    metadata_path = output_folder / f"{episode_id}_youtube_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False),
                             encoding="utf-8")

    thumb_path = output_folder / f"{episode_id}_thumbnail.jpg"
    _make_thumbnail(thumb_path, episode_id,
                    title.split("·")[-1].strip() or "Episodio",
                    (1920, 1080))

    log.info(f"Metadata guardada: {metadata_path.name}")
    log.info(f"Thumbnail generado: {thumb_path.name}")
    return metadata
