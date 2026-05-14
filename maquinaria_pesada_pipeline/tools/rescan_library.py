#!/usr/bin/env python3
"""
Reconstruye _scenes_index.json escaneando los MP4 ya descargados en
Videos/escenas_biblioteca/<categoria>/. Util cuando el index se ha borrado
o desincronizado, para no tener que regenerar con Luma.

Lee tools/generate_studio_clips.py para recuperar los metadatos (prompt,
tags, etc.) de cada slug conocido.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.scene_library import SceneLibrary
from pipeline.logger import get_logger
from tools.generate_studio_clips import STUDIO_CLIPS


LIBRARY_BASE = Path(r"C:\Users\Asus\maquinaria_pesada\Videos\escenas_biblioteca")


def main():
    log = get_logger("rescan_library")
    library = SceneLibrary(LIBRARY_BASE)
    by_slug = {c["slug"]: c for c in STUDIO_CLIPS}

    registered = 0
    missing = 0

    for slug, meta in by_slug.items():
        category = meta["category"]
        cat_dir = LIBRARY_BASE / category
        mp4 = cat_dir / f"{slug}.mp4"
        if not mp4.exists():
            log.warning(f"  no en disco: {category}/{slug}.mp4")
            missing += 1
            continue
        if library.find(slug):
            log.info(f"  ya registrado: {slug}")
            continue
        library.register(
            slug=slug, path=mp4,
            category=category,
            prompt=meta.get("prompt", ""),
            description=meta.get("description", ""),
            tags=meta.get("tags", []),
            source="luma",
        )
        registered += 1

    log.info(f"Hecho. registered={registered} · missing={missing} · total={library.stats()['total']}")
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
