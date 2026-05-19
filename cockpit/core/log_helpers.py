"""Helpers de logging granular para generadores y pipelines.

Centraliza el patrón "log step + AI call + retry" sobre `daylog.RunLog` para
que cualquier generador pueda emitir trazas estructuradas sin acoplarse al
RunLog activo.

Uso típico desde un generador::

    from cockpit.core.log_helpers import get_run_logger

    log = get_run_logger("generar_guion")
    log.step("extract_concepts", pdf=str(pdf_path))
    with log.ai_call(model=gen_model, purpose="extract_concepts",
                     source="generar_guion.py") as call:
        text, resp = client.messages.create(...)
        call.set_tokens(in_=resp.usage.input_tokens,
                        out_=resp.usage.output_tokens)
    log.retry(attempt=2, reason="hard_fails", count=4)
    log.ok("guion guardado", path=str(out))

Si no hay `RunLog` activo (script invocado sin envoltura), los mensajes
siguen escribiéndose en el fichero del día con `run=-`, como hace
`daylog._DayLogHandler`.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Any

import daylog


class RunLogger:
    """Fachada uniforme sobre `daylog.RunLog` para uso en funciones.

    Métodos:
      - `info(msg, **fields)` / `warn` / `error` / `ok`: equivalentes a los del
        `RunLog` activo (o caída a escritura directa si no hay).
      - `step(name, **fields)`: marca el inicio de un paso mayor (INFO con
        prefijo "paso → name").
      - `retry(attempt, reason, **fields)`: marca un reintento (WARN).
      - `ai_call(...)`: context manager que mide latencia y permite anotar
        tokens/coste; emite INFO al entrar y OK/ERROR al salir.

    Cada línea lleva el campo `module=<name>` para correlacionar con el
    generador concreto cuando varios escriben en el mismo día-log.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    # ---- emisión interna ----------------------------------------------------

    def _emit(self, level: str, msg: str, **fields: Any) -> None:
        run = daylog._ACTIVE_RUN  # noqa: SLF001 - punto único documentado
        body = f"[{self.name}] {msg}"
        if run is not None:
            run_method = {
                "INFO": run.info,
                "WARN": run.warn,
                "ERROR": run.error,
                "OK": run.ok,
            }.get(level, run.info)
            run_method(body, **fields)
        else:
            # Sin RunLog: vuelca igualmente para no perder traza.
            daylog._write_line(  # noqa: SLF001
                level, "-", self.name, os.getpid(), body, fields
            )

    # ---- API pública --------------------------------------------------------

    def info(self, msg: str, **fields: Any) -> None:
        self._emit("INFO", msg, **fields)

    def warn(self, msg: str, **fields: Any) -> None:
        self._emit("WARN", msg, **fields)

    def error(self, msg: str, **fields: Any) -> None:
        self._emit("ERROR", msg, **fields)

    def ok(self, msg: str, **fields: Any) -> None:
        self._emit("OK", msg, **fields)

    def step(self, name: str, **fields: Any) -> None:
        """Marca el inicio de un paso mayor del pipeline."""
        self._emit("INFO", f"paso → {name}", step=name, **fields)

    def retry(self, attempt: int, reason: str, **fields: Any) -> None:
        """Marca un reintento de operación (típicamente IA)."""
        self._emit("WARN", "retry", attempt=attempt, reason=reason, **fields)

    @contextmanager
    def ai_call(
        self,
        model: str,
        purpose: str,
        source: str | None = None,
        **extra: Any,
    ):
        """Context manager para una llamada a IA.

        Emite INFO al entrar (modelo, purpose, source) y OK/ERROR al salir con
        latencia en ms y, si se anotaron, `tokens_in`/`tokens_out`/`cost_usd`.

        Uso::
            with log.ai_call(model="claude-sonnet-4-5",
                             purpose="generate_block", source="generar_guion.py") as call:
                resp = client.messages.create(...)
                call.set_tokens(in_=resp.usage.input_tokens,
                                out_=resp.usage.output_tokens)
        """
        call = _AICall(
            self, model=model, purpose=purpose, source=source, **extra
        )
        call.start()
        try:
            yield call
        except Exception as exc:
            call.finish_error(exc)
            raise
        else:
            call.finish_ok()


class _AICall:
    """Estado de una llamada a IA en curso, devuelto por `RunLogger.ai_call`."""

    def __init__(
        self,
        logger: RunLogger,
        *,
        model: str,
        purpose: str,
        source: str | None = None,
        **extra: Any,
    ) -> None:
        self.logger = logger
        self.fields: dict[str, Any] = {"model": model, "purpose": purpose}
        if source:
            self.fields["source"] = source
        self.fields.update(extra)
        self.tokens_in: int | None = None
        self.tokens_out: int | None = None
        self.cost_usd: float | None = None
        self._t0 = 0.0

    def start(self) -> None:
        self._t0 = time.monotonic()
        self.logger._emit(  # noqa: SLF001 - misma jerarquía
            "INFO", f"AI call → {self.fields['purpose']}", **self.fields
        )

    def set_tokens(self, in_: int | None = None, out_: int | None = None) -> None:
        if in_ is not None:
            self.tokens_in = int(in_)
        if out_ is not None:
            self.tokens_out = int(out_)

    def set_cost_usd(self, value: float) -> None:
        self.cost_usd = float(value)

    def _result_fields(self) -> dict[str, Any]:
        fields = dict(self.fields)
        fields["ms"] = int((time.monotonic() - self._t0) * 1000)
        if self.tokens_in is not None:
            fields["tokens_in"] = self.tokens_in
        if self.tokens_out is not None:
            fields["tokens_out"] = self.tokens_out
        if self.cost_usd is not None:
            fields["cost_usd"] = round(self.cost_usd, 4)
        return fields

    def finish_ok(self) -> None:
        self.logger._emit(  # noqa: SLF001
            "OK", f"AI call ok → {self.fields['purpose']}", **self._result_fields()
        )

    def finish_error(self, exc: BaseException) -> None:
        fields = self._result_fields()
        fields["exc_type"] = type(exc).__name__
        self.logger._emit(  # noqa: SLF001
            "ERROR", f"AI call error → {self.fields['purpose']}", **fields
        )


# ---- API de módulo -------------------------------------------------------


def get_run_logger(name: str) -> RunLogger:
    """Devuelve un `RunLogger` para el módulo `name`.

    Crea uno nuevo en cada llamada (los `RunLogger` son baratos y stateless,
    no hay caché para evitar dependencias del orden de import).
    """
    return RunLogger(name)
