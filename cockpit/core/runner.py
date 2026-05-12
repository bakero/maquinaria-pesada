"""Ejecutor de pipelines: subprocess.Popen con stdout streaming.

Pensado para uso desde Streamlit. La función `stream_pipeline` es un generador
que yields líneas de output según llegan, para volcarlas en la UI en vivo.

No persiste estado; el llamador es responsable de capturar el output y
registrarlo en log_parser / runlog si procede.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from . import paths


@dataclass
class RunResult:
    returncode: int
    cmd: list[str]
    duration_s: float


def build_argv(script: str, flags: list[tuple[str, Any]]) -> list[str]:
    """Convierte (script, flags) en argv listo para subprocess.

    Reglas idénticas a prompt_builder.build:
      - None / "" / False → omitir
      - True → flag sin valor
      - resto → flag + str(valor)
    """
    argv: list[str] = [sys.executable, script]
    for flag, value in flags:
        if value is None or value == "" or value is False:
            continue
        if value is True:
            argv.append(flag)
        else:
            argv.extend([flag, str(value)])
    return argv


def stream_pipeline(
    script: str,
    flags: list[tuple[str, Any]],
    *,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> Iterator[str | RunResult]:
    """Ejecuta `python script [...flags]` y yields líneas de stdout/stderr.

    El último valor cedido es siempre un RunResult con returncode.
    Mezcla stderr en stdout para no perder errores en streaming.
    """
    import os
    import time

    argv = build_argv(script, flags)
    cwd = cwd or str(paths.repo_root())
    full_env = {**os.environ, **(env or {})}

    started = time.monotonic()
    proc = subprocess.Popen(
        argv,
        cwd=cwd,
        env=full_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            yield line.rstrip("\n")
        proc.wait()
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()

    yield RunResult(
        returncode=proc.returncode,
        cmd=argv,
        duration_s=round(time.monotonic() - started, 2),
    )


def preview_command(script: str, flags: list[tuple[str, Any]]) -> str:
    """Vista humana del comando exacto que se ejecutaría."""
    argv = build_argv(script, flags)
    return " ".join(shlex.quote(a) for a in argv)
