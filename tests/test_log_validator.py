"""Tests de cockpit.core.log_validator."""

from __future__ import annotations

from pathlib import Path

import pytest

import daylog
from cockpit.core import log_helpers, log_validator


@pytest.fixture
def tmp_daylog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DAYLOG_DIR", str(tmp_path))
    return tmp_path


def _today_log_path(daylog_dir: Path) -> Path:
    return daylog_dir / f"maquinaria_{daylog.log_day():%Y-%m-%d}.log"


def test_parse_log_extracts_run_record(tmp_daylog: Path):
    with daylog.RunLog(script="generar_guion.py", params=["--modulo", "3"], capture_output=False):
        log = log_helpers.get_run_logger("generar_guion")
        log.step("extract_concepts")
        log.step("generate")
    path = _today_log_path(tmp_daylog)
    runs = log_validator.parse_log(path)
    assert len(runs) == 1
    rec = next(iter(runs.values()))
    assert rec.script == "generar_guion.py"
    assert rec.status == "ok"
    assert rec.started_at is not None and rec.ended_at is not None
    assert "extract_concepts" in rec.steps
    assert "generate" in rec.steps


def test_validate_run_clean(tmp_daylog: Path):
    with daylog.RunLog(script="x.py", capture_output=False):
        pass
    runs = log_validator.parse_log(_today_log_path(tmp_daylog))
    rec = next(iter(runs.values()))
    report = log_validator.validate_run(rec)
    assert report.ok, report.issues


def test_validate_detects_error_status(tmp_daylog: Path):
    try:
        with daylog.RunLog(script="x.py", capture_output=False):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    runs = log_validator.parse_log(_today_log_path(tmp_daylog))
    rec = next(iter(runs.values()))
    report = log_validator.validate_run(rec)
    assert not report.ok
    assert any("error" in i.lower() for i in report.issues)


def test_validate_detects_systemexit_nonzero(tmp_daylog: Path):
    try:
        with daylog.RunLog(script="x.py", capture_output=False):
            raise SystemExit(2)
    except SystemExit:
        pass
    runs = log_validator.parse_log(_today_log_path(tmp_daylog))
    rec = next(iter(runs.values()))
    assert rec.status == "error"
    assert rec.exit_code == "2"
    report = log_validator.validate_run(rec)
    assert not report.ok


def test_ai_calls_are_counted(tmp_daylog: Path):
    with daylog.RunLog(script="g.py", capture_output=False):
        log = log_helpers.get_run_logger("g")
        with log.ai_call(model="m", purpose="p1"):
            pass
        with log.ai_call(model="m", purpose="p2") as c:
            c.set_tokens(in_=10, out_=20)
        try:
            with log.ai_call(model="m", purpose="p3"):
                raise RuntimeError("nope")
        except RuntimeError:
            pass
    runs = log_validator.parse_log(_today_log_path(tmp_daylog))
    rec = next(iter(runs.values()))
    assert rec.ai_calls_started == 3
    assert rec.ai_calls_ok == 2
    assert rec.ai_calls_error == 1


def test_retries_counted(tmp_daylog: Path):
    with daylog.RunLog(script="g.py", capture_output=False):
        log = log_helpers.get_run_logger("g")
        log.retry(attempt=2, reason="hard_fails")
        log.retry(attempt=3, reason="hard_fails")
    runs = log_validator.parse_log(_today_log_path(tmp_daylog))
    rec = next(iter(runs.values()))
    assert rec.retries == 2


def test_expected_steps_warning(tmp_daylog: Path):
    """Si faltan pasos esperados, emite warning (no issue)."""
    with daylog.RunLog(script="generar_guion.py", capture_output=False):
        # No emitimos NINGUN paso de los esperados
        pass
    runs = log_validator.parse_log(_today_log_path(tmp_daylog))
    rec = next(iter(runs.values()))
    report = log_validator.validate_run(rec)
    assert report.ok  # no es issue, solo warning
    assert any("pasos esperados ausentes" in w for w in report.warnings)


def test_validate_day_returns_per_run(tmp_daylog: Path):
    with daylog.RunLog(script="a.py", capture_output=False):
        pass
    with daylog.RunLog(script="b.py", capture_output=False):
        pass
    reports = log_validator.validate_day()
    assert len(reports) == 2
    assert all(r.ok for r in reports.values())


def test_validate_after_run_returns_report(tmp_daylog: Path):
    run = daylog.RunLog(script="x.py", capture_output=False)
    with run:
        pass
    report = log_validator.validate_after_run(run.run_id)
    assert report is not None
    assert report.ok


def test_validate_after_run_missing_returns_none(tmp_daylog: Path):
    assert log_validator.validate_after_run("ffffff") is None
