#!/usr/bin/env python3
"""
MaquinarIA Pesada - Orquestador principal del pipeline.

Uso:
    python run_pipeline.py                  # render completo a la resolucion configurada
    python run_pipeline.py --preview        # primer minuto a 720p, render rapido
    python run_pipeline.py --from-step 4    # reanudar desde el paso 4
    python run_pipeline.py --force          # ignorar caches y rehacer todos los pasos
    python run_pipeline.py --no-llm         # forzar el builder heuristico (sin Anthropic)

Cada paso guarda un checkpoint en outputs/. Si un paso ya tiene su
output cacheado, se omite (salvo --force).
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

# Cargar .env (busca en pipeline_dir, padre y abuelos)
try:
    from dotenv import load_dotenv
    for candidate in [ROOT / ".env", ROOT.parent / ".env", ROOT.parent.parent / ".env"]:
        if candidate.exists():
            load_dotenv(candidate)
            break
except ImportError:
    pass

from pipeline.logger import get_logger
from pipeline.asset_validator import validate_project_config
from pipeline.transcriber import transcribe_episode
from pipeline.content_extractor import extract_content
from pipeline.scene_builder import build_scene_timeline
from pipeline.overlay_renderer import render_frames
from pipeline.subtitle_generator import generate_srt
from pipeline.video_compositor import compose_video
from pipeline.metadata_generator import generate_metadata


def _intro_duration(intro_path: str | None) -> float:
    if not intro_path or not Path(intro_path).exists():
        return 0.0
    if shutil.which("ffprobe") is None:
        return 0.0
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", intro_path,
        ], text=True).strip()
        return float(out)
    except Exception:
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="MaquinarIA Pesada - Pipeline de videopodcast")
    parser.add_argument("--preview", action="store_true",
                        help="Render rapido del primer minuto a 720p")
    parser.add_argument("--preview-seconds", type=float, default=60.0)
    parser.add_argument("--from-step", type=int, default=1,
                        help="Reanudar desde un paso (1..7)")
    parser.add_argument("--force", action="store_true",
                        help="Ignorar caches en TODOS los pasos")
    parser.add_argument("--no-llm", action="store_true",
                        help="No usar LLM (heuristico) en el paso 3")
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
    log.info(f"  MAQUINARIA PESADA - PIPELINE START · {episode_id}")
    log.info(f"  preview={args.preview} · from-step={args.from_step} · force={args.force}")
    log.info("=" * 60)

    transcription = None
    content = None
    timeline = None
    frames_index = None
    srt_path = None
    final_video = None

    try:
        # PASO 1 - Transcripcion
        if args.from_step <= 1:
            log.info("[1/7] Transcripcion con Whisper...")
            transcription = transcribe_episode(
                config["assets"]["episode_audio"],
                output_folder,
                model_size="tiny" if args.preview else args.whisper_model,
                force=args.force,
            )
        else:
            transcription = json.loads((output_folder / "transcription_raw.json").read_text(encoding="utf-8"))

        # PASO 2 - Extraccion de contenido
        if args.from_step <= 2:
            log.info("[2/7] Extraccion de contenido del guion + PDF...")
            content = extract_content(
                config["assets"]["episode_script"],
                config["assets"].get("episode_pdf"),
                output_folder,
                force=args.force,
            )
        else:
            content = json.loads((output_folder / "content_data.json").read_text(encoding="utf-8"))

        # PASO 3 - Scene timeline
        if args.from_step <= 3:
            log.info("[3/7] Construccion de scene_timeline...")
            timeline = build_scene_timeline(
                content, transcription, output_folder,
                force=args.force, use_llm=not args.no_llm,
            )
        else:
            timeline = json.loads((output_folder / "scene_timeline.json").read_text(encoding="utf-8"))

        # PASO 4 - Render de overlays
        if args.from_step <= 4:
            log.info("[4/7] Render de overlays a frames PNG...")
            frames_index = render_frames(
                timeline, transcription, config, output_folder,
                preview_seconds=args.preview_seconds if args.preview else None,
                force=args.force,
            )
        else:
            frames_index = json.loads((output_folder / "frames_index.json").read_text(encoding="utf-8"))

        # PASO 5 - Subtitulos
        if args.from_step <= 5:
            log.info("[5/7] Generacion de subtitulos SRT...")
            srt_path = generate_srt(
                transcription, content, output_folder, episode_id, force=args.force,
            )
        else:
            srt_path = str(output_folder / f"{episode_id}_subtitulos.srt")

        # PASO 6 - Composicion FFMPEG
        if args.from_step <= 6:
            log.info("[6/7] Composicion final con ffmpeg...")
            final_video = compose_video(
                config, frames_index,
                config["assets"]["episode_audio"], srt_path,
                output_folder, episode_id, preview=args.preview,
            )

        # PASO 7 - Metadata
        if args.from_step <= 7 and not args.preview:
            log.info("[7/7] Metadata YouTube + thumbnail...")
            generate_metadata(
                config, content, transcription, output_folder, episode_id,
                intro_duration=_intro_duration(config["assets"].get("intro_video")),
            )

        log.info("=" * 60)
        log.info("  PIPELINE COMPLETADO CORRECTAMENTE")
        log.info(f"  Video: {final_video}")
        log.info(f"  Logs:  {log_path}")
        log.info("=" * 60)
        return 0

    except KeyboardInterrupt:
        log.error("Interrumpido por el usuario.")
        return 130
    except Exception as exc:
        log.exception(f"Pipeline fallido: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
