"""Tests de cockpit.core.log_helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

import daylog
from cockpit.core import log_helpers


@pytest.fixture
def tmp_daylog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirige los logs a un directorio temporal."""
    monkeypatch.setenv("DAYLOG_DIR", str(tmp_path))
    yield tmp_path


def _read_log(daylog_dir: Path) -> str:
    files = list(daylog_dir.glob("maquinaria_*.log"))
    if not files:
        return ""
    return files[0].read_text(encoding="utf-8")


def test_basic_emit_without_runlog(tmp_daylog: Path):
    log = log_helpers.get_run_logger("test_module")
    log.info("hola", clave="valor")
    log.warn("ojo")
    log.error("falló", code=42)
    log.ok("listo")
    text = _read_log(tmp_daylog)
    assert "[test_module] hola" in text
    assert "clave=valor" in text
    assert "[INFO ]" in text
    assert "[WARN ]" in text
    assert "[ERROR]" in text
    assert "[OK   ]" in text


def test_emit_inside_runlog(tmp_daylog: Path):
    with daylog.RunLog(script="test.py", capture_output=False):
        log = log_helpers.get_run_logger("test_mod")
        log.info("dentro", n=1)
    text = _read_log(tmp_daylog)
    # La línea de log_helpers debe llevar el mismo run_id que START/END
    lines = [ln for ln in text.splitlines() if "[test_mod]" in ln]
    assert lines, "no se encontró línea del logger"
    # extraer run= de cualquier línea
    run_ids = set()
    for ln in text.splitlines():
        if "run=" in ln:
            run_ids.add(ln.split("run=")[1].split()[0])
    # Solo debe haber un run_id (sin '-' porque hubo RunLog activo)
    assert "-" not in run_ids
    assert len(run_ids) == 1


def test_step_emits_with_prefix(tmp_daylog: Path):
    log = log_helpers.get_run_logger("genX")
    log.step("extract_concepts", pdf="foo.pdf")
    text = _read_log(tmp_daylog)
    assert "paso → extract_concepts" in text
    assert "step=extract_concepts" in text
    assert "pdf=foo.pdf" in text


def test_retry_emits_warn(tmp_daylog: Path):
    log = log_helpers.get_run_logger("genX")
    log.retry(attempt=2, reason="hard_fails", count=4)
    text = _read_log(tmp_daylog)
    assert "[WARN " in text
    assert "retry" in text
    assert "attempt=2" in text
    assert "reason=hard_fails" in text


def test_ai_call_ok(tmp_daylog: Path):
    log = log_helpers.get_run_logger("genX")
    with log.ai_call(
        model="claude-sonnet-4-6", purpose="extract", source="test.py"
    ) as call:
        call.set_tokens(in_=1234, out_=567)
        call.set_cost_usd(0.0042)
    text = _read_log(tmp_daylog)
    assert "AI call → extract" in text
    assert "AI call ok → extract" in text
    assert "tokens_in=1234" in text
    assert "tokens_out=567" in text
    assert "cost_usd=0.0042" in text
    # ms debe estar presente y ser entero
    ok_line = next(ln for ln in text.splitlines() if "AI call ok" in ln)
    assert "ms=" in ok_line


def test_ai_call_error_propagates(tmp_daylog: Path):
    log = log_helpers.get_run_logger("genX")
    with pytest.raises(RuntimeError, match="boom"):
        with log.ai_call(model="m", purpose="p"):
            raise RuntimeError("boom")
    text = _read_log(tmp_daylog)
    assert "AI call error → p" in text
    assert "exc_type=RuntimeError" in text


def test_logger_falls_back_to_dash_run(tmp_daylog: Path):
    """Sin RunLog activo, escribe con run=- y no peta."""
    assert daylog._ACTIVE_RUN is None
    log = log_helpers.get_run_logger("solo")
    log.info("sin contexto")
    text = _read_log(tmp_daylog)
    assert "run=-" in text
    assert "[solo] sin contexto" in text
