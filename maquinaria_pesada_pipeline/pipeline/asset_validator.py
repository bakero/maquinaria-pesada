"""
Paso 00 - Validacion de assets.
Carga project_config.json y valida que todos los assets obligatorios existen.
"""

import json
import sys
from pathlib import Path

from .logger import get_logger

REQUIRED_ASSETS = [
    "logo_watermark",
    "intro_video",
    "sintonia_audio",
    "background_music",
    "episode_script",
    "episode_audio",
    "output_folder",
]

OPTIONAL_ASSETS = [
    "logos_folder",
    "music_folder",
    "videos_folder",
    "stickers_folder",
    "episode_pdf",
    "episode_log",
]


def validate_project_config(config_path: str | Path = "project_config.json") -> dict:
    """
    Carga project_config.json y valida que todos los assets obligatorios
    siguen existiendo en sus rutas originales.
    Si falta alguno, muestra el error especifico y detiene la ejecucion.
    """
    log = get_logger("asset_validator")
    config_path = Path(config_path)

    if not config_path.exists():
        log.error("No se encontro project_config.json")
        log.error("Ejecuta primero: python setup_project.py")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    errors = []
    for asset_key in REQUIRED_ASSETS:
        path = config.get("assets", {}).get(asset_key)
        if not path:
            errors.append(f"Asset no configurado: {asset_key}")
        elif not Path(path).exists():
            errors.append(f"Archivo no encontrado: {asset_key} -> {path}")

    if errors:
        log.error("ERRORES DE VALIDACION DE ASSETS:")
        for e in errors:
            log.error(f"  - {e}")
        log.error("Ejecuta: python setup_project.py para reconfigurar.")
        sys.exit(1)

    # Avisos para opcionales
    for asset_key in OPTIONAL_ASSETS:
        path = config.get("assets", {}).get(asset_key)
        if path and not Path(path).exists():
            log.warning(f"Asset opcional no encontrado: {asset_key} -> {path}")

    # Asegurar carpetas de output
    output_folder = Path(config["assets"]["output_folder"])
    (output_folder / "logs").mkdir(parents=True, exist_ok=True)
    (output_folder / "clips").mkdir(parents=True, exist_ok=True)
    (output_folder / "frames_cache").mkdir(parents=True, exist_ok=True)

    log.info("Todos los assets validados correctamente")
    return config


if __name__ == "__main__":
    cfg = validate_project_config()
    print(json.dumps(cfg, indent=2, ensure_ascii=False))
