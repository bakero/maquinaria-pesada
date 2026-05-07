"""
Adaptador: escaleta parseada -> scene_timeline.json + scene_track.json

Toma el output del escaleta_parser y construye los archivos canonicos
que consume el resto del pipeline (overlay_renderer y video_compositor).

scene_timeline.json: lista de escenas con overlays para PIL renderer.
scene_track.json:    lista de segmentos (estudio/pizarra/blank) para
                     el compositor.
"""

import json
import re
from pathlib import Path

from .logger import get_logger


# ─── Mapeos ─────────────────────────────────────────────────────────────

# Plano de la escaleta -> slug de la library + tipo de segmento del track
PLANO_TO_SLUG = {
    "ESTABLISHING":         ("studio_establishing_general",     "studio"),
    "TWO_SHOT_M_ACTIVE":    ("studio_maria_speaks_yago_listens","studio"),
    "TWO_SHOT_Y_ACTIVE":    ("studio_yago_speaks_maria_listens","studio"),
    "CLOSE_UP_MARIA":       ("studio_maria_speaking_close",     "studio"),
    "CLOSE_UP_YAGO":        ("studio_yago_speaking_close",      "studio"),
    "DETAIL":               ("studio_detail_microphone",        "studio"),
    "BOTH_COMPLICIT":       ("studio_both_complicit",           "studio"),
    "OUTRO":                ("studio_outro_closing",            "studio"),
    "BLACK":                (None,                               "blank"),
    "PIZARRA":              (None,                               "pizarra"),
}

# Tipo on_screen escaleta -> tipo overlay del overlay_types.py
ELEM_TYPE_MAP = {
    "stat_card":            "stat_card",
    "name_tag":             "name_tag",
    "section_indicator":    "section_indicator",
    "section_title":        "section_indicator",
    "hierarchy_diagram":    "hierarchy_diagram",
    "hierarchy":            "hierarchy_diagram",
    "hierarchy_visual":     "hierarchy_diagram",
    "two_column_compare":   "two_column_compare",
    "compare":              "two_column_compare",
    "comparison":           "two_column_compare",
    "bar_chart":            "bar_chart",
    "barchart":             "bar_chart",
    "timeline":             "timeline_visual",
    "timeline_visual":      "timeline_visual",
    "timeline_regulation":  "timeline_visual",
    "regulation_alert":     "regulation_alert",
    "alert":                "regulation_alert",
    "warning":              "warning_badge",
    "warning_badge":        "warning_badge",
    "highlight_quote":      "highlight_quote",
    "quote":                "highlight_quote",
    "concept_card":         "highlight_quote",
    "concept_card_image":   "highlight_quote",
    "concept":              "highlight_quote",
    "badge":                "warning_badge",
    "recap_grid":           "recap_grid",
    "recap":                "recap_grid",
    "end_card":             "end_card",
    "logo_show":            "warning_badge",
    "logo_title":           "warning_badge",
    "subtitle":             "section_indicator",
    "examples_grid":        "recap_grid",
    "examples":             "recap_grid",
    "fade_to_content":      None,    # no renderiza, marca transicion
    "transition_to_timeline": None,
    "limpieza_pantalla":    None,
    "transition":           None,
    "fade":                 None,
    "sticker":              "sticker",
}

POSITION_MAP = {
    "TOP_LEFT":          "TOP_LEFT",
    "TOP_CENTER":        "TOP_CENTER",
    "TOP_RIGHT":         "TOP_RIGHT",
    "MID_LEFT":          "MID_LEFT",
    "MID_CENTER":        "MID_CENTER",
    "MID_RIGHT":         "MID_RIGHT",
    "BOTTOM_LEFT":       "BOTTOM_LEFT",
    "BOTTOM_CENTER":     "BOTTOM_CENTER",
    "BOTTOM_RIGHT_SAFE": "BOTTOM_RIGHT_SAFE",
    "BOTTOM_FULL_WIDTH": "BOTTOM_FULL_WIDTH",
    # Variantes / sinonimos
    "CENTER":            "MID_CENTER",
    "FULLSCREEN":        "MID_CENTER",
    "OVERLAY_CENTER":    "MID_CENTER",
    "LEFT":              "MID_LEFT",
    "RIGHT":             "MID_RIGHT",
    "LEFT_STACK":        "MID_LEFT",
    "RIGHT_STACK":       "MID_RIGHT",
    "CENTER_STACK":      "MID_CENTER",
    "MID":               "MID_CENTER",
}


# ─── Helpers ────────────────────────────────────────────────────────────


def _normalize_position(pos: str | None) -> str:
    if not pos:
        return "MID_CENTER"
    return POSITION_MAP.get(pos.strip().upper(), "MID_CENTER")


