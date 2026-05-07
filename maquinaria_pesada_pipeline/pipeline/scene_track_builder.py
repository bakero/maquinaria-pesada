"""
Construye la pista visual del videopodcast alternando ESTUDIO y PIZARRA.

ESTUDIO  = clip MP4 generado con Luma (presentadores hablando)
PIZARRA  = frame PNG generado con Pillow (datos, graficos, conceptos)
BLANK    = fondo neutro (rejilla industrial) para silencios y rango sintonia

La regla general:
  - El HOOK siempre es ESTUDIO con overlay del dato punzante.
  - Cierre del episodio (DESPEDIDA / CIERRE_FINAL) = ESTUDIO outro.
  - El resto: si la escena tiene overlay rico (stat_card, hierarchy, timeline,
    bar_chart, regulation_alert, recap_grid) -> PIZARRA. Si no -> ESTUDIO.
  - El estudio elige toma segun el speaker:
      * MARIA habla   -> studio_maria_speaks_yago_listens
      * YAGO habla    -> studio_yago_speaks_maria_listens
      * close_up cuando la duracion es corta (<8s)
      * complicidad / ironia compartida -> studio_both_complicit
"""

import json
from pathlib import Path

from .logger import get_logger


# Tipos de overlay considerados "ricos" (justifican mostrar pizarra)
RICH_OVERLAY_TYPES = {
    "stat_card", "hierarchy_diagram", "two_column_compare",
    "bar_chart", "timeline_visual", "regulation_alert", "recap_grid",
}

# Mapeo speaker -> slug por defecto cuando el dialogo es corto / individual
DEFAULT_STUDIO_CLIPS = {
    "MARIA":  "studio_maria_speaking_close",
    "IAGO":   "studio_yago_speaking_close",
    "YAGO":   "studio_yago_speaking_close",
}

# Mapeo speaker -> two-shot cuando la intervencion es larga (dialogo)
TWO_SHOT_CLIPS = {
    "MARIA":  "studio_maria_speaks_yago_listens",
    "IAGO":   "studio_yago_speaks_maria_listens",
    "YAGO":   "studio_yago_speaks_maria_listens",
}


def _has_rich_overlay(scene: dict) -> bool:
    for ov in scene.get("overlays", []):
        if ov.get("type") in RICH_OVERLAY_TYPES:
            return True
    return False


def _pick_studio_clip(scene: dict, library, prefer_close_up_below: float = 8.0) -> str | None:
    """Devuelve la ruta del MP4 de estudio adecuado para la escena, o None."""
    speaker = (scene.get("speaker") or "").upper().replace("Á", "A").replace("Í", "I")
    section = (scene.get("section") or "").upper()
    duration = float(scene.get("end", 0)) - float(scene.get("start", 0))

    # 1) Cierre / despedida -> outro
    if section in ("DESPEDIDA", "CIERRE_FINAL"):
        s = library.find("studio_outro_closing")
        if s:
            return s["path"]

    # 2) Establishing al inicio del primer bloque o tras la sintonia
    if section in ("SALUDO_Y_PRESENTACION", "SALUDO"):
        s = library.find("studio_establishing_general")
        if s:
            return s["path"]

    # 3) Tono complicidad / ironia compartida
    tones = scene.get("tones", []) or []
    if any(t in tones for t in ("ironico", "humor")) and duration < 6:
        s = library.find("studio_both_complicit")
        if s:
            return s["path"]

    # 4) Por defecto: close-up si dura poco, two-shot si dura mucho
    if duration < prefer_close_up_below:
        slug = DEFAULT_STUDIO_CLIPS.get(speaker)
    else:
        slug = TWO_SHOT_CLIPS.get(speaker)

    if slug:
        s = library.find(slug)
        if s:
            return s["path"]

    # Fallback: cualquier toma de estudio que tengamos
    for fallback_slug in ("studio_establishing_general",
                          "studio_yago_speaking_close",
                          "studio_maria_speaking_close"):
        s = library.find(fallback_slug)
        if s:
            return s["path"]
    return None


def build_scene_track(timeline: dict,
                       audio_structure: dict,
                       library,
                       output_folder: str | Path,
                       force: bool = False) -> list[dict]:
    """
    Devuelve lista de "segmentos" que cubren toda la duracion del audio.
    Cada segmento dice si es ESTUDIO, PIZARRA o BLANK y la fuente.
    """
    log = get_logger("scene_track_builder")
    output_folder = Path(output_folder)
    cache = output_folder / "scene_track.json"
    if cache.exists() and not force:
        log.info(f"scene_track cacheado: {cache.name}")
        return json.loads(cache.read_text(encoding="utf-8"))

    track = []
    studio_count = 0
    pizarra_count = 0

    for sc in timeline.get("scenes", []):
        section = (sc.get("section") or "").upper()
        is_pizarra = _has_rich_overlay(sc)

        # HOOK: prefer estudio aunque haya overlay (mostrar al speaker)
        if section == "HOOK":
            is_pizarra = False

        # CIERRE_CONCEPTOS: siempre pizarra (recap_grid)
        if section == "CIERRE_CONCEPTOS":
            is_pizarra = True

        if is_pizarra:
            seg = {
                "type":    "pizarra",
                "start":   float(sc.get("start", 0)),
                "end":     float(sc.get("end", 0)),
                "speaker": sc.get("speaker", ""),
                "section": sc.get("section", ""),
                "scene_idx": timeline["scenes"].index(sc),
            }
            pizarra_count += 1
        else:
            studio_path = _pick_studio_clip(sc, library)
            seg = {
                "type":    "studio",
                "start":   float(sc.get("start", 0)),
                "end":     float(sc.get("end", 0)),
                "speaker": sc.get("speaker", ""),
                "section": sc.get("section", ""),
                "source":  studio_path,
                "scene_idx": timeline["scenes"].index(sc),
            }
            if studio_path:
                studio_count += 1
            else:
                # Sin clip de estudio disponible -> caer a pizarra
                seg["type"] = "pizarra"
                pizarra_count += 1
                log.warning(f"  Sin clip estudio para escena {sc.get('start')}-{sc.get('end')} "
                            f"speaker={sc.get('speaker')}: cae a pizarra")

        track.append(seg)

    # Asegurar cobertura continua [0, audio_duration] con segmentos blank.
    audio_duration = float(audio_structure.get("audio_duration") or
                           (track[-1]["end"] if track else 60.0))
    track.sort(key=lambda s: float(s["start"]))
    filled = []
    cursor = 0.0
    for seg in track:
        s = float(seg["start"])
        if s > cursor + 0.05:
            filled.append({
                "type":    "blank",
                "start":   round(cursor, 3),
                "end":     round(s, 3),
                "speaker": "",
                "section": "GAP",
            })
        filled.append(seg)
        cursor = max(cursor, float(seg["end"]))
    if audio_duration > cursor + 0.05:
        filled.append({
            "type":    "blank",
            "start":   round(cursor, 3),
            "end":     round(audio_duration, 3),
            "speaker": "",
            "section": "TAIL",
        })
    track = filled

    output_folder.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(track, indent=2, ensure_ascii=False), encoding="utf-8")
    blank_count = sum(1 for s in track if s["type"] == "blank")
    log.info(f"scene_track guardado: {len(track)} segmentos "
             f"(estudio={studio_count} · pizarra={pizarra_count} · blanks={blank_count})")
    return track
