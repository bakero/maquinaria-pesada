#!/usr/bin/env python3
"""
Reconcilia el journal kling_tasks.jsonl con el estado actual de Kling.

Para cada slug en el journal que no este descargado/QA-OK/registrado:
  1. Pollea el LAST task_id (el que da el video final).
  2. Si Kling reporta succeed -> descarga + QA + registra.
  3. Si fallido -> marca en journal como fail.

Uso:
    # Reconcilia todo lo huerfano
    python tools/kling_reconcile.py

    # Solo reportar (dry-run)
    python tools/kling_reconcile.py --dry-run

    # Reconciliar un slug concreto
    python tools/kling_reconcile.py --slug studio_yago_solo_v1
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT.parent / ".env", override=True)

from pipeline.logger import get_logger
from pipeline.scene_library import SceneLibrary
from pipeline.kling_generator import (
    KlingGenerator, KLING_BASE, KLING_IMG2VIDEO_PATH, KLING_EXTEND_PATH,
)
from pipeline.kling_tasks import get_tracker
from pipeline import qa


def _last_task_id(entry: dict) -> tuple[str, str] | None:
    """Devuelve (task_id, kind_path) del ULTIMO paso submitido para
    este slug. kind_path = KLING_IMG2VIDEO_PATH o KLING_EXTEND_PATH."""
    if entry.get("extends"):
        # El ultimo extend
        max_step = max(entry["extends"].keys())
        ext = entry["extends"][max_step]
        return (ext["task_id"], KLING_EXTEND_PATH)
    if entry.get("base_task"):
        return (entry["base_task"], KLING_IMG2VIDEO_PATH)
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug", default=None,
                   help="Reconciliar solo este slug")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    log = get_logger("kling_reconcile")
    library = SceneLibrary(ROOT.parent / "Videos" / "escenas_biblioteca")
    tracker = get_tracker()
    g = KlingGenerator(library)

    agg = tracker.aggregate()
    log.info(f"Slugs en journal: {len(agg)}")

    pending = []
    for slug, entry in agg.items():
        if args.slug and slug != args.slug:
            continue
        if entry["downloaded"] and entry["registered"] and entry["qa_ok"]:
            continue
        # Verificar si el archivo fisico ya existe y registrado en library
        existing = library.find(slug)
        if existing and Path(existing.get("path", "")).exists():
            # Comprobar QA
            qa_res = qa.check_kling_clip(existing["path"], expected_min_duration=8.0)
            if qa_res["ok"]:
                continue   # ya OK
        pending.append((slug, entry))

    log.info(f"Pendientes de reconciliar: {len(pending)}")
    if not pending:
        log.info("Nada que reconciliar.")
        return 0

    if args.dry_run:
        for slug, e in pending:
            ltask = _last_task_id(e)
            log.info(f"  [DRY] {slug}: last_task={ltask} downloaded={e['downloaded']} "
                     f"registered={e['registered']} qa_ok={e['qa_ok']}")
        return 0

    recovered = 0
    failed = 0
    for slug, entry in pending:
        ltask = _last_task_id(entry)
        if not ltask:
            log.warning(f"  {slug}: sin task_id, skip")
            continue
        task_id, path = ltask
        log.info(f"  {slug}: poll {task_id[:10]}...")

        try:
            result = g._poll(task_id, path=path, max_seconds=120,
                              poll_interval=5)
        except Exception as exc:
            log.warning(f"    poll fallo: {exc}")
            tracker.log_failure(slug, task_id, f"reconcile poll: {exc}")
            failed += 1
            continue

        videos = (result.get("task_result") or {}).get("videos") or []
        if not videos:
            log.warning(f"    succeed sin videos")
            tracker.log_failure(slug, task_id, "reconcile: succeed sin videos")
            failed += 1
            continue

        video_url = videos[0].get("url")
        video_id = videos[0].get("id")
        tracker.log_complete(slug, task_id, video_id, video_url)

        # Descargar + QA + registrar
        try:
            cat = "estudio"   # default; podriamos inferir de slug si fuera relevante
            dest = library.base / cat / f"{slug}.mp4"
            g._download_video(video_url, dest)
            tracker.log_download(slug, dest, dest.stat().st_size)

            # QA con tolerancia amplia (no sabemos target real)
            qa_res = qa.check_kling_clip(dest, expected_min_duration=8.0,
                                          expected_max_duration=30.0)
            tracker.log_qa(slug, qa_res["ok"], qa_res["checks"])
            if not qa_res["ok"]:
                log.error(f"    QA FAILED: {qa_res['errors']}")
                dest.unlink()
                failed += 1
                continue

            library.register(
                slug=slug, path=dest, category=cat,
                source="kling-recovered",
                description=f"Recuperado de Kling task {task_id[:10]}",
            )
            tracker.log_register(slug, ok=True)
            log.info(f"    OK descargado + registrado: {dest.name}")
            recovered += 1
        except Exception as exc:
            log.error(f"    fallo descarga/registro: {exc}")
            tracker.log_register(slug, ok=False, error=str(exc))
            failed += 1

    log.info(f"\n=== Reconcile completo ===")
    log.info(f"  recuperados: {recovered}")
    log.info(f"  fallidos:    {failed}")
    log.info(f"  total slugs: {len(pending)}")
    return 0 if failed == 0 else 1


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
