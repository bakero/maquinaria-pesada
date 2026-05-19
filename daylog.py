"""Bitácora diaria de ejecuciones — punto único de logs de MaquinarIA Pesada.

Cada ejecución de un pipeline deja traza en un único fichero de texto por
"día-log". El día-log empieza a las 05:00: toda ejecución lanzada entre las
05:00 de un día y las 05:00 del siguiente escribe en el mismo fichero.

    logs/run/maquinaria_AAAA-MM-DD.log

Uso típico (context manager, recomendado):

    import sys
    from daylog import RunLog

    with RunLog(script="lanzar_produccion.py", params=sys.argv[1:]) as log:
        log.info("extrayendo conceptos", pdf="PDFs/M3.pdf")
        log.warn("reintento", intento=2)
        ...
    # al salir escribe END con status=ok|error + elapsed_s

Formato de línea (texto plano, legible):

    2026-05-14T10:30:00 [INFO ] run=a1b2c3 script=lanzar_produccion.py | mensaje k=v

Trazado completo sin tocar los pipelines
-----------------------------------------
Con `capture_output=True` (por defecto), mientras el context manager está
activo se espeja TODO lo que el script imprime: cada línea de `stdout` se
registra como nivel OUT y cada línea de `stderr` como ERR, sin dejar de
escribirse también en la consola real. Así los cientos de `print()` de
progreso, los errores capturados internamente y los tracebacks quedan en la
bitácora diaria sin reescribir una sola línea de los pipelines.

Logger por módulo
-----------------
`get_logger(name)` devuelve un `logging.Logger` estándar cuyas llamadas
`.info/.warning/.error/.debug` van al mismo fichero del día, correlacionadas
con el RunLog activo (campo `run=`). Es el único sistema de logging de la app:
sustituye a cualquier logger propio de los paquetes.

Visor
-----
`python daylog.py` imprime la ruta y las últimas líneas de la bitácora de hoy.

Diseño
------
- Append-only con flush por línea: varios procesos pueden escribir a la vez
  en el mismo fichero del día sin coordinarse.
- Rotación sin demonio: el fichero del día se resuelve en cada escritura, así
  un proceso largo que cruce las 05:00 pasa solo al fichero nuevo. Los procesos
  cortos (caso normal: ejecución bajo demanda) simplemente escriben en el
  fichero del día-log vigente al arrancar.
- Agnóstico de ubicación: resuelve el repo-root buscando hacia arriba (env
  REPO_ROOT o cwd), así funciona con los scripts sueltos y con los paquetes.
- Líneas con tope de longitud: una línea gigante no infla la bitácora.
- La línea END resume contadores `out_lines` / `err_lines` de la ejecución.
- Los fallos de logging nunca rompen al llamador (se vuelcan a stderr real).
- Sin dependencias: stdlib pura. Python 3.10+.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Hora a la que rota el fichero del día (hora local).
ROLL_HOUR = 5

_LEVELS = ("START", "INFO", "WARN", "ERROR", "OK", "END", "OUT", "ERR", "DEBUG")
_LOCK = threading.Lock()

# Si el buffer de una línea capturada crece sin salto de línea (p.ej. barras
# de progreso con \r), se vuelca igualmente al llegar a este tamaño.
_TEE_FLUSH_BYTES = 8192

# Tope de longitud por línea escrita: una línea gigante no infla la bitácora.
_MAX_LINE_CHARS = 2000

# RunLog activo en este proceso (lo usa get_logger para correlacionar con run=).
_ACTIVE_RUN: RunLog | None = None


def _repo_root() -> Path:
    """Repo-root para resolver `logs/run/`. Mirroring de `runlog.py`."""
    repo_root = os.environ.get("REPO_ROOT")
    return Path(repo_root) if repo_root else Path.cwd()


def log_dir() -> Path:
    """Directorio único donde viven los ficheros de bitácora diaria.

    Prioridad: env DAYLOG_DIR > REPO_ROOT/logs/run > cwd/logs/run.
    """
    custom = os.environ.get("DAYLOG_DIR")
    if custom:
        return Path(custom)
    return _repo_root() / "logs" / "run"


def log_day(now: datetime | None = None) -> datetime:
    """Fecha del día-log al que pertenece `now` (frontera a las ROLL_HOUR).

    Una ejecución a las 04:59 cuenta para el día-log anterior; a las 05:00,
    para el del propio día.
    """
    now = now or datetime.now()
    if now.hour < ROLL_HOUR:
        return now - timedelta(days=1)
    return now


def log_path(now: datetime | None = None) -> Path:
    """Ruta del fichero de bitácora para el día-log de `now`."""
    return log_dir() / f"maquinaria_{log_day(now):%Y-%m-%d}.log"


def _fmt_fields(fields: dict[str, Any]) -> str:
    """Serializa kwargs a ` k=v k2=v2` (vacío si no hay campos)."""
    if not fields:
        return ""
    parts = []
    for key, value in fields.items():
        text = str(value)
        if " " in text:
            text = f'"{text}"'
        parts.append(f"{key}={text}")
    return " " + " ".join(parts)


def _fmt_params(params: Any) -> str:
    """Normaliza los parámetros de ejecución a una cadena legible."""
    if params is None:
        return ""
    if isinstance(params, dict):
        return " ".join(f"{k}={v}" for k, v in params.items())
    if isinstance(params, (list, tuple)):
        return " ".join(str(p) for p in params)
    return str(params)


def _write_line(
    level: str, run_id: str, script: str, pid: int, msg: str, fields: dict[str, Any]
) -> None:
    """Escribe una línea en el fichero del día-log. Nunca propaga errores.

    Punto único de escritura: lo usan tanto `RunLog` como el logger por módulo.
    """
    try:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        body = f"{msg}{_fmt_fields(fields)}"
        if len(body) > _MAX_LINE_CHARS:
            body = f"{body[:_MAX_LINE_CHARS]}…(+{len(body) - _MAX_LINE_CHARS} chars)"
        line = f"{ts} [{level:<5}] run={run_id} script={script} pid={pid} | {body}\n"
        path = log_path()
        with _LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
    except Exception as exc:  # noqa: BLE001 - el logging jamás rompe al caller
        try:
            # __stderr__ es el stderr real: evita recursión si stderr está
            # envuelto por un _TeeStream.
            (sys.__stderr__ or sys.stderr).write(f"[daylog] write failed: {exc!r}\n")
        except Exception:  # noqa: BLE001
            pass


class _TeeStream:
    """Envoltura de stdout/stderr: escribe en la consola real y espeja cada
    línea completa en la bitácora vía `emit`. Cualquier fallo se ignora para
    no romper jamás un `print()` del pipeline.
    """

    def __init__(self, original: Any, emit: Any, level: str) -> None:
        self._original = original
        self._emit = emit
        self._level = level
        self._buf = ""

    def write(self, text: str) -> int:
        try:
            written = self._original.write(text)
        except Exception:  # noqa: BLE001
            written = len(text)
        try:
            self._buf += text
            while "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                if line.strip():
                    self._emit(self._level, line.rstrip("\r"))
            if len(self._buf) >= _TEE_FLUSH_BYTES:
                self._emit(self._level, self._buf.strip())
                self._buf = ""
        except Exception:  # noqa: BLE001 - el espejado jamás rompe al print()
            pass
        return written

    def flush(self) -> None:
        try:
            self._original.flush()
        except Exception:  # noqa: BLE001
            pass

    def drain(self) -> None:
        """Vuelca lo que quede en el buffer sin salto de línea final."""
        try:
            if self._buf.strip():
                self._emit(self._level, self._buf.strip())
            self._buf = ""
        except Exception:  # noqa: BLE001
            pass

    def __getattr__(self, name: str) -> Any:
        # isatty, fileno, encoding, etc. -> delegar en el stream real.
        return getattr(self._original, name)


class RunLog:
    """Bitácora de una ejecución concreta, volcada al fichero del día-log.

    Recomendado como context manager: emite una línea START al entrar (con los
    parámetros de ejecución) y una línea END al salir, con status=ok o
    status=error si escapó una excepción. `SystemExit` con código 0/None se
    considera ok; cualquier otro código, error.

    Con `capture_output=True` (por defecto) espeja además stdout/stderr en la
    bitácora mientras el bloque está activo (niveles OUT/ERR).
    """

    def __init__(
        self,
        script: str = "",
        params: Any = None,
        run_id: str | None = None,
        capture_output: bool = True,
    ) -> None:
        self.script = script or (Path(sys.argv[0]).name if sys.argv else "")
        self.params = params
        self.run_id = run_id or uuid.uuid4().hex[:6]
        self.pid = os.getpid()
        self.start_time = time.time()
        self.capture_output = capture_output
        self._saved_stdout: Any = None
        self._saved_stderr: Any = None
        self._out_lines = 0
        self._err_lines = 0

    # ---- Context manager -------------------------------------------------

    def __enter__(self) -> RunLog:
        global _ACTIVE_RUN
        self._emit("START", _fmt_params(self.params) or "(sin parámetros)")
        _ACTIVE_RUN = self
        if self.capture_output:
            self._install_capture()
        return self

    def _install_capture(self) -> None:
        """Sustituye stdout/stderr por tees que espejan en la bitácora."""
        try:
            self._saved_stdout = sys.stdout
            self._saved_stderr = sys.stderr
            sys.stdout = _TeeStream(self._saved_stdout, self._emit, "OUT")
            sys.stderr = _TeeStream(self._saved_stderr, self._emit, "ERR")
        except Exception:  # noqa: BLE001 - sin captura, el resto sigue igual
            self._restore_capture()

    def _restore_capture(self) -> None:
        """Restaura stdout/stderr y vuelca los buffers pendientes."""
        for attr, saved in (("stdout", self._saved_stdout), ("stderr", self._saved_stderr)):
            current = getattr(sys, attr, None)
            if isinstance(current, _TeeStream):
                current.drain()
            if saved is not None:
                setattr(sys, attr, saved)
        self._saved_stdout = None
        self._saved_stderr = None

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        global _ACTIVE_RUN
        if self.capture_output:
            self._restore_capture()
        elapsed = round(time.time() - self.start_time, 2)
        counts = {"elapsed_s": elapsed,
                  "out_lines": self._out_lines, "err_lines": self._err_lines}
        try:
            if exc_type is None:
                self._emit("END", "fin de ejecución", status="ok", **counts)
            elif exc_type is SystemExit:
                code = exc_val.code if exc_val is not None else None
                if code in (None, 0):
                    self._emit("END", "fin de ejecución", status="ok", **counts)
                else:
                    self._emit("END", "ejecución abortada", status="error",
                               code=code, **counts)
            else:
                # Excepción real: deja traza del error y cierra con status=error.
                self._emit(
                    "ERROR", str(exc_val)[:500],
                    exc_type=getattr(exc_type, "__name__", str(exc_type)),
                )
                self._emit(
                    "END", "ejecución con error", status="error",
                    exc_type=getattr(exc_type, "__name__", str(exc_type)), **counts,
                )
        finally:
            _ACTIVE_RUN = None
            # Auto-validación de la propia bitácora del run que acaba de cerrarse.
            # Si detecta inconsistencias, deja un WARN en el mismo día-log pero no
            # propaga errores (el contrato del logging es no-romper-al-caller).
            self._post_validate()

    def _post_validate(self) -> None:
        """Lanza `log_validator.validate_after_run` y registra el resultado.

        Opt-out vía env `DAYLOG_NO_AUTOVALIDATE=1` (útil en tests muy ajustados).
        """
        if os.environ.get("DAYLOG_NO_AUTOVALIDATE") == "1":
            return
        try:
            from cockpit.core.log_validator import validate_after_run

            report = validate_after_run(self.run_id)
            if report is None or report.ok and not report.warnings:
                return
            if report.issues:
                _write_line(
                    "WARN", self.run_id, self.script, self.pid,
                    "auto-validate: issues",
                    {"issues": "|".join(report.issues)[:300]},
                )
            if report.warnings:
                _write_line(
                    "INFO", self.run_id, self.script, self.pid,
                    "auto-validate: warnings",
                    {"warnings": "|".join(report.warnings)[:300]},
                )
        except Exception:  # noqa: BLE001 - jamás propagar
            pass

    # ---- API pública -----------------------------------------------------

    def info(self, msg: str, **fields: Any) -> None:
        self._emit("INFO", msg, **fields)

    def warn(self, msg: str, **fields: Any) -> None:
        self._emit("WARN", msg, **fields)

    def error(self, msg: str, **fields: Any) -> None:
        self._emit("ERROR", msg, **fields)

    def ok(self, msg: str, **fields: Any) -> None:
        self._emit("OK", msg, **fields)

    # ---- Internals -------------------------------------------------------

    def _emit(self, level: str, msg: str, **fields: Any) -> None:
        """Escribe una línea de esta ejecución y actualiza contadores."""
        if level in ("ERR", "ERROR"):
            self._err_lines += 1
        elif level == "OUT":
            self._out_lines += 1
        _write_line(level, self.run_id, self.script, self.pid, msg, fields)


# ---- Logger por módulo ---------------------------------------------------


class _DayLogHandler(logging.Handler):
    """Handler de `logging` que vuelca cada record en la bitácora diaria,
    correlacionado con el RunLog activo (campo `run=`) si lo hay.
    """

    _LEVEL_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARN",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "ERROR",
    }

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = self._LEVEL_MAP.get(record.levelno, "INFO")
            run = _ACTIVE_RUN
            if run is not None:
                run_id, script = run.run_id, run.script
                if level == "ERROR":
                    run._err_lines += 1
            else:
                run_id, script = "-", self._name
            _write_line(level, run_id, script, os.getpid(),
                        f"[{self._name}] {record.getMessage()}", {})
        except Exception:  # noqa: BLE001 - el logging jamás rompe al caller
            pass


def get_logger(
    name: str, level: int = logging.INFO, log_file: Any = None, **_ignored: Any
) -> logging.Logger:
    """Devuelve un `logging.Logger` que escribe en la bitácora diaria central.

    Es el único sistema de logging de la app: las llamadas `.info/.warning/
    .error/.debug` van al fichero del día, con el campo `run=` del RunLog activo.
    `log_file` y otros kwargs se aceptan por compatibilidad y se ignoran (todo
    va al log central).
    """
    logger = logging.getLogger(f"daylog.{name}")
    if not logger.handlers:
        logger.setLevel(level)
        logger.addHandler(_DayLogHandler(name))
        logger.propagate = False
    return logger


# ---- Visor ---------------------------------------------------------------


def tail(n: int = 40, now: datetime | None = None) -> list[str]:
    """Últimas `n` líneas de la bitácora del día-log de `now` (vacío si no hay)."""
    path = log_path(now)
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    except OSError:
        return []


if __name__ == "__main__":
    # Visor rápido: `python daylog.py` muestra la bitácora del día-log de hoy.
    _path = log_path()
    print(f"# bitácora del día-log: {_path}")
    _lines = tail(200)
    if _lines:
        for _ln in _lines:
            print(_ln)
    else:
        print("(aún sin entradas en este día-log)")
