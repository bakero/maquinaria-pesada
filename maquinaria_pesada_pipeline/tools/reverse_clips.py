#!/usr/bin/env python3
"""
Genera variantes invertidas (reverse playback) de clips de la library.

Para cada clip <slug>.mp4 produce <slug>_rev.mp4 con el video reversado.
Util para duplicar catalogo: la camara que orbita en una direccion en el
clip original, orbita en la otra en el reverse. Practicamente otra toma.

Limitacion: el movimiento de boca queda invertido. Solo registramos el
reverse para clips de "listening" o two-shots del lado pasivo. Los slugs
solo (ej. studio_maria_solo_v1) NO conviene reversarlos para usarse
mientras el speaker habla.

Uso:
    python tools/reverse_clips.py                # reversa los aptos
    python tools/reverse_clips.py --all          # reversa todos
    python tools/reverse_clips.py --slug studio_two_m_active_v1
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.logger import get_logger
from pipeline.scene_library import SceneLibrary


# Solo reversamos two-shots (donde uno escucha) y outros/details/establishing.
# NO reversamos solo_v* porque el speaker activo se vera con boca invertida.
REVERSE_SAFE_PATTERNS = (
    "two_m_active",   # Maria habla, Yago escucha. Reverse: queda raro Maria,
                       # pero si lo usamos para "Yago habla" en su intervencion,
                       # NO lo usaremos asi (es two_m_active no two_y_active).
                       # Revisado: si lo usamos para listening solamente.
    "two_y_active",
    "establishing",
    "both_complicit",
    "outro",
    "detail",
)


def is_reversable(slug: str, allow_all: bool) -> bool:
    if allow_all:
        return True
    return any(p in slug for p in REVERSE_SAFE_PATTERNS)


def reverse_video(src: Path, dst: Path, log) -> bool:
    """ffmpeg reverse video (no audio, los clips Kling ya vienen sin audio)."""
    if dst.exists():
        log.info(f"  ya existe: {dst.name}")
        return True
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", "reverse",
        "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "30",
        str(dst),
    ]
    log.info(f"  reversando -> {dst.name}")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as exc:
        log.error(f"    ffmpeg fallo: {exc.stderr[-500:]}")
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug", default=None,
                   help="Reversar solo este slug")
    p.add_argument("--all", action="store_true",
                   help="Reversar TODOS los clips, no solo two-shots")
    args = p.parse_args()

    log = get_logger("reverse_clips")
    library_base = Path(r"C:\Users\Asus\maquinaria_pesada\Videos\escenas_biblioteca")
    library = SceneLibrary(library_base)

    # Tomar todos los clips registrados.
    # _index estructura: {"version":..., "scenes": {slug: {...}}}
    scenes = []
    idx = getattr(library, "_index", {})
    raw_scenes = idx.get("scenes", {}) if isinstance(idx, dict) else {}
    if isinstance(raw_scenes, dict):
        scenes = list(raw_scenes.values())
    if not scenes:
        # Fallback: walk filesystem
        for p_mp4 in library_base.rglob("*.mp4"):
            if "_rev" in p_mp4.stem:
                continue
            scenes.append({"slug": p_mp4.stem, "path": str(p_mp4),
                           "category": p_mp4.parent.name})

    targets = []
    for sc in scenes:
        slug = sc.get("slug") or Path(sc.get("path","")).stem
        if "_rev" in slug:
            continue
        if args.slug and slug != args.slug:
            continue
        if not is_reversable(slug, args.all):
            continue
        targets.append(sc)

    log.info(f"Clips a reversar: {len(targets)}")
    ok = 0
    for sc in targets:
        src = Path(sc["path"])
        if not src.exists():
            log.warning(f"  no existe: {src}")
            continue
        rev_slug = f"{src.stem}_rev"
        rev_path = src.parent / f"{rev_slug}.mp4"
        if reverse_video(src, rev_path, log):
            library.register(
                slug=rev_slug, path=rev_path,
                category=sc.get("category", "estudio"),
                source="reversed",
                tags=["reversed", "listening_only"],
                description=f"Reverse playback de {src.stem}",
            )
            ok += 1
    log.info(f"OK: {ok}/{len(targets)} reversados.")
    return 0 if ok == len(targets) else 1


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
