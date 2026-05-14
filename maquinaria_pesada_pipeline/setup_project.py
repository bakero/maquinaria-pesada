#!/usr/bin/env python3
"""
MaquinarIA Pesada — Setup interactivo de proyecto
Ejecutar UNA VEZ para configurar las rutas de assets.
La configuracion se guarda en project_config.json y se reutiliza en todos los episodios.

Uso:
    python setup_project.py                # configuracion completa
    python setup_project.py --episode-only # solo actualizar assets del episodio
"""

import os
import sys
import json
import argparse
from pathlib import Path


def ask_path(prompt: str, asset_type: str, required: bool = True,
             valid_extensions: list = None) -> str | None:
    """
    Pregunta al usuario la ruta de un asset, valida existencia y extension.
    Acepta rutas absolutas, relativas o ~.
    """
    while True:
        print(f"\n{'='*60}")
        print(f"  {prompt}")
        if valid_extensions:
            print(f"  Formatos validos: {', '.join(valid_extensions)}")
        if not required:
            print(f"  (Opcional - pulsa ENTER para saltar)")
        print(f"{'='*60}")

        raw = input("  Ruta: ").strip().strip('"').strip("'")

        if not raw and not required:
            print(f"  [SKIP] Saltado (opcional)")
            return None

        if not raw and required:
            print(f"  [ERROR] Este asset es obligatorio. Introduce una ruta valida.")
            continue

        path = Path(raw).expanduser().resolve()

        if not path.exists():
            print(f"  [ERROR] No encontrado: {path}")
            print(f"          Comprueba la ruta e intentalo de nuevo.")
            continue

        if valid_extensions and path.suffix.lower() not in valid_extensions:
            print(f"  [ERROR] Extension no valida: {path.suffix}")
            print(f"          Se esperaba: {', '.join(valid_extensions)}")
            continue

        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  [OK] Encontrado: {path.name} ({size_mb:.1f} MB)")
        return str(path)


def ask_folder(prompt: str, required: bool = True) -> str | None:
    """Pregunta la ruta de una carpeta y valida que existe."""
    while True:
        print(f"\n{'='*60}")
        print(f"  {prompt}")
        if not required:
            print(f"  (Opcional - pulsa ENTER para saltar)")
        print(f"{'='*60}")

        raw = input("  Ruta de carpeta: ").strip().strip('"').strip("'")

        if not raw and not required:
            return None
        if not raw and required:
            print(f"  [ERROR] Carpeta obligatoria.")
            continue

        path = Path(raw).expanduser().resolve()

        if not path.exists() or not path.is_dir():
            print(f"  [ERROR] Carpeta no encontrada: {path}")
            continue

        files = list(path.iterdir())
        print(f"  [OK] Carpeta encontrada: {path} ({len(files)} archivos)")
        return str(path)


def collect_global_assets(config: dict) -> dict:
    """BLOQUE A - Assets globales del proyecto."""
    print("\n" + "-" * 60)
    print("  BLOQUE A - ASSETS GLOBALES DEL PROYECTO")
    print("  (Logos, musica, videos de intro - se usan en todos los episodios)")
    print("-" * 60)

    config["assets"]["logo_watermark"] = ask_path(
        prompt="A1 - LOGO SIN FONDO (watermark del video)\n"
               "     Debe ser PNG con fondo transparente.\n"
               "     Ejemplo: /proyecto/logos/logo_sin_fondo.png",
        asset_type="logo",
        required=True,
        valid_extensions=[".png"],
    )

    config["assets"]["logos_folder"] = ask_folder(
        prompt="A2 - CARPETA DE LOGOS\n"
               "     Carpeta con todos los logos del proyecto.\n"
               "     Ejemplo: /proyecto/logos/",
        required=False,
    )

    config["assets"]["intro_video"] = ask_path(
        prompt="A3 - VIDEO DE INTRO (sintonia de MaquinarIA Pesada)\n"
               "     Video que se inserta al inicio de cada episodio.\n"
               "     Ejemplo: /proyecto/videos/intro_maquinaria_pesada.mp4",
        asset_type="video_intro",
        required=True,
        valid_extensions=[".mp4", ".mov", ".avi", ".mkv"],
    )

    config["assets"]["sintonia_audio"] = ask_path(
        prompt="A4 - SINTONIA DE AUDIO (MP3 o WAV)\n"
               "     Musica de la sintonia del podcast.\n"
               "     Ejemplo: /proyecto/musica/Sintonia_Maquinaria_pesada.mp3",
        asset_type="sintonia",
        required=True,
        valid_extensions=[".mp3", ".wav", ".aac", ".m4a"],
    )

    config["assets"]["background_music"] = ask_path(
        prompt="A5 - MUSICA DE FONDO DEL PODCAST\n"
               "     Track de fondo que suena durante el episodio (loop).\n"
               "     Ejemplo: /proyecto/musica/base_podcast.mp3",
        asset_type="background_music",
        required=True,
        valid_extensions=[".mp3", ".wav", ".aac", ".m4a"],
    )

    config["assets"]["music_folder"] = ask_folder(
        prompt="A6 - CARPETA DE MUSICA\n"
               "     Carpeta con todos los archivos de musica del proyecto.\n"
               "     Ejemplo: /proyecto/musica/",
        required=False,
    )

    config["assets"]["videos_folder"] = ask_folder(
        prompt="A7 - CARPETA DE VIDEOS\n"
               "     Carpeta con los videos del proyecto (intros, outros, etc.)\n"
               "     Ejemplo: /proyecto/videos/",
        required=False,
    )

    config["assets"]["stickers_folder"] = ask_folder(
        prompt="A8 - CARPETA DE STICKERS (opcional)\n"
               "     PNGs transparentes de memes/iconos para overlays de humor.\n"
               "     Si no tienes, los generaremos con IA.\n"
               "     Ejemplo: /proyecto/stickers/",
        required=False,
    )

    return config


