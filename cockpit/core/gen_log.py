"""Traza de generación/validación de guiones por episodio.

`generar_guion.py` / `generar_guion_t.py` imprimen a stdout su bucle de
validación y regeneración. Cuando la generación se lanza desde la app
(web_server) o desde `lanzar_guiones.py`, esa salida se redirige a una ruta
determinista: `Guiones/logs/{ep_id}_gen.log`.

Este módulo centraliza dónde vive esa traza y cómo se parsea — para que
`web_server.py` se quede como capa fina de routing.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import paths

# Marcadores que imprime el bucle de generación (ver generar_guion.py)
_ATTEMPT_RE = re.compile(r"Generando guion \(intento \d+/")
_HARD_RE = re.compile(r"\[HARD\]\s*(.+)")
_SOFT_RE = re.compile(r"\[WARN\]\s*(.+)")
_PASS = "[PASS] Validacion OK"
_EXHAUSTED = "Superado máximo de intentos"
_SAVED = "GUION GENERADO"


def gen_log_path(ep_id: str) -> Path:
    """Ruta determinista de la traza de un episodio.

    Misma convención que lanzar_guiones.py: `Guiones/logs/{ep_id}_gen.log`."""
    return paths.guiones_dir() / "logs" / f"{ep_id}_gen.log"


def parse_gen_log(text: str) -> dict:
    """Extrae un resumen estructurado de la traza: intentos, issues hard/soft
    y veredicto (ok | warn | running)."""
    attempts = len(_ATTEMPT_RE.findall(text))
    hard = [m.group(1).strip() for m in _HARD_RE.finditer(text)]
    soft = [m.group(1).strip() for m in _SOFT_RE.finditer(text)]
    passed = _PASS in text
    exhausted = _EXHAUSTED in text
    saved = _SAVED in text

    if passed:
        verdict = "ok"
    elif saved and exhausted:
        verdict = "warn"        # guardó el mejor intento con issues
    elif saved:
        verdict = "ok"
    else:
        verdict = "running"     # aún sin línea final de guardado

    return {
        "verdict": verdict,
        "attempts": attempts,
        "hard_issues": hard,
        "soft_issues": soft,
        "saved": saved,
    }


def read(ep_id: str) -> dict:
    """Lee y parsea la traza de un episodio.

    Devuelve el texto crudo + el resumen estructurado, o `exists: False` si
    todavía no se ha lanzado ninguna generación."""
    log_path = gen_log_path(ep_id)
    if not log_path.exists():
        return {"ok": False, "ep_id": ep_id, "exists": False,
                "error": "sin traza de generación todavía"}

    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"ok": False, "ep_id": ep_id, "exists": True, "error": str(exc)}

    return {
        "ok": True,
        "ep_id": ep_id,
        "exists": True,
        **parse_gen_log(text),
        "mtime": log_path.stat().st_mtime,
        "text": text,
    }