def _build_overlay_data(elem_type: str, raw: str, label: str,
                        color: str | None) -> dict:
    """Construye el dict 'data' del overlay segun el tipo."""
    speaker_color = color or "#F5C400"
    if elem_type == "stat_card":
        # Buscar valor (numero/%) y subtitulo
        m_val = re.search(r"(\d{1,3}(?:[.,]\d+)?\s*(?:%|M|K|B)?|€\d+M?|\$\d+M?)",
                           raw)
        value = m_val.group(0) if m_val else label.split()[0] if label else ""
        # Label = primera parte; subtitulo = resto
        parts = re.split(r"·|\|", label, maxsplit=1)
        return {
            "label":    (parts[0].strip().upper() if parts else "DATO")[:32],
            "value":    value or label[:8],
            "subtitle": (parts[1].strip() if len(parts) > 1 else "")[:48],
            "color":    speaker_color,
        }
    if elem_type == "name_tag":
        return {"name": label.upper()[:8], "color": speaker_color}
    if elem_type == "section_indicator":
        return {"label": label[:40]}
    if elem_type == "hierarchy_diagram":
        # items separados por flechas o comas
        items = re.split(r"→|->|⊃|,|·", label)
        items = [it.strip() for it in items if it.strip()][:6]
        return {"title": "Taxonomia", "items": items or ["IA"]}
    if elem_type == "two_column_compare":
        parts = re.split(r"vs\.?|≠|frente a|\bvs\b", label, flags=re.IGNORECASE)
        return {
            "left_title":  (parts[0] if len(parts) >= 1 else "A")[:20],
            "right_title": (parts[1] if len(parts) >= 2 else "B")[:20],
            "left_items":  [],
            "right_items": [],
        }
    if elem_type == "bar_chart":
        return {"title": label[:32], "bars": [
            {"label": "A", "value": 80}, {"label": "B", "value": 60},
        ]}
    if elem_type == "timeline_visual":
        items = []
        for m in re.finditer(r"(\d{4}|\d{2}\d{2}s)\s*[·|-]?\s*([^·|→]+)", label):
            items.append({"year": m.group(1).strip(), "label": m.group(2).strip()[:24]})
        if not items:
            items = [{"year": "—", "label": label[:24]}]
        return {"items": items[:5]}
    if elem_type == "regulation_alert":
        parts = re.split(r"·|\|", label, maxsplit=1)
        return {
            "title": (parts[0] if parts else "REGULACIÓN").strip()[:24],
            "text":  (parts[1] if len(parts) > 1 else label).strip()[:60],
        }
    if elem_type == "warning_badge":
        return {"label": label[:24]}
    if elem_type == "highlight_quote":
        return {"text": label[:200], "author": ""}
    if elem_type == "recap_grid":
        items = re.split(r"·|,|\|", label)
        items = [it.strip()[:24] for it in items if it.strip()][:8]
        return {"items": items}
    if elem_type == "end_card":
        return {"title": "MaquinarIA Pesada", "subtitle": label[:48]}
    return {"label": label[:40], "color": speaker_color}


# ─── Conversion ─────────────────────────────────────────────────────────


def parsed_escaleta_to_scene_timeline(parsed: dict) -> dict:
    """Convierte la escaleta parseada en scene_timeline.json."""
    scenes = []
    for block in parsed["blocks"]:
        for iv in block["interventions"]:
            iv_start = iv["tc_in"]
            iv_end = iv["tc_out"]
            speaker = iv["speaker"] or ""
            speaker_color = "#F5C400" if speaker == "MARIA" else "#4DB8FF" if speaker in ("YAGO", "IAGO") else "#888888"

            overlays = []
            # name_tag siempre que haya speaker
            if speaker:
                overlays.append({
                    "type": "name_tag", "position": "TOP_RIGHT",
                    "data": {"name": speaker, "color": speaker_color},
                    "start": iv_start, "end": iv_end,
                })

            # On-screen items
            for os_item in iv.get("on_screen", []):
                elem_type = ELEM_TYPE_MAP.get(os_item["element"].lower())
                if not elem_type:
                    continue
                # sticker se procesa aparte (lo metemos como sticker scene-level)
                if elem_type == "sticker":
                    continue
                t_abs_in = iv_start + os_item["t_rel"]
                # out_t_rel es relativo: si > duration, es absoluto al final
                if os_item["out_t_rel"] >= iv["duration"]:
                    t_abs_out = iv_end
                else:
                    t_abs_out = iv_start + os_item["out_t_rel"]
                t_abs_out = max(t_abs_in + 0.5, min(t_abs_out, iv_end))

                overlays.append({
                    "type":     elem_type,
                    "position": _normalize_position(os_item["position"]),
                    "data":     _build_overlay_data(
                                    elem_type, os_item["raw"],
                                    os_item.get("label_text") or "",
                                    os_item.get("color"),
                                ),
                    "start":    round(t_abs_in, 3),
                    "end":      round(t_abs_out, 3),
                })

            stickers = []
            for os_item in iv.get("on_screen", []):
                if ELEM_TYPE_MAP.get(os_item["element"].lower()) == "sticker":
                    name_match = re.search(r'"([^"]+)"', os_item["raw"])
                    sticker_name = (name_match.group(1) if name_match
                                    else os_item.get("label_text", "")
                                    ).replace(".png", "").strip()
                    if not sticker_name:
                        continue
                    stickers.append({
                        "name": sticker_name,
                        "position": _normalize_position(os_item["position"]),
                        "start":    round(iv_start + os_item["t_rel"], 3),
                        "end":      round(iv_start + os_item["out_t_rel"], 3),
                    })

            scenes.append({
                "start":      iv_start,
                "end":        iv_end,
                "section":    block["name"],
                "speaker":    speaker,
                "background": "industrial_grid",
                "text":       iv.get("text", ""),
                "tones":      [iv["tono"]] if iv.get("tono") else [],
                "plano":      iv["plano"],
                "overlays":   overlays,
                "stickers":   stickers,
                "_from_escaleta": True,
            })
    return {"background": "industrial_grid", "scenes": scenes}