def collect_episode_assets(config: dict) -> dict:
    """BLOQUE B - Assets del episodio actual."""
    print("\n" + "-" * 60)
    print("  BLOQUE B - ASSETS DEL EPISODIO ACTUAL")
    print("  (Guion, audio y PDF de contenido del episodio a procesar)")
    print("-" * 60)

    config["assets"]["episode_script"] = ask_path(
        prompt="B1 - GUION ETIQUETADO DEL EPISODIO\n"
               "     Archivo .txt con la estructura:\n"
               "     # SECCION\n"
               "     SPEAKER: [tono] texto\n"
               "     Ejemplo: /proyecto/episodios/EP-MOD000_guion_etiquetas_v1.txt",
        asset_type="script",
        required=True,
        valid_extensions=[".txt"],
    )

    config["assets"]["episode_audio"] = ask_path(
        prompt="B2 - AUDIO FINAL DEL EPISODIO (MP3)\n"
               "     El audio del episodio ya producido con ElevenLabs.\n"
               "     Ejemplo: /proyecto/episodios/EP-MOD000_MaquinarIaPesada_final.mp3",
        asset_type="audio",
        required=True,
        valid_extensions=[".mp3", ".wav", ".m4a", ".aac"],
    )

    config["assets"]["episode_pdf"] = ask_path(
        prompt="B3 - PDF DE CONTENIDO DEL EPISODIO (opcional pero recomendado)\n"
               "     Resumen o material del modulo. Se usa para extraer\n"
               "     datos, estadisticas y conceptos clave automaticamente.\n"
               "     Ejemplo: /proyecto/episodios/RESUMEN_M0_Introduccion.pdf",
        asset_type="pdf",
        required=False,
        valid_extensions=[".pdf"],
    )

    config["assets"]["episode_log"] = ask_path(
        prompt="B4 - LOG DE PRODUCCION (opcional)\n"
               "     Archivo .log generado en la produccion del audio.\n"
               "     Contiene metadatos de bloques, voces y tiempos.\n"
               "     Ejemplo: /proyecto/episodios/EP-MOD000_produccion.log",
        asset_type="log",
        required=False,
        valid_extensions=[".log", ".txt"],
    )

    return config


def collect_output_config(config: dict) -> dict:
    """BLOQUE C - Configuracion de output."""
    print("\n" + "-" * 60)
    print("  BLOQUE C - CONFIGURACION DE OUTPUT")
    print("-" * 60)

    print("\n" + "=" * 60)
    print("  C1 - CARPETA DE SALIDA")
    print("  Donde se guardaran los videos generados.")
    print("  Ejemplo: /proyecto/outputs/  o  ~/Desktop/videopodcast_output/")
    print("=" * 60)
    raw_out = input("  Ruta de carpeta de salida: ").strip().strip('"').strip("'")
    if not raw_out:
        raw_out = "./outputs"
    out_path = Path(raw_out).expanduser().resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "logs").mkdir(parents=True, exist_ok=True)
    (out_path / "clips").mkdir(parents=True, exist_ok=True)
    (out_path / "frames_cache").mkdir(parents=True, exist_ok=True)
    config["assets"]["output_folder"] = str(out_path)
    print(f"  [OK] Carpeta de salida: {out_path}")

    print("\n" + "=" * 60)
    print("  C2 - ID DEL EPISODIO")
    print("  Identificador unico para nombrar los archivos de output.")
    print("  Ejemplo: EP-MOD000  /  EP-MOD001  /  EP-MOD002")
    print("=" * 60)
    ep_id = input("  ID del episodio: ").strip() or "EP-MOD000"
    config["episode_defaults"]["episode_id"] = ep_id
    print(f"  [OK] ID: {ep_id}")

    print("\n" + "=" * 60)
    print("  C3 - RESOLUCION DE OUTPUT")
    print("  1 = 1920x1080 (YouTube, recomendado)")
    print("  2 = 1280x720  (mas rapido de renderizar)")
    print("=" * 60)
    res_choice = input("  Elige [1/2] (default: 1): ").strip() or "1"
    config["episode_defaults"]["resolution"] = (
        "1920x1080" if res_choice == "1" else "1280x720"
    )
    print(f"  [OK] Resolucion: {config['episode_defaults']['resolution']}")

    return config


