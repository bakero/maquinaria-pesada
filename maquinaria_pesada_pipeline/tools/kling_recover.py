#!/usr/bin/env python3
"""
Recupera tareas Kling huerfanas (cuando el polling fallo pero la tarea
sigue corriendo o ya completo en el servidor).

Casos de uso:
  - Polling timeout, sabes el task_id, quieres descargar el resultado.
  - Tienes un video_id de un base completado, quieres encadenar extends
    sin regenerar el base.

Uso:
    # Descargar resultado de una tarea ya completada
    python tools/kling_recover.py --task-id 881670742209859630 \\
        --slug studio_maria_solo_v1_recovered --kind base

    # Extender un video existente
    python tools/kling_recover.py --extend-from-video-id 881670742302134272 \\
        --slug studio_maria_solo_v1 --extends 2
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(r"C:\Users\Asus\maquinaria_pesada\.env", override=True)

from pipeline.logger import get_logger
from pipeline.scene_library import SceneLibrary
from pipeline.kling_generator import (
    KlingGenerator, KLING_BASE, KLING_IMG2VIDEO_PATH, KLING_EXTEND_PATH,
    DEFAULT_NEGATIVE,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True)
    p.add_argument("--task-id", default=None,
                   help="Recupera resultado de una tarea conocida")
    p.add_argument("--kind", choices=["base", "extend"], default="base")
    p.add_argument("--extend-from-video-id", default=None,
                   help="Encadena extends desde este video_id existente")
    p.add_argument("--extends", type=int, default=2,
                   help="Numero de extends a encadenar (5s cada uno)")
    p.add_argument("--category", default="estudio")
    args = p.parse_args()

    log = get_logger("kling_recover")
    lib = SceneLibrary(Path(r"C:\Users\Asus\maquinaria_pesada\Videos\escenas_biblioteca"))
    g = KlingGenerator(lib)

    last_video_id = args.extend_from_video_id
    last_video_url = None

    if args.task_id:
        path = KLING_IMG2VIDEO_PATH if args.kind == "base" else KLING_EXTEND_PATH
        log.info(f"Esperando task {args.task_id} (kind={args.kind})...")
        result = g._poll(args.task_id, path=path)
        videos = (result.get("task_result") or {}).get("videos") or []
        if not videos:
            log.error("Sin videos en el resultado")
            return 1
        last_video_id = videos[0].get("id")
        last_video_url = videos[0].get("url")
        log.info(f"  Recuperado video_id={last_video_id}")

    # Encadenar extends si toca
    for i in range(args.extends):
        log.info(f"  [extend {i+1}/{args.extends}] desde video_id={last_video_id}")
        ext_task = g._extend(video_id=last_video_id, negative_prompt=DEFAULT_NEGATIVE)
        log.info(f"    extend task_id={ext_task}")
        result = g._poll(ext_task, path=KLING_EXTEND_PATH)
        videos = (result.get("task_result") or {}).get("videos") or []
        if not videos:
            log.error("Extend sin videos")
            return 1
        last_video_id = videos[0].get("id")
        last_video_url = videos[0].get("url")
        time.sleep(2)

    if not last_video_url:
        log.error("Sin URL final")
        return 1

    dest = lib.base / args.category / f"{args.slug}.mp4"
    log.info(f"Descargando -> {dest}")
    g._download_video(last_video_url, dest)
    lib.register(slug=args.slug, path=dest, category=args.category,
                 source="kling-recovered")
    log.info(f"OK -> {dest}")
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
