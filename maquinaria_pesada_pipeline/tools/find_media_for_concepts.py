#!/usr/bin/env python3
"""
Lanza la busqueda y descarga de medios (imagenes, GIFs) para los conceptos
del master que aparecen en >=2 modulos.

Output: Videos/escenas_biblioteca/media/<slug_concepto>/*.jpg|png|gif
        + _media_index.json con metadata.

Uso:
    python tools/find_media_for_concepts.py
    python tools/find_media_for_concepts.py --top 50 --min 3
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT.parent / ".env", override=True)

from pipeline.media_finder import find_media_for_concepts

_LIBRARY_DIR = ROOT.parent / "Videos" / "escenas_biblioteca"
CONCEPTS_PATH = _LIBRARY_DIR / "_concepts_index.json"
LIBRARY_BASE = _LIBRARY_DIR / "media"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=None,
                        help="Limitar a top N conceptos por reuso (None = todos)")
    parser.add_argument("--min", type=int, default=2,
                        help="Minimo de modulos donde aparece para considerarlo")
    parser.add_argument("--no-gif", action="store_true",
                        help="No buscar GIFs en Tenor")
    args = parser.parse_args()

    if not CONCEPTS_PATH.exists():
        print(f"[ERROR] No existe {CONCEPTS_PATH}")
        return 1

    find_media_for_concepts(
        concepts_index_path=CONCEPTS_PATH,
        library_base=LIBRARY_BASE,
        min_apariciones=args.min,
        top_n=args.top,
        want_gif=not args.no_gif,
    )
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