def print_summary(config: dict) -> None:
    print("\n" + "=" * 60)
    print("  RESUMEN DE CONFIGURACION")
    print("=" * 60)

    print("\n  ASSETS GLOBALES:")
    global_keys = [
        "logo_watermark", "logos_folder", "intro_video", "sintonia_audio",
        "background_music", "music_folder", "videos_folder", "stickers_folder",
    ]
    for k in global_keys:
        v = config["assets"].get(k)
        mark = "[OK]  " if v else "[SKIP]"
        name = Path(v).name if v else "no configurado"
        print(f"    {mark} {k:25s} -> {name}")

    print("\n  ASSETS DEL EPISODIO:")
    for k in ["episode_script", "episode_audio", "episode_pdf", "episode_log"]:
        v = config["assets"].get(k)
        mark = "[OK]  " if v else "[SKIP]"
        name = Path(v).name if v else "no configurado"
        print(f"    {mark} {k:25s} -> {name}")

    print("\n  OUTPUT:")
    print(f"    Carpeta:        {config['assets']['output_folder']}")
    print(f"    ID episodio:    {config['episode_defaults']['episode_id']}")
    print(f"    Resolucion:     {config['episode_defaults']['resolution']}")


def save_config(config: dict, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"\n  [OK] Configuracion guardada en: {config_path.resolve()}")


def run_setup_full() -> dict:
    print("\n" + "#" * 60)
    print("  MAQUINARIA PESADA - CONFIGURACION DEL PROYECTO")
    print("  Sistema de videopodcast automatizado v2.0")
    print("#" * 60 + "\n")
    print("  Este asistente te pedira la ubicacion de cada asset del proyecto.")
    print("  Solo necesitas hacer esto UNA VEZ. La config se guarda en")
    print("  project_config.json y se reutiliza automaticamente en todos los")
    print("  episodios futuros.\n")

    config = {
        "version": "2.0",
        "assets": {},
        "episode_defaults": {},
    }

    config = collect_global_assets(config)
    config = collect_episode_assets(config)
    config = collect_output_config(config)
    print_summary(config)

    print("\n" + "=" * 60)
    confirm = input("  Confirmar y guardar configuracion? [s/n]: ").strip().lower()
    if confirm not in ("s", "si", "y", "yes"):
        print("  [CANCELADO] Configuracion cancelada. Vuelve a ejecutar setup_project.py")
        sys.exit(0)

    config_path = Path(__file__).parent / "project_config.json"
    save_config(config, config_path)
    print(f"\n  [LISTO] Ahora ejecuta: python run_pipeline.py")
    print("\n" + "#" * 60 + "\n")
    return config


def run_setup_episode_only() -> dict:
    """Modo rapido: solo actualiza los assets del episodio actual."""
    config_path = Path(__file__).parent / "project_config.json"
    if not config_path.exists():
        print("[ERROR] No existe project_config.json. Ejecuta primero el setup completo:")
        print("        python setup_project.py")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    print("\n" + "#" * 60)
    print("  MAQUINARIA PESADA - ACTUALIZAR EPISODIO")
    print("  (Solo se actualizaran los assets del episodio actual)")
    print("#" * 60 + "\n")

    config = collect_episode_assets(config)

    print("\n" + "=" * 60)
    print("  ID DEL EPISODIO")
    print("  Actual:", config.get("episode_defaults", {}).get("episode_id", "EP-MOD000"))
    print("=" * 60)
    new_id = input("  Nuevo ID (ENTER para mantener): ").strip()
    if new_id:
        config.setdefault("episode_defaults", {})["episode_id"] = new_id

    print_summary(config)

    confirm = input("\n  Guardar cambios? [s/n]: ").strip().lower()
    if confirm not in ("s", "si", "y", "yes"):
        print("  [CANCELADO] No se han guardado los cambios.")
        sys.exit(0)

    save_config(config, config_path)
    print(f"\n  [LISTO] Ahora ejecuta: python run_pipeline.py")
    return config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Setup interactivo del videopodcast MaquinarIA Pesada"
    )
    parser.add_argument(
        "--episode-only",
        action="store_true",
        help="Solo actualizar assets del episodio (mantiene config global)",
    )
    args = parser.parse_args()

    if args.episode_only:
        run_setup_episode_only()
    else:
        run_setup_full()


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
        main()
