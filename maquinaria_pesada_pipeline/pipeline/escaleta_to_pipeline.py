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

# Plano de la escaleta -> tipo de segmento del track. El SLUG concreto se
# elige en runtime desde el pool del speaker (rotacion sin repetir dentro
# de la misma intervencion).
PLANO_TO_TYPE = {
    "ESTABLISHING":         "studio",
    "TWO_SHOT_M_ACTIVE":    "studio",
    "TWO_SHOT_Y_ACTIVE":    "studio",
    "CLOSE_UP_MARIA":       "studio",
    "CLOSE_UP_YAGO":        "studio",
    "DETAIL":               "studio",
    "BOTH_COMPLICIT":       "studio",
    "OUTRO":                "studio",
    "BLACK":                "blank",
    "PIZARRA":              "pizarra",
}

# Pool de clips disponibles por speaker. La rotacion no repite slug dentro
# de la misma intervencion. Los slugs nuevos (Kling v2) van primero; los
# antiguos quedan como fallback si los Kling aun no se han generado.
SPEAKER_POOL = {
    "MARIA": [
        # Solo Maria (close-medium frontal)
        "studio_maria_solo_v1", "studio_maria_solo_v2",
        "studio_maria_solo_v3", "studio_maria_solo_v4",
        # Two-shot con Maria activa
        "studio_two_m_active_v1", "studio_two_m_active_v2",
        "studio_two_m_active_v3", "studio_two_m_active_v4",
        "studio_two_m_active_v5",
        # Fallbacks legacy
        "studio_maria_speaking_close",
        "studio_maria_speaks_yago_listens",
    ],
    "YAGO": [
        "studio_yago_solo_v1", "studio_yago_solo_v2",
        "studio_yago_solo_v3", "studio_yago_solo_v4",
        "studio_two_y_active_v1", "studio_two_y_active_v2",
        "studio_two_y_active_v3", "studio_two_y_active_v4",
        "studio_two_y_active_v5",
        "studio_yago_speaking_close",
        "studio_yago_speaks_maria_listens",
    ],
    "AMBOS": [
        "studio_establishing_general",
        "studio_both_complicit",
    ],
}

# Plano -> filtro adicional sobre el pool (preferencia por sub-tipo)
PLANO_PREF_TAGS = {
    "CLOSE_UP_MARIA":    ["solo_v"],         # prefiere solo
    "CLOSE_UP_YAGO":     ["solo_v"],
    "TWO_SHOT_M_ACTIVE": ["two_m_active"],   # prefiere two-shot
    "TWO_SHOT_Y_ACTIVE": ["two_y_active"],
    "ESTABLISHING":      ["establishing"],
    "BOTH_COMPLICIT":    ["both_complicit"],
    "OUTRO":             ["outro"],
    "DETAIL":            ["detail"],
}

# Duracion maxima de un solo clip antes de partir en sub-segmentos.
# Kling 1.6 Pro genera 10s nativos.
MAX_CLIP_DUR = 10.0


