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


def _build_heuristic_timeline(content: dict, transcription: dict,
                               audio_structure: dict | None = None,
                               aligned_interventions: list[dict] | None = None) -> dict:
    """
    Builder heuristico V2 - usa el guion ALINEADO con timestamps del audio
    para colocar overlays relevantes al contenido de cada intervencion.

    Reglas (ordenadas por prioridad):
      1. name_tag SIEMPRE en TOP_RIGHT con color del speaker activo.
      2. section_indicator en TOP_LEFT durante 4s en el cambio de seccion.
      3. Si la intervencion contiene una cifra concreta -> stat_card MID_LEFT.
      4. Si menciona IA/ML/DL/LLM en la misma frase -> hierarchy_diagram MID_RIGHT.
      5. Si menciona comparacion (vs, frente a, sistema 1/2) -> two_column_compare BOTTOM_FULL_WIDTH.
      6. Si menciona anio/historia/inviernos -> timeline_visual BOTTOM_FULL_WIDTH.
      7. Si menciona regulacion/EU AI Act/multa -> regulation_alert MID_CENTER.
      8. CIERRE_CONCEPTOS -> recap_grid con conceptos clave del episodio.
      9. Sticker segun trigger del texto (max 1 por intervencion).
    """
    log = get_logger("03_scene_builder")
    duration = transcription.get("duration_seconds", 0.0) or 0.0

    # Si tenemos aligned_interventions con timestamps reales, usarlos.
    if aligned_interventions:
        ivs = aligned_interventions
    else:
        # Fallback: distribuir proporcionalmente
        ivs = []
        for sec in content.get("sections", []):
            for iv in sec.get("interventions", []):
                ivs.append({
                    "section": sec["name"], "speaker": iv["speaker"],
                    "tones": iv.get("tones", []), "text": iv.get("text", ""),
                })
        total_words = sum(max(len(i["text"].split()), 1) for i in ivs) or 1
        cursor = 0.0
        for iv in ivs:
            share = max(len(iv["text"].split()), 1) / total_words
            iv_dur = duration * share
            iv["start"] = round(cursor, 3)
            iv["end"] = round(cursor + iv_dur, 3)
            cursor = iv["end"]

    if not ivs:
        return {"background": "industrial_grid",
                "scenes": [{"start": 0.0, "end": max(duration, 60.0),
                            "section": "EPISODIO", "speaker": "MARIA",
                            "background": "industrial_grid",
                            "overlays": [], "stickers": []}]}

    keywords = content.get("keywords", [])
    concepts = content.get("concepts", [])

    scenes = []
    for idx, iv in enumerate(ivs):
        speaker = iv["speaker"].upper()
        speaker_color = "#F5C400" if speaker == "MARIA" else "#4DB8FF"
        text = iv["text"]
        text_norm = _normalize(text)
        section = iv.get("section", "")

        # name_tag SIEMPRE
        overlays = [{
            "type": "name_tag", "position": "TOP_RIGHT",
            "data": {"name": speaker, "color": speaker_color},
            "start": iv["start"], "end": iv["end"],
        }]

        # section_indicator al cambiar
        prev_section = ivs[idx - 1].get("section") if idx > 0 else None
        if section and section != prev_section:
            overlays.append({
                "type": "section_indicator", "position": "TOP_LEFT",
                "data": {"label": section.replace("_", " ").title()},
                "start": iv["start"],
                "end": round(min(iv["start"] + 4.0, iv["end"]), 3),
            })

        # 1) Cifra concreta -> stat_card
        m_pct = re.search(r"\b(\d{1,3}(?:[.,]\d+)?\s*%)", text)
        m_money = re.search(
            r"(\$|€|EUR|USD)?\s*\d{1,3}(?:[.,]\d{1,3})*\s*(B|M|K|millones|billones|mil)\b",
            text, re.IGNORECASE)
        m_users = re.search(
            r"\b\d{1,3}(?:[.,]\d+)?\s*(M|millones|mil|billones)\s*(usuarios?|empresas?|users?)\b",
            text, re.IGNORECASE)
        m_year = re.search(r"\b(19[7-9]\d|20[0-3]\d)\b", text)

        if m_pct:
            label = "DATO"
            sub = ""
            if "empresa" in text_norm: sub = "empresas"
            elif "usuario" in text_norm: sub = "usuarios"
            elif "adopcion" in text_norm: label = "ADOPCION"
            overlays.append({
                "type": "stat_card", "position": "MID_LEFT",
                "data": {"label": label, "value": m_pct.group(1).strip(),
                         "subtitle": sub, "color": speaker_color},
                "start": round(iv["start"] + 0.6, 3),
                "end": round(min(iv["start"] + 5.5, iv["end"]), 3),
            })
        elif m_money:
            overlays.append({
                "type": "stat_card", "position": "MID_LEFT",
                "data": {"label": "VOLUMEN", "value": m_money.group(0).strip(),
                         "subtitle": "", "color": speaker_color},
                "start": round(iv["start"] + 0.6, 3),
                "end": round(min(iv["start"] + 5.5, iv["end"]), 3),
            })
        elif m_users:
            overlays.append({
                "type": "stat_card", "position": "MID_LEFT",
                "data": {"label": "ESCALA", "value": m_users.group(0).strip(),
                         "subtitle": "", "color": speaker_color},
                "start": round(iv["start"] + 0.6, 3),
                "end": round(min(iv["start"] + 5.5, iv["end"]), 3),
            })

        # 2) Conceptos jerarquicos: IA / ML / DL / LLM
        if re.search(r"\b(I\.?A\.?|inteligencia artificial)\b.*\b(machine learning|ML|deep learning|DL|LLM)\b",
                     text, re.IGNORECASE | re.DOTALL):
            items = []
            for label, pat in [("IA", r"inteligencia artificial|I\.?A\.?"),
                               ("ML", r"machine learning|ML"),
                               ("DL", r"deep learning|DL"),
                               ("LLMs", r"LLM")]:
                if re.search(pat, text, re.IGNORECASE):
                    items.append(label)
            if len(items) >= 2:
                overlays.append({
                    "type": "hierarchy_diagram", "position": "MID_RIGHT",
                    "data": {"title": "Taxonomia IA", "items": items},
                    "start": round(iv["start"] + 1.0, 3),
                    "end": round(min(iv["start"] + 7.0, iv["end"]), 3),
                })

        # 3) Inviernos / cronologia
        if "invierno" in text_norm and ("70" in text or "90" in text or "80" in text):
            overlays.append({
                "type": "timeline_visual", "position": "BOTTOM_FULL_WIDTH",
                "data": {"items": [
                    {"year": "1970s", "label": "1er invierno"},
                    {"year": "1990s", "label": "2do invierno"},
                    {"year": "2017",  "label": "Transformers"},
                    {"year": "2026",  "label": "Hoy"},
                ]},
                "start": round(iv["start"] + 1.0, 3),
                "end": round(min(iv["start"] + 8.0, iv["end"]), 3),
            })

        # 4) Regulacion / EU AI Act / multas
        if any(k in text_norm for k in ["eu ai act", "regulacion", "multa", "abogado",
                                          "compliance", "rgpd", "gdpr"]):
            overlays.append({
                "type": "regulation_alert", "position": "MID_CENTER",
                "data": {"title": "EU AI ACT",
                         "text": "Riesgo · Compliance · Multas"},
                "start": round(iv["start"] + 0.8, 3),
                "end": round(min(iv["start"] + 5.5, iv["end"]), 3),
            })

        # 5) Comparaciones / dualidades
        if (" vs " in text_norm or "frente a" in text_norm
                or "sistema 1" in text_norm or "simbolica" in text_norm):
            # Fallback genérico
            overlays.append({
                "type": "two_column_compare", "position": "BOTTOM_FULL_WIDTH",
                "data": {
                    "left_title":  "ANTES" if "antes" in text_norm else "OPCION A",
                    "right_title": "AHORA" if "ahora" in text_norm else "OPCION B",
                    "left_items":  [],
                    "right_items": [],
                },
                "start": round(iv["start"] + 1.0, 3),
                "end": round(min(iv["start"] + 6.0, iv["end"]), 3),
            })

        # 6) CIERRE_CONCEPTOS -> recap_grid
        if section in ("CIERRE_CONCEPTOS", "CIERRE_FINAL"):
            top_concepts = [c for c in concepts if len(c) > 2][:8] or keywords[:8]
            overlays.append({
                "type": "recap_grid", "position": "MID_CENTER",
                "data": {"items": top_concepts},
                "start": iv["start"], "end": iv["end"],
            })

        # 7) Cita destacable: si la intervencion es corta y punzante (<= 25 palabras)
        #    y tiene tono [serio]/[firme]/[directo], muestra como highlight_quote
        n_words = len(text.split())
        tones = iv.get("tones", []) or []
        if n_words <= 28 and any(t in tones for t in ["serio", "firme", "directo", "tenso", "grave"]):
            quote = text.strip().rstrip(".")[:120]
            overlays.append({
                "type": "highlight_quote", "position": "MID_CENTER",
                "data": {"text": quote, "author": speaker},
                "start": round(iv["start"] + 0.5, 3),
                "end": round(min(iv["start"] + 6.0, iv["end"]), 3),
            })

        # Sticker (max 1)
        stickers = []
        for stk, triggers in STICKER_TRIGGERS.items():
            if any(t in text_norm for t in triggers):
                stickers.append({
                    "name": stk,
                    "position": "BOTTOM_LEFT" if speaker == "MARIA" else "BOTTOM_CENTER",
                    "start": round(iv["start"] + 1.5, 3),
                    "end": round(min(iv["start"] + 4.5, iv["end"]), 3),
                })
                break

        # Background segun seccion / contenido
        bg = "industrial_grid"
        if "regulacion" in section.lower() or "lawyer" in str(stickers):
            bg = "circuit_board"
        elif section.startswith("CIERRE") or section.startswith("DESPEDIDA"):
            bg = "data_diagonal"

        scenes.append({
            "start": iv["start"], "end": iv["end"], "section": section,
            "speaker": speaker, "background": bg,
            "overlays": overlays, "stickers": stickers,
        })

    log.info(f"Builder heuristico V2: {len(scenes)} escenas, "
             f"{sum(len(s['overlays']) for s in scenes)} overlays totales.")
    return {"background": "industrial_grid", "scenes": scenes}