def parsed_escaleta_to_scene_track(parsed: dict, library,
                                    audio_duration: float | None = None) -> list[dict]:
    """Convierte la escaleta en scene_track (estudio/pizarra/blank) usando
    el plano definido en cada intervencion."""
    log = get_logger("escaleta_to_pipeline")
    track = []
    for block in parsed["blocks"]:
        for iv in block["interventions"]:
            plano = iv["plano"].upper()
            slug, seg_type = PLANO_TO_SLUG.get(plano, (None, "pizarra"))

            seg = {
                "start":   iv["tc_in"],
                "end":     iv["tc_out"],
                "speaker": iv["speaker"],
                "section": block["name"],
                "type":    seg_type,
                "plano":   plano,
            }
            if seg_type == "studio" and slug:
                lib_entry = library.find(slug)
                if lib_entry:
                    seg["source"] = lib_entry["path"]
                else:
                    log.warning(f"  plano {plano} -> {slug} no en library, "
                                f"caera a establishing")
                    fallback = library.find("studio_establishing_general")
                    if fallback:
                        seg["source"] = fallback["path"]
                    else:
                        seg["type"] = "pizarra"
            track.append(seg)

    # Consolidar consecutivos del mismo source
    track.sort(key=lambda s: s["start"])
    consolidated = []
    for seg in track:
        if (consolidated
                and consolidated[-1]["type"] == seg["type"]
                and consolidated[-1].get("source") == seg.get("source")
                and seg["start"] - consolidated[-1]["end"] < 1.5):
            consolidated[-1]["end"] = seg["end"]
        else:
            consolidated.append(dict(seg))

    # Rellenar gaps con blank (lead silence, gaps internos, sintonia, tail)
    if audio_duration is None:
        audio_duration = consolidated[-1]["end"] if consolidated else 0.0
    filled = []
    cursor = 0.0
    for seg in consolidated:
        s = float(seg["start"])
        if s > cursor + 0.05:
            filled.append({
                "type": "blank", "start": round(cursor, 3),
                "end": round(s, 3), "speaker": "", "section": "GAP",
            })
        filled.append(seg)
        cursor = max(cursor, float(seg["end"]))
    if audio_duration > cursor + 0.05:
        filled.append({
            "type": "blank", "start": round(cursor, 3),
            "end": round(audio_duration, 3), "speaker": "", "section": "TAIL",
        })

    log.info(f"  scene_track desde escaleta: {len(filled)} segmentos "
             f"(de {len(consolidated)} fusionados desde {len(track)})")
    return filled


def write_pipeline_files(parsed: dict, library, output_folder: str | Path,
                          audio_duration: float | None = None) -> tuple[Path, Path]:
    """Escribe scene_timeline.json y scene_track.json al output_folder."""
    log = get_logger("escaleta_to_pipeline")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    timeline = parsed_escaleta_to_scene_timeline(parsed)
    track = parsed_escaleta_to_scene_track(parsed, library, audio_duration)

    timeline_path = output_folder / "scene_timeline.json"
    track_path = output_folder / "scene_track.json"

    timeline_path.write_text(
        json.dumps(timeline, indent=2, ensure_ascii=False),
        encoding="utf-8")
    track_path.write_text(
        json.dumps(track, indent=2, ensure_ascii=False),
        encoding="utf-8")

    log.info(f"  scene_timeline -> {timeline_path}")
    log.info(f"  scene_track    -> {track_path}")
    return timeline_path, track_path