def _resolve_speaker_pool(plano: str, speaker: str, library) -> list[str]:
    """Devuelve la lista ORDENADA de slugs candidatos para esta combinacion
    plano+speaker, filtrando a los que existen actualmente en la library."""
    speaker_key = "MARIA" if speaker == "MARIA" else "YAGO" if speaker in ("YAGO", "IAGO") else "AMBOS"
    base = list(SPEAKER_POOL.get(speaker_key, SPEAKER_POOL["AMBOS"]))
    pref_tags = PLANO_PREF_TAGS.get(plano, [])
    if pref_tags:
        # Sube al principio los que matchean alguna pref tag
        preferred = [s for s in base if any(t in s for t in pref_tags)]
        rest = [s for s in base if s not in preferred]
        base = preferred + rest
    # Filtrar a los que existen en la library
    available = [s for s in base if library.find(s)]
    return available

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
        # Estrategia: el "valor" es la cifra mas representativa del texto.
        # Prioridades:
        #   1. Cualquier cifra con sufijo % / M / K / B / €$  -> es el valor.
        #   2. Si hay varias cifras, la del subtitulo (despues del " · ")
        #      gana sobre el label (el "ADOPCION 2026" del label es contexto;
        #      el "88%" del subtitulo es el dato).
        #   3. Fallback: primera cifra con sufijo, despues primera palabra.
        parts = re.split(r"·|\|", label, maxsplit=1)
        label_part = parts[0].strip() if parts else ""
        subtitle_part = parts[1].strip() if len(parts) > 1 else ""

        # Patron robusto: numero opcionalmente con coma/punto + sufijo
        # obligatorio (% M K B) o moneda. Asi 2026 (anyo) NO matchea, pero
        # 88% si.
        # Boundary tras el sufijo: espacio, fin, puntuacion (no usamos \b
        # porque % no es word-char y \b fallaria).
        VALUE_RE = re.compile(
            r"(?:€|\$)?\s*\d{1,4}(?:[.,]\d+)?\s*"
            r"(?:%|MM?|K|B|bn|mn|€|\$)(?=\s|$|[.,·|]|[A-Z])",
            re.IGNORECASE,
        )
        # Buscar primero en subtitulo, despues en label, despues en raw.
        value = ""
        for src in (subtitle_part, label_part, raw):
            m = VALUE_RE.search(src)
            if m:
                value = m.group(0).strip()
                break
        # Fallback final: si no hay sufijo claro, el primer numero "limpio"
        # (no anyo) -> rango 1-99 sin contexto de anyo
        if not value:
            for src in (subtitle_part, label_part):
                m = re.search(r"\b(\d{1,3}(?:[.,]\d+)?)\b", src)
                if m and not re.match(r"20[0-9][0-9]", m.group(1)):
                    value = m.group(1)
                    break
        if not value:
            value = (label.split()[0] if label else "")[:8]

        return {
            "label":    label_part.upper()[:32] or "DATO",
            "value":    value or "—",
            "subtitle": subtitle_part[:48],
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
    """Convierte la escaleta en scene_track (estudio/pizarra/blank).

    Reglas de montaje:
      - Cada intervencion -> 1+ segmentos (split si dur > MAX_CLIP_DUR)
      - No se repite el mismo clip dentro de la misma intervencion
      - Pizarra: si la intervencion esta marcada como pizarra, todo el
        rango es pizarra con PIP del presentador (rotacion no-repeat).
    """
    log = get_logger("escaleta_to_pipeline")
    track = []
    iv_counter = 0
    for block in parsed["blocks"]:
        for iv in block["interventions"]:
            iv_counter += 1
            plano = iv["plano"].upper()
            seg_type = PLANO_TO_TYPE.get(plano, "pizarra")
            speaker = iv["speaker"] or ""
            iv_start = float(iv["tc_in"])
            iv_end = float(iv["tc_out"])
            iv_dur = max(0.0, iv_end - iv_start)
            # uses_pizarra: explicito (escaleta v2) o heuristica conservadora.
            # Defecto = studio fullscreen. Pizarra solo cuando hay material
            # visual relevante (datos, listas, comparaciones), no cuando
            # solo hay un name_tag o un sticker.
            if "uses_pizarra" in iv:
                uses_pizarra = bool(iv["uses_pizarra"])
            else:
                heavy_elements = {
                    "stat_card", "hierarchy", "hierarchy_diagram",
                    "hierarchy_visual", "two_column_compare", "compare",
                    "comparison", "bar_chart", "barchart", "timeline",
                    "timeline_visual", "timeline_regulation",
                    "regulation_alert", "highlight_quote", "quote",
                    "concept_card", "concept_card_image", "recap_grid",
                    "recap", "examples_grid", "examples", "end_card",
                }
                rich_count = sum(
                    1 for os_item in (iv.get("on_screen") or [])
                    if (os_item.get("element") or "").lower() in heavy_elements
                )
                uses_pizarra = (
                    plano == "PIZARRA"
                    or (rich_count >= 2 and iv_dur >= 12.0)
                )

            # Resolver pool
            pool = _resolve_speaker_pool(plano, speaker, library)

            # Determinar tipo de segmento final:
            #   - Si la intervencion lleva pizarra -> "pizarra" + PIP
            #   - Si no -> "studio" (o "blank" si plano BLACK)
            if seg_type == "blank" or plano == "BLACK":
                track.append({
                    "start":   iv_start, "end": iv_end,
                    "speaker": speaker, "section": block["name"],
                    "type":    "blank", "plano": plano,
                    "iv_id":   iv_counter,
                })
                continue

            final_type = "pizarra" if uses_pizarra else "studio"

            # Partir la intervencion en sub-segmentos de hasta MAX_CLIP_DUR,
            # asignando un clip distinto del pool a cada uno.
            n_subs = max(1, int((iv_dur + MAX_CLIP_DUR - 0.01) // MAX_CLIP_DUR))
            sub_dur = iv_dur / n_subs
            used_in_iv: list[str] = []
            for k in range(n_subs):
                # Pick: primer slug del pool no usado aun en esta intervencion
                pick = next((s for s in pool if s not in used_in_iv), None)
                if pick is None and pool:
                    pick = pool[k % len(pool)]   # ya recorrido todo el pool
                used_in_iv.append(pick or "")
                lib_entry = library.find(pick) if pick else None
                source_path = lib_entry["path"] if lib_entry else None

                seg_start = iv_start + k * sub_dur
                seg_end = iv_start + (k + 1) * sub_dur if k < n_subs - 1 else iv_end
                seg = {
                    "start":   round(seg_start, 3),
                    "end":     round(seg_end, 3),
                    "speaker": speaker,
                    "section": block["name"],
                    "type":    final_type,
                    "plano":   plano,
                    "iv_id":   iv_counter,
                    "clip_slug": pick,
                }
                if final_type == "studio":
                    if source_path:
                        seg["source"] = source_path
                    else:
                        log.warning(f"  iv{iv_counter} plano {plano}: pool vacio, "
                                    f"cae a pizarra")
                        seg["type"] = "pizarra"
                if final_type == "pizarra" and source_path:
                    # PIP del presentador encima de la pizarra
                    seg["pip_source"] = source_path
                track.append(seg)

    # Sort + sin consolidar (cada sub-seg debe usar su clip propio).
    track.sort(key=lambda s: s["start"])
    consolidated = track  # alias para no romper el resto del codigo

    # CRITICO: eliminar solapamientos. Si la escaleta tiene TCs solapados
    # (fin de N > inicio de N+1), al concatenar el body video se "estira"
    # respecto al audio y los subtitulos quedan desincronizados. Recortamos
    # cada segmento para que termine, como mucho, donde empieza el siguiente.
    overlaps_fixed = 0
    for i in range(len(consolidated) - 1):
        cur_end = float(consolidated[i]["end"])
        next_start = float(consolidated[i + 1]["start"])
        if cur_end > next_start:
            consolidated[i]["end"] = round(next_start, 3)
            overlaps_fixed += 1
    # Descartar segmentos que quedaron con duracion < 0.1s tras el recorte
    consolidated = [
        s for s in consolidated
        if float(s["end"]) - float(s["start"]) >= 0.1
    ]
    if overlaps_fixed:
        log.warning(f"  {overlaps_fixed} solapamientos en escaleta corregidos "
                    f"(track ahora monotonico, audio<->video sin drift)")

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
