"""
Paso 03 - Construccion del scene_timeline.json.

Si hay ANTHROPIC_API_KEY disponible, usa Claude para generar el timeline.
Si no, usa un constructor heuristico que ya genera un timeline funcional.
"""

import json
import os
import random
import re
from pathlib import Path

from .logger import get_logger

POSITIONS_RING = [
    "MID_LEFT", "TOP_LEFT", "TOP_CENTER", "MID_CENTER",
    "BOTTOM_LEFT", "BOTTOM_CENTER", "MID_RIGHT", "TOP_RIGHT",
]

STICKER_TRIGGERS = {
    "nobody_reads_tos":  ["terminos", "condiciones", "letra pequena", "tos"],
    "winter_is_coming":  ["invierno", "winter", "crisis", "burbuja"],
    "linkedin_guru":     ["linkedin", "guru", "influencer", "thought leader"],
    "expensive_mistake": ["error", "fracaso", "perdida", "millones perdidos"],
    "speedrun":          ["velocidad", "rapido", "obsolet", "speedrun"],
    "this_is_fine":      ["esta bien", "todo ok", "everything fine"],
    "lawyer_up":         ["multa", "regulacion", "eu ai act", "abogado", "demanda"],
    "stonks":            ["sueldo", "salario", "crece", "stonks", "subida", "ganancia"],
    "wave_bye":          ["despedida", "hasta la proxima", "adios", "cierre"],
}


def _normalize(s: str) -> str:
    s = s.lower()
    repl = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}
    for k, v in repl.items():
        s = s.replace(k, v)
    return s


def _section_to_words(transcription: dict, search_text: str,
                      offset: int = 0) -> tuple[float, float]:
    """
    Aproxima los timestamps start/end de una porcion de texto buscando
    sus primeras palabras en la transcripcion de Whisper.
    """
    words = transcription.get("words", [])
    if not words:
        return (0.0, 0.0)

    norm_search = _normalize(search_text)
    needle = " ".join(norm_search.split()[:6])

    # Construye un buffer rolante normalizado
    for i in range(offset, len(words)):
        window = " ".join(_normalize(w["word"]) for w in words[i:i + 12])
        if needle and needle[:30] in window:
            return (words[i]["start"], words[min(i + 11, len(words) - 1)]["end"])

    return (0.0, 0.0)


def _build_heuristic_timeline(content: dict, transcription: dict) -> dict:
    """
    Construye scene_timeline.json sin LLM, asignando overlays segun heuristicas:
      - name_tag siempre presente para el speaker activo.
      - stat_card para cada estadistica detectada en orden de aparicion.
      - sticker cuando un trigger aparece en la intervencion.
    """
    log = get_logger("03_scene_builder")
    sections = content.get("sections", [])
    duration = transcription.get("duration_seconds", 0.0) or 0.0
    words = transcription.get("words", [])
    total_words = len(words)

    if total_words == 0 or duration <= 0:
        log.warning("Sin transcripcion utilizable, generando timeline minimo.")
        return {
            "background": "industrial_grid",
            "scenes": [{
                "start": 0.0, "end": max(duration, 60.0), "section": "EPISODIO",
                "speaker": "MARIA", "background": "industrial_grid",
                "overlays": [], "stickers": [],
            }],
        }

    # Mapear cada interview a un rango temporal aproximado.
    flat_interventions = []
    for sec in sections:
        for iv in sec.get("interventions", []):
            flat_interventions.append({
                "section": sec["name"],
                "speaker": iv["speaker"],
                "tones":   iv["tones"],
                "text":    iv["text"],
            })

    if not flat_interventions:
        flat_interventions = [{
            "section": "EPISODIO", "speaker": "MARIA",
            "tones": [], "text": transcription.get("full_text", ""),
        }]

    # Asignar tiempos proporcionalmente al numero de palabras de cada intervencion.
    total_text_words = sum(max(len(iv["text"].split()), 1)
                           for iv in flat_interventions)

    cursor = 0.0
    for iv in flat_interventions:
        share = max(len(iv["text"].split()), 1) / total_text_words
        iv_dur = duration * share
        iv["start"] = round(cursor, 3)
        iv["end"] = round(min(cursor + iv_dur, duration), 3)
        cursor = iv["end"]

    stats = list(content.get("statistics", []))
    stat_idx = 0
    scenes = []

    for idx, iv in enumerate(flat_interventions):
        speaker = iv["speaker"].upper()
        speaker_color = "#F5C400" if speaker == "MARIA" else "#4DB8FF"

        overlays = [{
            "type":     "name_tag",
            "position": "TOP_RIGHT",
            "data":     {"name": speaker, "color": speaker_color},
            "start":    iv["start"],
            "end":      iv["end"],
        }]

        # Indicador de seccion en TOP_LEFT al cambiar de seccion
        if idx == 0 or flat_interventions[idx - 1]["section"] != iv["section"]:
            overlays.append({
                "type":     "section_indicator",
                "position": "TOP_LEFT",
                "data":     {"label": iv["section"].replace("_", " ").title()},
                "start":    iv["start"],
                "end":      min(iv["start"] + 4.0, iv["end"]),
            })

        # Repartir hasta 2 stat_cards de la lista global de stats
        chunk_stats = stats[stat_idx:stat_idx + 2]
        for j, st in enumerate(chunk_stats):
            pos = POSITIONS_RING[(idx + j) % len(POSITIONS_RING)]
            if pos == "BOTTOM_RIGHT_SAFE":
                pos = "MID_LEFT"
            overlays.append({
                "type":     "stat_card",
                "position": pos,
                "data":     {
                    "label":    st.get("type", "dato").upper(),
                    "value":    st.get("value", ""),
                    "subtitle": "",
                },
                "start": round(min(iv["start"] + 1.0 + j * 1.5, iv["end"] - 0.5), 3),
                "end":   round(min(iv["start"] + 5.0 + j * 1.5, iv["end"]), 3),
            })
        stat_idx += len(chunk_stats)

        # Stickers segun triggers
        stickers = []
        text_norm = _normalize(iv["text"])
        for stk, triggers in STICKER_TRIGGERS.items():
            if any(t in text_norm for t in triggers):
                stickers.append({
                    "name":     stk,
                    "position": "BOTTOM_LEFT" if speaker == "MARIA" else "BOTTOM_CENTER",
                    "start":    round(min(iv["start"] + 1.5, iv["end"] - 0.3), 3),
                    "end":      round(min(iv["start"] + 4.0, iv["end"]), 3),
                })
                break  # un sticker max por intervencion

        bg = "industrial_grid"
        if "regulacion" in iv["section"].lower() or "alerta" in text_norm:
            bg = "circuit_board"
        elif iv["section"].startswith("CIERRE") or iv["section"].startswith("DESPEDIDA"):
            bg = "data_diagonal"

        scenes.append({
            "start":      iv["start"],
            "end":        iv["end"],
            "section":    iv["section"],
            "speaker":    speaker,
            "background": bg,
            "overlays":   overlays,
            "stickers":   stickers,
        })

    return {"background": "industrial_grid", "scenes": scenes}


