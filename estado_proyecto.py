#!/usr/bin/env python3
"""
estado_proyecto.py
------------------
Estado de produccion de MaquinarIA Pesada.

Muestra para cada modulo del master si tiene:
  - PDF de contenido (fuente)
  - Guion de episodio generado
  - Episodio de audio generado
  - Episodio de videopodcast generado

Las rutas se leen desde PODCAST_MASTER_SPEC.md (fuente unica de verdad).

Uso:
  python estado_proyecto.py              # tabla completa
  python estado_proyecto.py --codex      # comandos pendientes para Codex
  python estado_proyecto.py --pendiente  # solo modulos incompletos
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Cargar spec y resolver rutas
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from podcast_spec import load_master_spec

_spec = load_master_spec(BASE_DIR / "PODCAST_MASTER_SPEC.md")
_dirs = _spec["directories"]

PDF_DIR     = BASE_DIR / _dirs["pdfs_dir"]
GUIONES_DIR = BASE_DIR / _dirs["scripts_dir"]
AUDIO_DIR   = BASE_DIR / _dirs["output_dir"]
VIDEO_DIR   = BASE_DIR / _dirs["videos_dir"]
MUSIC_DIR   = BASE_DIR / _dirs["music_dir"]
INTRO_DIR   = BASE_DIR / _dirs["intro_dir"]
LOGOS_DIR   = BASE_DIR / _dirs["logos_dir"]
DEFAULT_LOGO = BASE_DIR / _dirs["default_logo"]

# ---------------------------------------------------------------------------
# Patrones de nombre de fichero
# ---------------------------------------------------------------------------

PDF_RE   = re.compile(r"^M(\d+)_T_(.+)\.pdf$",                              re.IGNORECASE)
GUION_RE = re.compile(r"^M(\d+)_T_(.+)\.txt$",                              re.IGNORECASE)
AUDIO_RE = re.compile(r"^M(\d+)_E_(.+)\.mp3$",                              re.IGNORECASE)
VIDEO_RE = re.compile(r"^M(\d+)_V_(.+)\.mp4$",                              re.IGNORECASE)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def scan(directory: Path, pattern: re.Pattern) -> dict[int, Path]:
    """Devuelve {numero_modulo: ruta} para los ficheros que encajan con el patron."""
    result: dict[int, Path] = {}
    if not directory.exists():
        return result
    for path in sorted(directory.iterdir()):
        m = pattern.match(path.name)
        if m:
            result[int(m.group(1))] = path
    return result


def pdf_label(path: Path) -> str:
    m = PDF_RE.match(path.name)
    return m.group(2).replace("_", " ") if m else path.stem


def cell(ok: bool) -> str:
    return "SI" if ok else "--"


def check_asset(path: Path, label: str) -> str:
    return f"  {label}: {path} {'[OK]' if path.exists() else '[NO ENCONTRADO]'}"


def print_estado_resumen() -> None:
    """
    Imprime un resumen compacto del estado de produccion.
    Importar y llamar al final de cualquier script de produccion.
    """
    pdfs    = scan(PDF_DIR,     PDF_RE)
    guiones = scan(GUIONES_DIR, GUION_RE)
    audios  = scan(AUDIO_DIR,   AUDIO_RE)
    videos  = scan(VIDEO_DIR,   VIDEO_RE)

    all_modules = sorted(set(pdfs) | set(guiones) | set(audios) | set(videos))

    sin_guion = [m for m in all_modules if m in pdfs and m not in guiones]
    sin_audio = [m for m in all_modules if m in guiones and m not in audios]
    sin_video = [m for m in all_modules if m in audios and m not in videos]
    completos = [m for m in all_modules if m in audios and m in videos]

    linea = "-" * 52
    print()
    print(linea)
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
    print(linea)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Estado de produccion de MaquinarIA Pesada")
    parser.add_argument("--codex",     action="store_true", help="Comandos pendientes para Codex")
    parser.add_argument("--pendiente", action="store_true", help="Solo modulos incompletos")
    parser.add_argument("--assets",    action="store_true", help="Verifica ficheros de assets del proyecto")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Modo --assets: verifica musica, intro, logos
    # ------------------------------------------------------------------
    if args.assets:
        print()
        print("VERIFICACION DE ASSETS — MaquinarIA Pesada")
        print("=" * 50)

        assets = [
            (MUSIC_DIR / "base podcast.mp3",              "Musica de fondo"),
            (MUSIC_DIR / "Sintonia Maquinaria pesada.mp3","Sintonia podcast"),
            (INTRO_DIR,                                    "Carpeta intro videopodcast"),
            (LOGOS_DIR,                                    "Carpeta logos"),
            (DEFAULT_LOGO,                                 "Logo por defecto"),
        ]
        all_ok = True
        for path, label in assets:
            exists = path.exists()
            status = "OK" if exists else "NO ENCONTRADO"
            print(f"  [{status:^14}] {label}")
            print(f"               {path}")
            if not exists:
                all_ok = False

        print()
        if all_ok:
            print("Todos los assets estan en su lugar.")
        else:
            print("Algunos assets no se encontraron. Revisa las rutas en PODCAST_MASTER_SPEC.md.")
        return

    pdfs    = scan(PDF_DIR,     PDF_RE)
    guiones = scan(GUIONES_DIR, GUION_RE)
    audios  = scan(AUDIO_DIR,   AUDIO_RE)
    videos  = scan(VIDEO_DIR,   VIDEO_RE)

    all_modules = sorted(set(pdfs) | set(guiones) | set(audios) | set(videos))

    # ------------------------------------------------------------------
    # Modo --codex: solo comandos para Codex
    # ------------------------------------------------------------------
    if args.codex:
        pending = [m for m in all_modules if m in guiones and m not in audios]
        if not pending:
            print("Sin guiones pendientes de audio. Todos los guiones tienen episodio.")
            return
        print(f"# Comandos para Codex — {len(pending)} episodio(s) pendiente(s) de audio")
        print()
        for mod in pending:
            guion_rel = guiones[mod].relative_to(BASE_DIR)
            # Guion: M0_T_Nombre.txt → ep_code audio: M0_E_Nombre
            ep_code = guiones[mod].stem.replace("_T_", "_E_", 1)
            print(f"python generar_episodio_v2.py --guion {guion_rel} --ep {ep_code}")
        return

    # ------------------------------------------------------------------
    # Tabla de estado completa
    # ------------------------------------------------------------------
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

    sin_guion : list[int] = []
    sin_audio : list[int] = []
    sin_video : list[int] = []
    completos : list[int] = []
    rows      : list[str] = []

    for mod in all_modules:
        has_pdf   = mod in pdfs
        has_guion = mod in guiones
        has_audio = mod in audios
        has_video = mod in videos

        tema = pdf_label(pdfs[mod]) if has_pdf else "?"

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
    print("RESUMEN")
    print("-------")
    print(f"  PDFs disponibles:    {len(pdfs)}")
    print(f"  Guiones generados:   {len(guiones)}")
    print(f"  Episodios de audio:  {len(audios)}")
    print(f"  Episodios de video:  {len(videos)}")
    print()

    if sin_guion:
        nombres = [pdf_label(pdfs[m]) for m in sin_guion if m in pdfs]
        print(f"  Sin guion  ({len(sin_guion)}):  " + ", ".join(f"M{m} ({n})" for m, n in zip(sin_guion, nombres)))
    if sin_audio:
        print(f"  Sin audio  ({len(sin_audio)}):  " + ", ".join(f"M{m}" for m in sin_audio))
    if sin_video:
        print(f"  Sin video  ({len(sin_video)}):  " + ", ".join(f"M{m}" for m in sin_video))
    if completos:
        print(f"  Completos  ({len(completos)}):  " + ", ".join(f"M{m}" for m in completos))

    print()
    if sin_audio:
        print("Para generar los audios pendientes con Codex:")
        print("  python estado_proyecto.py --codex")
    if sin_guion:
        print("Pide a Claude Code que genere los guiones pendientes antes de lanzar Codex.")
    if not sin_guion and not sin_audio and not sin_video:
        print("Produccion completada para todos los modulos.")


if __name__ == "__main__":
    main()
