#!/usr/bin/env python3
"""
Renderiza un episodio completo a partir de su escaleta de produccion.

Flujo:
  1. Parsea escaletas/<EP>_escaleta.md
  2. Convierte a scene_timeline.json + scene_track.json
  3. Lanza el pipeline normal desde el paso 6 (overlay_renderer) usando
     esos archivos como verdad. NO regenera scene_timeline con LLM.

Uso:
    python tools/render_from_escaleta.py --episode EP-MOD000
    python tools/render_from_escaleta.py --episode EP-MOD000 --preview --preview-seconds 90
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(r"C:\Users\Asus\maquinaria_pesada\.env", override=True)

from pipeline.logger import get_logger
from pipeline.asset_validator import validate_project_config
from pipeline.transcriber import transcribe_episode
from pipeline.content_extractor import extract_content
from pipeline.audio_analyzer import analyze_episode_audio
from pipeline.subtitle_generator import generate_srt
from pipeline.overlay_renderer import render_frames
from pipeline.video_compositor import compose_video, derive_video_basename
from pipeline.metadata_generator import generate_metadata
from pipeline.scene_library import SceneLibrary

from pipeline.escaleta_parser import parse_escaleta
from pipeline.escaleta_to_pipeline import write_pipeline_files


PROJECT_ROOT = Path(r"C:\Users\Asus\maquinaria_pesada")
ESCALETAS_DIR = PROJECT_ROOT / "escaletas"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True,
                        help="Episode ID (ej. EP-MOD000)")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--preview-seconds", type=float, default=90.0)
    parser.add_argument("--whisper-model", default="medium",
                        choices=["tiny", "base", "small", "medium", "large-v3"])
    parser.add_argument("--escaleta", default=None,
                        help="Ruta del .md (default: escaletas/<EP>_escaleta.md)")
    parser.add_argument("--config", default="project_config.json")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    pipe_root = PROJECT_ROOT / "maquinaria_pesada_pipeline"
    config = validate_project_config(pipe_root / args.config)
    episode_id = config["episode_defaults"].get("episode_id", args.episode)
    output_folder = Path(config["assets"]["output_folder"])
    log_path = output_folder / "logs" / f"{episode_id}_pipeline.log"
    log = get_logger("render_from_escaleta", log_file=log_path)

    log.info("=" * 60)
    log.info(f"  RENDER FROM ESCALETA · {episode_id} · preview={args.preview}")
    log.info("=" * 60)

    escaleta_path = (Path(args.escaleta) if args.escaleta
                     else ESCALETAS_DIR / f"{args.episode}_escaleta.md")
    if not escaleta_path.exists():
        log.error(f"No existe {escaleta_path}")
        return 1

    # 1. Whisper
    log.info("[1/8] Transcripcion Whisper...")
    transcription = transcribe_episode(
        config["assets"]["episode_audio"], output_folder,
        model_size=args.whisper_model, force=args.force,
    )

    # 2. Content extractor
    log.info("[2/8] Extraccion contenido (guion + PDF)...")
    content = extract_content(
        config["assets"]["episode_script"],
        config["assets"].get("episode_pdf"),
        output_folder, force=args.force,
    )

    # 3. Audio analyzer
    log.info("[3/8] Analizador de audio...")
    audio_structure = analyze_episode_audio(
        config["assets"]["episode_audio"],
        config["assets"].get("intro_video"),
        output_folder, force=args.force,
    )

    # 4. Parsear escaleta
    log.info(f"[4/8] Parseando escaleta {escaleta_path.name}...")
    parsed = parse_escaleta(escaleta_path)
    log.info(f"  bloques={len(parsed['blocks'])} "
             f"intervenciones={sum(len(b['interventions']) for b in parsed['blocks'])}")

    # 5. Convertir a scene_timeline + scene_track
    log.info("[5/8] Convirtiendo escaleta a scene_timeline + scene_track...")
    videos_folder = config["assets"].get("videos_folder")
    library_base = (Path(videos_folder) / "escenas_biblioteca"
                    if videos_folder else output_folder / "escenas_biblioteca")
    library = SceneLibrary(library_base)
    write_pipeline_files(parsed, library, output_folder,
                         audio_duration=audio_structure.get("audio_duration"))
    timeline = json.loads((output_folder / "scene_timeline.json").read_text(encoding="utf-8"))
    scene_track = json.loads((output_folder / "scene_track.json").read_text(encoding="utf-8"))

    # 6. Render frames
    log.info("[6/8] Render frames PNG...")
    preview_secs = args.preview_seconds if args.preview else None
    frames_index = render_frames(
        timeline, transcription, config, output_folder,
        preview_seconds=preview_secs, force=True,  # siempre regenerar tras escaleta
    )

    # 7. SRT
    log.info("[7/8] SRT desde Whisper word-level...")
    base_name = derive_video_basename(
        config["assets"].get("episode_audio"), episode_id,
    )
    srt_path = generate_srt(
        transcription, content, output_folder, episode_id,
        force=True, videos_folder=videos_folder,
        base_name=base_name, audio_structure=audio_structure,
    )

    # 8. Composicion
    log.info("[8/8] Composicion ffmpeg...")
    final_video = compose_video(
        config, frames_index,
        config["assets"]["episode_audio"], srt_path,
        output_folder, episode_id, preview=args.preview,
        audio_structure=audio_structure,
        scene_track=scene_track,
    )

    log.info("=" * 60)
    log.info(f"  RENDER COMPLETADO -> {final_video}")
    log.info("=" * 60)
    return 0


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
