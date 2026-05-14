"""Puente al sistema único de logs de la app (`daylog.py` en la raíz del repo).

Histórico: este módulo configuraba su propio `logging` (consola + fichero).
Ya no: la app tiene una sola bitácora central (`daylog`). Este fichero solo
resuelve el path de `daylog` y reexporta `get_logger`, para no romper los
imports existentes `from .logger import get_logger` y
`from pipeline.logger import get_logger`.

`get_logger(name)` devuelve un `logging.Logger` estándar cuyas llamadas
`.info/.warning/.error/.debug` van al fichero del día-log, correlacionadas con
el RunLog activo (campo `run=`).
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

# Asegura que la raíz del repo (donde vive daylog.py) es importable, tanto si
# el paquete se ejecuta suelto como si lo importa la cockpit.
for _p in _Path(__file__).resolve().parents:
    if (_p / "daylog.py").exists():
        if str(_p) not in _sys.path:
            _sys.path.insert(0, str(_p))
        break

from daylog import get_logger  # noqa: E402

__all__ = ["get_logger"]
