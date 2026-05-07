"""Logger compartido para todos los pasos del pipeline."""

import logging
import sys
from pathlib import Path


def get_logger(name: str, log_file: Path | str | None = None,
               level: int = logging.INFO) -> logging.Logger:
    """
    Devuelve un logger configurado con handlers de consola y archivo.
    Si ya estaba configurado, lo reutiliza sin duplicar handlers.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    logger.propagate = False
    return logger