def _try_anthropic_timeline(content: dict, transcription: dict,
                             prompt_path: Path) -> dict | None:
    """Intenta usar Claude para generar el timeline. None si no hay API key."""
    log = get_logger("03_scene_builder")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.info("ANTHROPIC_API_KEY no definida, usando builder heuristico.")
        return None

    try:
        import anthropic
    except ImportError:
        log.warning("Paquete 'anthropic' no instalado, usando builder heuristico.")
        return None

    system_prompt = prompt_path.read_text(encoding="utf-8")

    payload = {
        "duration_seconds": transcription.get("duration_seconds", 0),
        "sections":         [{
            "name": s["name"],
            "speakers": [iv["speaker"] for iv in s["interventions"]],
            "tones":    list({t for iv in s["interventions"] for t in iv["tones"]}),
            "text":     " ".join(iv["text"] for iv in s["interventions"])[:1500],
        } for s in content.get("sections", [])],
        "statistics": content.get("statistics", [])[:60],
        "concepts":   content.get("concepts", [])[:30],
        "speakers":   content.get("speakers", []),
    }

    client = anthropic.Anthropic(api_key=api_key)
    log.info("Solicitando scene_timeline a Claude...")

    try:
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": (
                    "Datos del episodio (JSON):\n"
                    + json.dumps(payload, ensure_ascii=False)
                    + "\n\nDevuelve EXCLUSIVAMENTE el JSON de scene_timeline."
                ),
            }],
        )
    except Exception as exc:
        log.warning(f"Error llamando a Anthropic: {exc}. Fallback a heuristico.")
        return None

    try:
        text = msg.content[0].text if msg.content else ""
    except Exception:
        text = str(msg)

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        log.warning(f"JSON invalido del LLM: {exc}. Fallback a heuristico.")
        return None

    if not isinstance(parsed, dict) or "scenes" not in parsed:
        log.warning("Respuesta del LLM sin claves esperadas. Fallback a heuristico.")
        return None

    log.info(f"Timeline LLM: {len(parsed.get('scenes', []))} escenas.")
    return parsed


def build_scene_timeline(content: dict, transcription: dict,
                         output_folder: str | Path,
                         prompt_path: str | Path | None = None,
                         force: bool = False,
                         use_llm: bool = True) -> dict:
    """
    Genera scene_timeline.json combinando datos del guion + transcripcion.
    """
    log = get_logger("03_scene_builder")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    cache = output_folder / "scene_timeline.json"

    if cache.exists() and not force:
        log.info(f"scene_timeline cacheado: {cache.name}")
        return json.loads(cache.read_text(encoding="utf-8"))

    if prompt_path is None:
        prompt_path = Path(__file__).parent.parent / "templates" / "system_prompt_timeline.txt"
    prompt_path = Path(prompt_path)

    timeline = None
    if use_llm and prompt_path.exists():
        timeline = _try_anthropic_timeline(content, transcription, prompt_path)

    if timeline is None:
        log.info("Generando timeline heuristico.")
        timeline = _build_heuristic_timeline(content, transcription)

    cache.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"scene_timeline guardado: {len(timeline.get('scenes', []))} escenas.")
    return timeline


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True)
    parser.add_argument("--transcription", required=True)
    parser.add_argument("--out", default="./outputs")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    content = json.loads(Path(args.content).read_text(encoding="utf-8"))
    transcription = json.loads(Path(args.transcription).read_text(encoding="utf-8"))
    build_scene_timeline(content, transcription, args.out,
                         force=args.force, use_llm=not args.no_llm)
