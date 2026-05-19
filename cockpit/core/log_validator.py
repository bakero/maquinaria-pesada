"""Validador de bitácoras diarias de `daylog`.

Lee el fichero del día-log (`logs/run/maquinaria_YYYY-MM-DD.log`) y verifica
para cada `run_id` que su ejecución quedó correctamente trazada:

  - Existen líneas START y END.
  - `status` final es `ok` o `error` (no falta y no es valor inesperado).
  - El número de ERROR es coherente con `status` (≥1 si error, 0 si ok salvo
    si el llamador lo ha justificado).
  - El elapsed_s es positivo.
  - (Opcional) contiene los pasos esperados por script.

No bloquea ninguna ejecución. Se usa:

  - Como módulo: `validate_day(date)` / `validate_run(record)` desde tests
    o desde `evaluador/cli.py --check-run-log`.
  - Como auto-validación: `daylog.RunLog.__exit__` invoca a
    `validate_after_run(run_id)` si el bloque cerró ok, y deja un WARN si
    detecta inconsistencias en la propia bitácora.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

import daylog

# Línea estándar de la bitácora:
#   2026-05-18T10:30:00 [INFO ] run=a1b2c3 script=foo.py pid=1234 | mensaje k=v
LINE_REGEX = re.compile(
    r"^(?P<ts>\S+)\s+\[(?P<level>[A-Z]+)\s*\]\s+"
    r"run=(?P<run>\S+)\s+"
    r"script=(?P<script>\S+)\s+"
    r"pid=(?P<pid>\d+)\s+\|\s+(?P<body>.*)$"
)

# Pasos esperados por script (heurística suave; ausencia = WARN, no ERROR).
# Cada entrada lista pasos que DEBEN aparecer al menos una vez en INFO con el
# prefijo "paso → ".
EXPECTED_STEPS: dict[str, list[str]] = {
    "generar_guion.py": ["load_spec", "extract_concepts", "generate", "validate", "save"],
    "generar_guion_t.py": ["load_spec", "extract_concepts", "generate", "validate", "save"],
    "generar_episodio_v2.py": ["load_script", "audio", "render"],
    "validar_episodio.py": ["load_script", "validate"],
    "produce_pending.py": ["scan_pending", "produce"],
    "lanzar_produccion_v6.py": ["plan", "produce"],
    "entrenar_v6.py": ["iterate"],
    "dual_debate.py": ["debate"],
    "evaluador/cli.py": ["discover", "evaluate"],
    "maquinaria_pesada_pipeline/run_pipeline.py": ["plan", "execute"],
}


@dataclass
class RunRecord:
    """Resumen parseado de un `run_id` extraído del día-log."""

    run_id: str
    script: str
    pid: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: str | None = None
    exit_code: str | None = None
    elapsed_s: float | None = None
    out_lines: int | None = None
    err_lines: int | None = None
    level_counts: dict[str, int] = field(default_factory=dict)
    steps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    retries: int = 0
    ai_calls_started: int = 0
    ai_calls_ok: int = 0
    ai_calls_error: int = 0


@dataclass
class RunReport:
    """Resultado de validar un `RunRecord`."""

    run: RunRecord
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict:
        return {
            "run_id": self.run.run_id,
            "script": self.run.script,
            "status": self.run.status,
            "elapsed_s": self.run.elapsed_s,
            "ai_calls": {
                "started": self.run.ai_calls_started,
                "ok": self.run.ai_calls_ok,
                "error": self.run.ai_calls_error,
            },
            "retries": self.run.retries,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "ok": self.ok,
        }


# ---- Parser ----------------------------------------------------------------


def _parse_ts(text: str) -> datetime | None:
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_fields(body: str) -> dict[str, str]:
    """Extrae k=v del cuerpo de una línea. Tolerante con valores entre comillas."""
    out: dict[str, str] = {}
    # k="v con espacios" | k=v
    pattern = re.compile(r'(\w+)=(?:"([^"]*)"|(\S+))')
    for m in pattern.finditer(body):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return out


def parse_log(path: Path) -> dict[str, RunRecord]:
    """Parsea un fichero de día-log y devuelve {run_id: RunRecord}."""
    runs: dict[str, RunRecord] = {}
    if not path.exists():
        return runs
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        m = LINE_REGEX.match(line)
        if not m:
            continue
        run_id = m["run"]
        if run_id == "-":
            # Sin RunLog activo; no es una ejecución completa, lo saltamos.
            continue
        rec = runs.get(run_id)
        if rec is None:
            rec = RunRecord(run_id=run_id, script=m["script"], pid=int(m["pid"]))
            runs[run_id] = rec
        level = m["level"].strip()
        rec.level_counts[level] = rec.level_counts.get(level, 0) + 1
        body = m["body"]
        fields = _parse_fields(body)

        if level == "START":
            rec.started_at = _parse_ts(m["ts"])
        elif level == "END":
            rec.ended_at = _parse_ts(m["ts"])
            rec.status = fields.get("status")
            rec.exit_code = fields.get("code")
            rec.elapsed_s = (
                float(fields["elapsed_s"]) if "elapsed_s" in fields else None
            )
            rec.out_lines = (
                int(fields["out_lines"]) if "out_lines" in fields else None
            )
            rec.err_lines = (
                int(fields["err_lines"]) if "err_lines" in fields else None
            )
        elif level == "ERROR":
            rec.errors.append(body[:300])
            if "AI call error" in body:
                rec.ai_calls_error += 1
        elif level == "WARN":
            if body.startswith("[") and "retry" in body:
                rec.retries += 1
        elif level == "INFO":
            if "paso →" in body or "paso →" in body:
                step = fields.get("step")
                if step:
                    rec.steps.append(step)
            if "AI call →" in body:
                rec.ai_calls_started += 1
        elif level == "OK":
            if "AI call ok" in body:
                rec.ai_calls_ok += 1
    return runs


# ---- Validación ------------------------------------------------------------


def validate_run(
    record: RunRecord, expected_steps: list[str] | None = None
) -> RunReport:
    """Aplica las reglas de coherencia mínimas a un `RunRecord`."""
    issues: list[str] = []
    warnings: list[str] = []

    if record.started_at is None:
        issues.append("falta línea START")
    if record.ended_at is None:
        issues.append("falta línea END (ejecución no cerró)")

    if record.status not in ("ok", "error", None):
        issues.append(f"status inválido: {record.status!r}")

    if record.status == "error":
        issues.append(
            "ejecución terminó en error"
            + (f" (code={record.exit_code})" if record.exit_code else "")
        )

    if record.elapsed_s is not None and record.elapsed_s < 0:
        issues.append(f"elapsed_s inválido: {record.elapsed_s}")

    # AI calls iniciadas pero no cerradas
    pending = record.ai_calls_started - record.ai_calls_ok - record.ai_calls_error
    if pending > 0:
        warnings.append(f"{pending} llamadas IA sin OK/ERROR final")

    # Pasos esperados (heurística suave)
    if expected_steps is None:
        # script en el log puede llevar prefijo de carpeta o no
        expected_steps = EXPECTED_STEPS.get(record.script, [])
        if not expected_steps:
            # probar buscando por basename
            bn = Path(record.script).name
            expected_steps = EXPECTED_STEPS.get(bn, [])
    if expected_steps:
        present = set(record.steps)
        missing = [s for s in expected_steps if s not in present]
        if missing:
            warnings.append(f"pasos esperados ausentes: {', '.join(missing)}")

    return RunReport(run=record, issues=issues, warnings=warnings)


def validate_day(date_obj: date | None = None) -> dict[str, RunReport]:
    """Valida todos los runs del día-log que contiene `date_obj` (hoy si None).

    `date_obj` es la fecha del día-log (no la fecha calendario): un día-log
    arranca a las 05:00 y termina a las 04:59 del día siguiente.
    """
    if date_obj is None:
        now = datetime.now()
    else:
        # Usar mediodía para que `log_path` resuelva sin ambigüedad.
        now = datetime.combine(date_obj, datetime.min.time()) + timedelta(hours=12)
    path = daylog.log_path(now)
    runs = parse_log(path)
    return {rid: validate_run(rec) for rid, rec in runs.items()}


def validate_after_run(run_id: str) -> RunReport | None:
    """Valida una ejecución concreta justo después de cerrar (hot path).

    Se invoca desde `daylog.RunLog.__exit__` (si la integración está activa).
    No lanza excepciones — devuelve `None` si no encuentra el run en el log.
    """
    try:
        path = daylog.log_path()
        runs = parse_log(path)
        rec = runs.get(run_id)
        if rec is None:
            return None
        return validate_run(rec)
    except Exception:  # noqa: BLE001 - jamás romper al caller del RunLog
        return None
