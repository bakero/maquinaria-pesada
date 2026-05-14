#!/usr/bin/env python3
"""
MaquinarIA Pesada - Orquestador principal del pipeline (v2.1).

Orden de pasos:
  1. Whisper -> transcription_raw.json
  2. Content extractor (guion + PDF) -> content_data.json
  3. Audio analyzer (silencios, hook, sintonia) -> audio_structure.json
  4. Align interventions (guion <-> Whisper) -> aligned_interventions.json
  5. Scene builder (LLM o heuristico) -> scene_timeline.json
  6. Overlay renderer -> frames PNG
  7. Subtitle generator (desde guion) -> *.srt
  8. Video compositor (intro_video como overlay sobre sintonia) -> *.mp4
  9. Metadata (chapters + thumbnail) -> *.json + *.jpg

CLI:
  python run_pipeline.py                  # render completo
  python run_pipeline.py --preview        # primer minuto a 720p
  python run_pipeline.py --from-step 5    # reanudar desde paso 5
  python run_pipeline.py --force          # ignorar caches
  python run_pipeline.py --no-llm         # forzar heuristico (sin Anthropic)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

# Cargar .env. Buscamos en orden de prioridad:
#   1) raiz REAL del proyecto (<repo>/.env, un nivel por encima de ROOT)
#   2) cualquier .env en ROOT o ancestros
try:
    from dotenv import find_dotenv, load_dotenv
    PROJECT_ROOT_ENV = ROOT.parent / ".env"
    if PROJECT_ROOT_ENV.exists():
        load_dotenv(str(PROJECT_ROOT_ENV), override=True)
    else:
        found = find_dotenv(filename=".env", usecwd=True)
        if found:
            load_dotenv(found, override=True)
except ImportError:
    pass

from pipeline.asset_validator import validate_project_config
from pipeline.audio_analyzer import analyze_episode_audio
from pipeline.content_extractor import extract_content
from pipeline.logger import get_logger
from pipeline.metadata_generator import generate_metadata
from pipeline.overlay_renderer import render_frames
from pipeline.scene_builder import build_scene_timeline
from pipeline.scene_library import SceneLibrary
from pipeline.scene_track_builder import build_scene_track
from pipeline.subtitle_generator import (
    _align_interventions_with_whisper,
    _flatten_interventions,
    generate_srt,
)
from pipeline.transcriber import transcribe_episode
from pipeline.video_compositor import compose_video, derive_video_basename


def _load_or_compute(path: Path, compute, *args, **kwargs):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return compute(*args, **kwargs)


def _enrich_timeline_with_interventions(timeline: dict,
                                         aligned: list[dict],
                                         audio_structure: dict | None = None) -> dict:
    """
    Anyade el campo `text` a cada escena del timeline buscando la intervencion
    cuyo rango temporal contiene el centro de la escena.

    Tambien GARANTIZA que existen escenas para las intervenciones del HOOK
    (que el LLM puede haber saltado).
    """
    scenes = timeline.get("scenes", [])
    audio_structure = audio_structure or {}

    # Mapear cada escena con su intervencion correspondiente (por overlap temporal)
    for sc in scenes:
        sc_mid = (float(sc.get("start", 0)) + float(sc.get("end", 0))) / 2
        best = None
        best_overlap = 0.0
        for iv in aligned:
            iv_s, iv_e = float(iv.get("start", 0)), float(iv.get("end", 0))
            if iv_s <= sc_mid <= iv_e:
                best = iv
                break
            # Si no contiene el centro, calcular overlap maximo
            ov = max(0, min(iv_e, float(sc["end"])) - max(iv_s, float(sc["start"])))
            if ov > best_overlap:
                best_overlap = ov
                best = iv
        if best:
            sc["text"] = best.get("text", "")
            if not sc.get("speaker"):
                sc["speaker"] = best.get("speaker", "")
            if not sc.get("section"):
                sc["section"] = best.get("section", "")

    # Anyadir escenas faltantes para HOOK + cualquier intervencion no cubierta
    covered_ranges = [(float(sc["start"]), float(sc["end"])) for sc in scenes]

    def _is_covered(start: float, end: float) -> bool:
        mid = (start + end) / 2
        return any(s <= mid <= e for s, e in covered_ranges)

    for iv in aligned:
        iv_s, iv_e = float(iv.get("start", 0)), float(iv.get("end", 0))
        if iv_e <= iv_s:
            continue
        if _is_covered(iv_s, iv_e):
            continue
        speaker = iv.get("speaker", "")
        speaker_color = "#F5C400" if speaker.upper() == "MARIA" else "#4DB8FF"
        new_scene = {
            "start":      round(iv_s, 3),
            "end":        round(iv_e, 3),
            "section":    iv.get("section", ""),
            "speaker":    speaker.upper(),
            "background": "industrial_grid",
            "text":       iv.get("text", ""),
            "overlays": [{
                "type":     "name_tag",
                "position": "TOP_RIGHT",
                "data":     {"name": speaker.upper(), "color": speaker_color},
                "start":    round(iv_s, 3),
                "end":      round(iv_e, 3),
            }],
            "stickers":   [],
            "_added_by":  "enrich",
        }
        scenes.append(new_scene)

    scenes.sort(key=lambda x: float(x.get("start", 0)))
    timeline["scenes"] = scenes
    return timeline


def main() -> int:
    parser = argparse.ArgumentParser(description="MaquinarIA Pesada - Pipeline videopodcast")
    parser.add_argument("--preview", action="store_true",
                        help="Render rapido a 720p (primer minuto por defecto)")
    parser.add_argument("--preview-seconds", type=float, default=60.0)
    parser.add_argument("--from-step", type=int, default=1,
                        help="Reanudar desde un paso (1..9)")
    parser.add_argument("--force", action="store_true",
                        help="Ignorar caches en TODOS los pasos")
    parser.add_argument("--no-llm", action="store_true",
                        help="No usar LLM en el paso 5 (heuristico)")
    parser.add_argument("--whisper-model", default="large-v3",
                        choices=["tiny", "base", "small", "medium", "large-v3"])
    parser.add_argument("--config", default="project_config.json")
    args = parser.parse_args()

    config = validate_project_config(ROOT / args.config)
    episode_id = config["episode_defaults"].get("episode_id", "EP-MOD000")
    output_folder = Path(config["assets"]["output_folder"])
    log_path = output_folder / "logs" / f"{episode_id}_pipeline.log"
    log = get_logger("run_pipeline", log_file=log_path)

    log.info("=" * 60)
    log.info(f"  MAQUINARIA PESADA - PIPELINE v2.1 - {episode_id}")
    log.info(f"  preview={args.preview} from-step={args.from_step} force={args.force}")
    log.info("=" * 60)

    transcription = content = audio_structure = aligned = None
    timeline = frames_index = srt_path = final_video = None

    try:
        # ─── 1. Whisper ────────────────────────────────────────────
        if args.from_step <= 1:
            log.info("[1/9] Transcripcion con Whisper...")
            transcription = transcribe_episode(
                config["assets"]["episode_audio"],
                output_folder,
                model_size="medium" if args.preview else args.whisper_model,
                force=args.force,
            )
        else:
            transcription = json.loads((output_folder / "transcription_raw.json").read_text(encoding="utf-8"))

        # ─── 2. Content extractor ──────────────────────────────────
        if args.from_step <= 2:
            log.info("[2/9] Extraccion de contenido (guion + PDF)...")
            content = extract_content(
                config["assets"]["episode_script"],
                config["assets"].get("episode_pdf"),
                output_folder,
                force=args.force,
            )
        else:
            content = json.loads((output_folder / "content_data.json").read_text(encoding="utf-8"))

        # ─── 3. Audio analyzer ─────────────────────────────────────
        if args.from_step <= 3:
            log.info("[3/9] Analisis estructural del audio...")
            audio_structure = analyze_episode_audio(
                config["assets"]["episode_audio"],
                config["assets"].get("intro_video"),
                output_folder,
                force=args.force,
            )
        else:
            audio_structure = json.loads((output_folder / "audio_structure.json").read_text(encoding="utf-8"))

        # ─── 4. Alineamiento guion ↔ Whisper ──────────────────────
        aligned_path = output_folder / "aligned_interventions.json"
        if args.from_step <= 4 or not aligned_path.exists():
            log.info("[4/9] Alineamiento guion <-> Whisper...")
            interventions_clean = _flatten_interventions(content)
            aligned = _align_interventions_with_whisper(
                interventions_clean,
                transcription.get("words", []),
                content_start=audio_structure.get("content_start") or 0.0,
                content_end=audio_structure.get("content_end"),
                audio_structure=audio_structure,
            )
            aligned_path.write_text(json.dumps(aligned, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
        else:
            aligned = json.loads(aligned_path.read_text(encoding="utf-8"))

        # ─── 5. Scene timeline ─────────────────────────────────────
        if args.from_step <= 5:
            log.info("[5/9] Construccion de scene_timeline (con LLM si hay saldo)...")
            timeline = build_scene_timeline(
                content, transcription, output_folder,
                force=args.force, use_llm=not args.no_llm,
                audio_structure=audio_structure,
                pdf_text=content.get("pdf_text", ""),
                aligned_interventions=aligned,
            )
        else:
            timeline = json.loads((output_folder / "scene_timeline.json").read_text(encoding="utf-8"))

        # ─── 5b. Enriquecer timeline con textos + escenas HOOK ────
        log.info("[5b] Enriqueciendo timeline con texto de intervenciones...")
        timeline = _enrich_timeline_with_interventions(timeline, aligned, audio_structure)

        # ─── 6. Render de overlays ────────────────────────────────
        if args.from_step <= 6:
            log.info("[6/9] Render de overlays a frames PNG...")
            preview_secs = args.preview_seconds if args.preview else None
            frames_index = render_frames(
                timeline, transcription, config, output_folder,
                preview_seconds=preview_secs, force=args.force,
            )
        else:
            frames_index = json.loads((output_folder / "frames_index.json").read_text(encoding="utf-8"))

        # ─── 7. Subtitulos ────────────────────────────────────────
        videos_folder_cfg = config["assets"].get("videos_folder")
        base_name = derive_video_basename(
            config["assets"].get("episode_audio"), episode_id,
        )
        if args.from_step <= 7:
            log.info("[7/9] Generacion de SRT desde guion limpio...")
            srt_path = generate_srt(
                transcription, content, output_folder, episode_id,
                force=args.force, videos_folder=videos_folder_cfg,
                base_name=base_name, audio_structure=audio_structure,
            )
        else:
            srt_dir = Path(videos_folder_cfg) if videos_folder_cfg else output_folder
            srt_path = str(srt_dir / f"{base_name}.srt")

        # ─── 7b. Construccion del scene_track (alterna estudio/pizarra) ──
        log.info("[7b] Construccion del scene_track (estudio vs pizarra)...")
        videos_folder_cfg2 = config["assets"].get("videos_folder")
        library_base = (Path(videos_folder_cfg2) / "escenas_biblioteca"
                        if videos_folder_cfg2 else output_folder / "escenas_biblioteca")
        scene_track = None
        try:
            library = SceneLibrary(library_base)
            scene_track = build_scene_track(
                timeline, audio_structure, library, output_folder,
                force=args.force,
            )
        except Exception as exc:
            log.warning(f"  scene_track no disponible: {exc}. Modo legacy (todo pizarra).")

        # ─── 8. Composicion final ─────────────────────────────────
        if args.from_step <= 8:
            log.info("[8/9] Composicion final con ffmpeg...")
            final_video = compose_video(
                config, frames_index,
                config["assets"]["episode_audio"], srt_path,
                output_folder, episode_id, preview=args.preview,
                audio_structure=audio_structure,
                scene_track=scene_track,
            )

        # ─── 9. Metadata ──────────────────────────────────────────
        if args.from_step <= 9 and not args.preview:
            log.info("[9/9] Metadata YouTube + thumbnail...")
            generate_metadata(
                config, content, transcription, output_folder, episode_id,
                intro_duration=audio_structure.get("sintonia_end", 0) or 0,
                base_name=base_name,
            )

        log.info("=" * 60)
        log.info("  PIPELINE COMPLETADO")
        log.info(f"  Video: {final_video}")
        log.info("=" * 60)
        return 0

    except KeyboardInterrupt:
        log.error("Interrumpido por el usuario.")
        return 130
    except Exception as exc:
        log.exception(f"Pipeline fallido: {exc}")
        return 1


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
        raise SystemExit(main())
