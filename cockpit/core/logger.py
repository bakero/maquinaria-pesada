"""Logging estructurado JSON para la cockpit.

Sustituye `print()` por entries JSON con timestamp + level + correlation_id.
Pensado para que cualquier ejecución de pipeline pueda correlar todas sus
líneas vía un único `correlation_id` (e.g. el id de episodio).

Uso típico:

    from cockpit.core import logger as L

    L.bind(correlation_id="M3_T_ML_001", pipeline="generar_guion")
    L.info("start", pdf="PDFs/M3_T_ML.pdf")
    L.warn("retry", reason="429", attempt=2)
    L.error("fail", exc="ConnectionError")

Output (a stdout):
    {"ts": "2026-05-12T15:00:00", "level": "info", "msg": "start",
     "correlation_id": "M3_T_ML_001", "pipeline": "generar_guion",
     "pdf": "PDFs/M3_T_ML.pdf"}

El binding es por hilo (via contextvars), así varias ejecuciones simultáneas
no se mezclan.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any

_BOUND: ContextVar[dict[str, Any] | None] = ContextVar("_logger_bound", default=None)
_HANDLER_INSTALLED = False


def _get_bound() -> dict[str, Any]:
    """Devuelve el dict de bindings actual (vacío si nunca se llamó a bind)."""
    return _BOUND.get() or {}


def _ensure_handler() -> None:
    global _HANDLER_INSTALLED
    if _HANDLER_INSTALLED:
        return
    root = logging.getLogger("maquinaria")
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    # Evitar handlers duplicados si el módulo se recarga.
    root.handlers = [handler]
    root.propagate = False
    _HANDLER_INSTALLED = True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
        }
        # Bindings (correlation_id, pipeline, etc.)
        bound = getattr(record, "_bound", {})
        payload.update(bound)
        # Extras (kwargs por línea)
        extras = getattr(record, "_extras", {})
        payload.update(extras)
        return json.dumps(payload, ensure_ascii=False, default=str)


def bind(**ctx: Any) -> None:
    """Asocia campos al contexto actual. Sobrescribe claves repetidas."""
    current = dict(_get_bound())
    current.update(ctx)
    _BOUND.set(current)


def unbind(*keys: str) -> None:
    current = dict(_get_bound())
    for k in keys:
        current.pop(k, None)
    _BOUND.set(current)


def clear() -> None:
    _BOUND.set(None)


def _log(level: int, msg: str, **fields: Any) -> None:
    _ensure_handler()
    logger = logging.getLogger("maquinaria")
    extra = {"_bound": dict(_get_bound()), "_extras": fields}
    logger.log(level, msg, extra=extra)


def info(msg: str, **fields: Any) -> None:
    _log(logging.INFO, msg, **fields)


def warn(msg: str, **fields: Any) -> None:
    _log(logging.WARNING, msg, **fields)


def error(msg: str, **fields: Any) -> None:
    _log(logging.ERROR, msg, **fields)


def debug(msg: str, **fields: Any) -> None:
    _log(logging.DEBUG, msg, **fields)


def with_correlation(correlation_id: str, **extra: Any):
    """Context manager que asocia correlation_id durante un bloque.

    Uso:
        with logger.with_correlation("M3_T_ML_001", pipeline="audio"):
            logger.info("start")
            ...
    """
    from contextlib import contextmanager

    @contextmanager
    def _cm():
        token = _BOUND.set({**_get_bound(), "correlation_id": correlation_id, **extra})
        try:
            yield
        finally:
            _BOUND.reset(token)

    return _cm()