def _try_anthropic_timeline(content: dict, transcription: dict,
                             prompt_path: Path,
                             audio_structure: dict | None = None,
                             pdf_text: str | None = None,
                             aligned_interventions: list[dict] | None = None) -> dict | None:
    """Intenta usar Claude para generar el timeline. None si no hay API key/saldo."""
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

    # Si tenemos intervenciones ya alineadas con timestamps, las pasamos completas.
    if aligned_interventions:
        intervenciones = [{
            "section":     iv.get("section"),
            "speaker":     iv.get("speaker"),
            "tones":       iv.get("tones", []),
            "text":        iv.get("text", "")[:600],
            "start_audio": iv.get("start"),
            "end_audio":   iv.get("end"),
        } for iv in aligned_interventions]
    else:
        intervenciones = []
        for s in content.get("sections", []):
            for iv in s.get("interventions", []):
                intervenciones.append({
                    "section": s["name"],
                    "speaker": iv["speaker"],
                    "tones":   iv.get("tones", []),
                    "text":    iv.get("text", "")[:600],
                })

    payload = {
        "audio_structure":  {k: v for k, v in (audio_structure or {}).items()
                              if k != "silences"},
        "speakers":         content.get("speakers", []),
        "statistics":       content.get("statistics", [])[:80],
        "concepts":         content.get("concepts", [])[:30],
        "keywords":         content.get("keywords", [])[:50],
        "pdf_summary":      (pdf_text or "")[:6000],
        "interventions":    intervenciones,
    }

    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    log.info(f"Solicitando scene_timeline a Claude ({model})...")

    import time as _t
    _t0 = _t.monotonic()
    try:
        msg = client.messages.create(
            model=model,
            max_tokens=12000,
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
        from cockpit.core.usage_tracker import track_anthropic
        track_anthropic(msg, model=model, source="pipeline.scene_builder",
                        kind="generation", latency_ms=int((_t.monotonic() - _t0) * 1000))
    except ImportError:
        pass

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
                         use_llm: bool = True,
                         audio_structure: dict | None = None,
                         pdf_text: str | None = None,
                         aligned_interventions: list[dict] | None = None) -> dict:
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
        timeline = _try_anthropic_timeline(
            content, transcription, prompt_path,
            audio_structure=audio_structure,
            pdf_text=pdf_text,
            aligned_interventions=aligned_interventions,
        )

    if timeline is None:
        log.info("Generando timeline heuristico V2 (con guion alineado).")
        timeline = _build_heuristic_timeline(
            content, transcription,
            audio_structure=audio_structure,
            aligned_interventions=aligned_interventions,
        )

    cache.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"scene_timeline guardado: {len(timeline.get('scenes', []))} escenas.")
    return timeline


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Localiza daylog.py subiendo
    # directorios; si fallara, el script sigue con un nullcontext de respaldo.
    import sys as _sys
    from pathlib import Path as _Path
    for _p in _Path(__file__).resolve().parents:
        if (_p / "daylog.py").exists():
            if str(_p) not in _sys.path:
                _sys.path.insert(0, str(_p))
            break
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script=_Path(__file__).name, params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
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
