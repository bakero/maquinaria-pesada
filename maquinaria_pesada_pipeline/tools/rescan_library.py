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
    raise SystemExit(main())
