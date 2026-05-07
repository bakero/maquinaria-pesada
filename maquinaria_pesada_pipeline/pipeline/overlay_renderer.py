"""
Paso 04 - Render de overlays a PNGs por keyframe.

Estrategia:
- Detectamos los "instantes de cambio" (cuando aparece o desaparece algo).
- Para cada intervalo entre dos cambios, generamos UN UNICO frame PNG
  que contiene el background + todos los overlays activos + logo watermark.
- El compositor de ffmpeg luego mostrara cada frame durante su intervalo.

Esto es MUCHISIMO mas barato que renderizar 30fps de frames.
"""

import json
from pathlib import Path

from PIL import Image

from .logger import get_logger
from .brand import POSITIONS_1080P, LOGO_WATERMARK, RESOLUTIONS

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

from templates.background_generators import get_background
from templates.overlay_types import build_overlay
from templates.sticker_manager import get_sticker


def _resolve_position(name: str, w: int, h: int, overlay_size: tuple) -> tuple[int, int]:
    """
    Devuelve (x, y) para colocar un overlay segun la posicion nombrada.
    Considera el tamano del overlay para no salirse de pantalla.
    Mantiene la zona del logo libre.
    """
    ow, oh = overlay_size
    margin = 40
    pos_map = {
        "TOP_LEFT":          (margin, margin),
        "TOP_CENTER":        ((w - ow) // 2, margin),
        "TOP_RIGHT":         (w - ow - margin, margin),
        "MID_LEFT":          (margin, (h - oh) // 2),
        "MID_CENTER":        ((w - ow) // 2, (h - oh) // 2),
        "MID_RIGHT":         (w - ow - margin, (h - oh) // 2),
        "BOTTOM_LEFT":       (margin, h - oh - margin),
        "BOTTOM_CENTER":     ((w - ow) // 2, h - oh - margin),
        "BOTTOM_RIGHT_SAFE": (w - ow - margin, h - oh - 120),  # arriba del logo
        "BOTTOM_FULL_WIDTH": (margin, h - oh - margin),
    }
    return pos_map.get(name, pos_map["MID_CENTER"])


def _collect_keyframes(timeline: dict, total_duration: float) -> list[float]:
    """Lista ordenada de instantes en los que cambian overlays activos."""
    times = {0.0, round(total_duration, 3)}
    for scene in timeline.get("scenes", []):
        times.add(round(float(scene.get("start", 0.0)), 3))
        times.add(round(float(scene.get("end", 0.0)), 3))
        for ov in scene.get("overlays", []):
            times.add(round(float(ov.get("start", 0.0)), 3))
            times.add(round(float(ov.get("end", 0.0)), 3))
        for st in scene.get("stickers", []):
            times.add(round(float(st.get("start", 0.0)), 3))
            times.add(round(float(st.get("end", 0.0)), 3))
    return sorted(t for t in times if 0 <= t <= total_duration)


def _active_at(scene: dict, t: float) -> tuple[list, list]:
    overlays = [
        ov for ov in scene.get("overlays", [])
        if float(ov.get("start", 0)) <= t < float(ov.get("end", 0))
    ]
    stickers = [
        s for s in scene.get("stickers", [])
        if float(s.get("start", 0)) <= t < float(s.get("end", 0))
    ]
    return overlays, stickers


def _scene_at(timeline: dict, t: float) -> dict | None:
    for sc in timeline.get("scenes", []):
        if float(sc.get("start", 0)) <= t < float(sc.get("end", 0)):
            return sc
    return None


def _apply_logo(frame: Image.Image, logo_path: str | Path | None) -> Image.Image:
    if not logo_path or not Path(logo_path).exists():
        return frame
    try:
        logo = Image.open(logo_path).convert("RGBA")
    except Exception:
        return frame
    size = LOGO_WATERMARK["size_px"]
    ratio = size / max(logo.width, logo.height)
    logo = logo.resize((int(logo.width * ratio), int(logo.height * ratio)), Image.LANCZOS)
    # opacidad
    alpha = logo.split()[-1]
    alpha = alpha.point(lambda a: int(a * LOGO_WATERMARK["opacity"]))
    logo.putalpha(alpha)

    margin = LOGO_WATERMARK["margin_px"]
    x = frame.width - logo.width - margin
    y = frame.height - logo.height - margin
    frame.alpha_composite(logo, dest=(x, y))
    return frame


def render_frames(timeline: dict, transcription: dict, config: dict,
                  output_folder: str | Path,
                  preview_seconds: float | None = None,
                  force: bool = False) -> dict:
    """
    Renderiza un PNG por cada cambio de overlays.
    Devuelve un dict con la lista de frames (path, start, end).
    """
    log = get_logger("04_overlay_renderer")
    output_folder = Path(output_folder)
    frames_dir = output_folder / "frames_cache"
    frames_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_folder / "frames_index.json"

    if index_path.exists() and not force:
        log.info(f"frames_index cacheado: {index_path.name}")
        return json.loads(index_path.read_text(encoding="utf-8"))

    res_str = config.get("episode_defaults", {}).get("resolution", "1920x1080")
    w, h = RESOLUTIONS.get(res_str, (1920, 1080))
    duration = transcription.get("duration_seconds", 0.0)
    if preview_seconds:
        duration = min(duration, preview_seconds)

    keyframes = _collect_keyframes(timeline, duration)
    if not keyframes or keyframes[-1] < duration:
        keyframes.append(round(duration, 3))

    logo_path = config.get("assets", {}).get("logo_watermark")
    stickers_folder = config.get("assets", {}).get("stickers_folder")

    frames = []
    for i in range(len(keyframes) - 1):
        t_start = keyframes[i]
        t_end = keyframes[i + 1]
        if t_end - t_start < 0.05:
            continue

        scene = _scene_at(timeline, t_start) or {}
        bg_name = scene.get("background", timeline.get("background", "industrial_grid"))
        frame = get_background(bg_name, w, h).convert("RGBA")

        overlays, stickers = _active_at(scene, t_start)

        # Limitar a 3 overlays simultaneos (excluyendo name_tag)
        non_name = [ov for ov in overlays if ov.get("type") != "name_tag"]
        name_tag_overlays = [ov for ov in overlays if ov.get("type") == "name_tag"]
        non_name = non_name[:3]
        overlays_final = name_tag_overlays + non_name

        for ov in overlays_final:
            img = build_overlay(ov.get("type", ""), ov.get("data", {}))
            if img is None:
                continue
            x, y = _resolve_position(ov.get("position", "MID_CENTER"),
                                     w, h, img.size)
            frame.alpha_composite(img, dest=(x, y))

        for st in stickers:
            sticker = get_sticker(st.get("name", ""), stickers_folder, size=200)
            if sticker is None:
                continue
            x, y = _resolve_position(st.get("position", "BOTTOM_LEFT"),
                                     w, h, sticker.size)
            frame.alpha_composite(sticker, dest=(x, y))

        frame = _apply_logo(frame, logo_path)

        out_path = frames_dir / f"frame_{i:05d}.png"
        frame.convert("RGB").save(out_path, "PNG", optimize=True)
        frames.append({
            "path":  str(out_path),
            "start": round(t_start, 3),
            "end":   round(t_end, 3),
            "duration": round(t_end - t_start, 3),
        })

    index = {
        "resolution": [w, h],
        "duration":   round(duration, 3),
        "frames":     frames,
    }
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Renderizados {len(frames)} keyframes en {frames_dir}")
    return index
