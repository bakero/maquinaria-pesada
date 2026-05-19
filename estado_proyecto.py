#!/usr/bin/env python3
"""
estado_proyecto.py
------------------
Estado de producción de MaquinarIA Pesada.

Nomenclatura de archivos:
  - Guiones M (módulo): M0_Nombre.txt
  - Guiones T (tema):   M0_TX_Nombre.txt
  - Audio M:            M0_E_Nombre.mp3
  - Audio T:            M0_TX_E_Nombre.mp3
  - Video:              M0_V_Nombre.mp4

Uso:
  python estado_proyecto.py              # tabla completa
  python estado_proyecto.py --codex      # comandos pendientes para generar audio
  python estado_proyecto.py --pendiente  # solo módulos incompletos
  python estado_proyecto.py --assets     # verifica assets del proyecto
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from podcast_spec import load_spec, guion_to_ep_code, episode_type

# ---------------------------------------------------------------------------
# Cargar directorios desde M-spec
# ---------------------------------------------------------------------------

_spec = load_spec(BASE_DIR / "PODCAST_M_SPEC.md")
_dirs = _spec["directories"]

PDF_DIR      = BASE_DIR / _dirs["pdfs_resumenes_dir"]   # PDFs/resumenes/
GUIONES_DIR  = BASE_DIR / _dirs["scripts_dir"]          # Guiones/
AUDIO_DIR    = BASE_DIR / _dirs["output_dir"]           # episodios/
VIDEO_DIR    = BASE_DIR / _dirs["videos_dir"]           # Videos/
MUSIC_DIR    = BASE_DIR / _dirs["music_dir"]
LOGOS_DIR    = BASE_DIR / _dirs["logos_dir"]
DEFAULT_LOGO = BASE_DIR / _dirs["default_logo"]

# ---------------------------------------------------------------------------
# Patrones de nombre de fichero
# ---------------------------------------------------------------------------

# PDFs de resumen de módulo: RESUMEN_M0_*.pdf
PDF_RE   = re.compile(r"^RESUMEN_M(\d+)_.+\.pdf$",   re.IGNORECASE)

# Guiones M (módulo): M0_Nombre.txt  (sin _TX_)
GUION_M_RE = re.compile(r"^M(\d+)_(?!TX_)(.+)\.txt$", re.IGNORECASE)

# Guiones T (tema): M0_TX_Nombre.txt
GUION_T_RE = re.compile(r"^M(\d+)_TX_(.+)\.txt$",   re.IGNORECASE)

# Audio M: M0_E_Nombre.mp3
AUDIO_M_RE = re.compile(r"^M(\d+)_E_(.+)\.mp3$",    re.IGNORECASE)

# Audio T: M0_TX_E_Nombre.mp3
AUDIO_T_RE = re.compile(r"^M(\d+)_TX_E_(.+)\.mp3$", re.IGNORECASE)

# Video: M0_V_Nombre.mp4
VIDEO_RE   = re.compile(r"^M(\d+)_V_(.+)\.mp4$",    re.IGNORECASE)

# Retrocompatibilidad: guiones viejos M0_T_Nombre.txt (del sistema anterior)
GUION_LEGACY_RE = re.compile(r"^M(\d+)_T_(.+)\.txt$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def scan(directory: Path, pattern: re.Pattern) -> dict[int, Path]:
    """Devuelve {numero_modulo: ruta} para los ficheros que encajan."""
    result: dict[int, Path] = {}
    if not directory.exists():
        return result
    for path in sorted(directory.iterdir()):
        m = pattern.match(path.name)
        if m:
            result[int(m.group(1))] = path
    return result


def cell(ok: bool) -> str:
    return "SI" if ok else "--"


def print_estado_resumen() -> None:
    """Imprime resumen compacto de producción. Llama desde scripts de producción."""
    pdfs    = scan(PDF_DIR,     PDF_RE)
    guiones = scan(GUIONES_DIR, GUION_M_RE)
    audios  = scan(AUDIO_DIR,   AUDIO_M_RE)
    videos  = scan(VIDEO_DIR,   VIDEO_RE)

    all_modules = sorted(set(pdfs) | set(guiones) | set(audios) | set(videos))

    sin_guion = [m for m in all_modules if m in pdfs and m not in guiones]
    sin_audio = [m for m in all_modules if m in guiones and m not in audios]
    sin_video = [m for m in all_modules if m in audios and m not in videos]
    completos = [m for m in all_modules if m in audios and m in videos]

    sep = "-" * 52
    print()
    print(sep)
    print("ESTADO  MaquinarIA Pesada")
    print(f"  PDFs {len(pdfs)}  |  Guiones {len(guiones)}  |  Audio {len(audios)}  |  Video {len(videos)}")
    if sin_guion:
        print(f"  Sin guion ({len(sin_guion)}): {', '.join(f'M{m}' for m in sin_guion)}")
    if sin_audio:
        print(f"  Sin audio ({len(sin_audio)}): {', '.join(f'M{m}' for m in sin_audio)}")
    if sin_video:
        print(f"  Sin video ({len(sin_video)}): {', '.join(f'M{m}' for m in sin_video)}")
    if completos:
        print(f"  Completos ({len(completos)}): {', '.join(f'M{m}' for m in completos)}")
    print(sep)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Estado de producción de MaquinarIA Pesada")
    parser.add_argument("--codex",     action="store_true", help="Comandos pendientes de audio")
    parser.add_argument("--pendiente", action="store_true", help="Solo módulos incompletos")
    parser.add_argument("--assets",    action="store_true", help="Verifica assets del proyecto")
    args = parser.parse_args()

    # ── Modo --assets ───────────────────────────────────────────────────────
    if args.assets:
        print("\nVERIFICACION DE ASSETS — MaquinarIA Pesada")
        print("=" * 50)
        assets = [
            (BASE_DIR / "Música" / "base podcast.mp3",               "Música de fondo"),
            (BASE_DIR / "Música" / "Sintonia Maquinaria pesada.mp3", "Sintonía podcast"),
            (BASE_DIR / "intro",                                       "Carpeta intro"),
            (BASE_DIR / LOGOS_DIR,                                     "Carpeta logos"),
            (BASE_DIR / DEFAULT_LOGO,                                  "Logo por defecto"),
            (BASE_DIR / "BIBLIA_SISTEMA.md",                           "BIBLIA_SISTEMA.md"),
            (BASE_DIR / "PRIMERPODCAST.md",                            "PRIMERPODCAST.md"),
            (BASE_DIR / "VIDEOPODCAST.md",                             "VIDEOPODCAST.md"),
            (BASE_DIR / "PODCAST.md",                                  "PODCAST.md"),
        ]
        all_ok = True
        for path, label in assets:
            exists = path.exists()
            status = "OK" if exists else "NO ENCONTRADO"
            print(f"  [{status:^14}] {label}")
            if not exists:
                all_ok = False
        print()
        print("Todos los assets OK." if all_ok else "Algunos assets no encontrados.")
        return

    pdfs    = scan(PDF_DIR,     PDF_RE)
    guiones = scan(GUIONES_DIR, GUION_M_RE)
    audios  = scan(AUDIO_DIR,   AUDIO_M_RE)
    videos  = scan(VIDEO_DIR,   VIDEO_RE)

    # También detectar guiones legacy (nomenclatura antigua _T_)
    legacy = scan(GUIONES_DIR, GUION_LEGACY_RE)
    if legacy:
        print(f"\n[AVISO] {len(legacy)} guion(es) con nomenclatura antigua (_T_):")
        for m, p in legacy.items():
            print(f"  M{m}: {p.name}")
        print()

    all_modules = sorted(set(pdfs) | set(guiones) | set(audios) | set(videos))

    # ── Modo --codex ────────────────────────────────────────────────────────
    if args.codex:
        pending = [m for m in all_modules if m in guiones and m not in audios]
        if not pending:
            print("Sin guiones pendientes de audio.")
            return
        print(f"# Comandos — {len(pending)} episodio(s) pendiente(s) de audio\n")
        for mod in pending:
            guion_rel = guiones[mod].relative_to(BASE_DIR)
            ep_code   = guion_to_ep_code(guiones[mod].stem)
            print(f"python generar_episodio_v2.py --guion {guion_rel} --ep {ep_code}")
        return

    # ── Tabla completa ───────────────────────────────────────────────────────
    COL_MOD  = 7
    COL_TEMA = 34
    COL_ITEM = 7

    header = (
        f"{'MOD':<{COL_MOD}}"
        f"{'TEMA':<{COL_TEMA}}"
        f"{'PDF':<{COL_ITEM}}"
        f"{'GUION':<{COL_ITEM}}"
        f"{'AUDIO':<{COL_ITEM}}"
        f"{'VIDEO':<{COL_ITEM}}"
        f"ESTADO"
    )
    sep = "-" * len(header)

    sin_guion: list[int] = []
    sin_audio: list[int] = []
    sin_video: list[int] = []
    completos: list[int] = []
    rows: list[str] = []

    for mod in all_modules:
        has_pdf   = mod in pdfs
        has_guion = mod in guiones
        has_audio = mod in audios
        has_video = mod in videos

        # Nombre del tema desde PDF
        if has_pdf:
            stem = pdfs[mod].stem  # RESUMEN_M0_Introduccion_Estrategica
            tema = re.sub(r"^RESUMEN_M\d+_", "", stem, flags=re.IGNORECASE).replace("_", " ")
        else:
            tema = "?"

        if has_pdf and not has_guion:
            estado = "FALTA GUION"
            sin_guion.append(mod)
        elif has_guion and not has_audio:
            estado = "FALTA AUDIO"
            sin_audio.append(mod)
        elif has_audio and not has_video:
            estado = "FALTA VIDEO"
            sin_video.append(mod)
        elif has_audio and has_video:
            estado = "COMPLETO"
            completos.append(mod)
        else:
            estado = "OK"

        if args.pendiente and estado in ("COMPLETO", "OK"):
            continue

        rows.append(
            f"{'M' + str(mod):<{COL_MOD}}"
            f"{tema[:COL_TEMA - 1]:<{COL_TEMA}}"
            f"{cell(has_pdf):<{COL_ITEM}}"
            f"{cell(has_guion):<{COL_ITEM}}"
            f"{cell(has_audio):<{COL_ITEM}}"
            f"{cell(has_video):<{COL_ITEM}}"
            f"{estado}"
        )

    print()
    print("ESTADO DE PRODUCCION — MaquinarIA Pesada")
    print("=" * len(header))
    print(header)
    print(sep)
    for row in rows:
        print(row)
    print(sep)
    print()
    print(f"  PDFs: {len(pdfs)}  |  Guiones M: {len(guiones)}  |  Audio: {len(audios)}  |  Video: {len(videos)}")
    if sin_guion:
        print(f"  Sin guion  ({len(sin_guion)}): {', '.join(f'M{m}' for m in sin_guion)}")
    if sin_audio:
        print(f"  Sin audio  ({len(sin_audio)}): {', '.join(f'M{m}' for m in sin_audio)}")
    if sin_video:
        print(f"  Sin video  ({len(sin_video)}): {', '.join(f'M{m}' for m in sin_video)}")
    if completos:
        print(f"  Completos  ({len(completos)}): {', '.join(f'M{m}' for m in completos)}")
    print()
    if sin_audio:
        print("  Para audio pendiente:  python generar_episodio_v2.py --ep <id>")
    if sin_guion:
        print("  Para guion (M/T/S):    python lanzar_produccion.py --kind {M|T|S} --ep <id>")


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="estado_proyecto.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
