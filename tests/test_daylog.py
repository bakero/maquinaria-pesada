"""Tests de daylog.py — bitácora diaria con rotación de día-log a las 05:00."""
from __future__ import annotations

import sys
from datetime import datetime

import pytest

import daylog


@pytest.fixture(autouse=True)
def _isolated_log_dir(tmp_path, monkeypatch):
    """Aísla cada test en su propio logs/run/ vía DAYLOG_DIR."""
    monkeypatch.setenv("DAYLOG_DIR", str(tmp_path))
    return tmp_path


# ---- Frontera del día-log a las 05:00 ------------------------------------

@pytest.mark.parametrize(
    "hour, expected_day",
    [
        (4, 13),    # 04:xx -> pertenece al día-log anterior
        (0, 13),    # medianoche -> día-log anterior
        (5, 14),    # justo a las 05:00 -> día-log del propio día
        (5.5, 14),  # 05:30 -> día-log del propio día
        (23, 14),   # noche -> día-log del propio día
    ],
)
def test_log_day_boundary(hour, expected_day):
    now = datetime(2026, 5, 14, int(hour), int((hour % 1) * 60))
    assert daylog.log_day(now).day == expected_day


def test_log_path_uses_day_log_and_dir(tmp_path):
    now = datetime(2026, 5, 14, 4, 0)  # antes de las 05:00 -> fichero del día 13
    path = daylog.log_path(now)
    assert path.parent == tmp_path
    assert path.name == "maquinaria_2026-05-13.log"


# ---- Ciclo de ejecución: START / END -------------------------------------

def test_runlog_ok_writes_start_and_end():
    with daylog.RunLog(script="pilot.py", params=["--modulo", "3"],
                       capture_output=False) as log:
        log.info("paso intermedio", n=1)

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "[START]" in content
    assert "--modulo 3" in content
    assert "[INFO ]" in content and "paso intermedio" in content
    assert "[END  ]" in content and "status=ok" in content


def test_runlog_captures_real_exception():
    with pytest.raises(ValueError):
        with daylog.RunLog(script="pilot.py", capture_output=False):
            raise ValueError("boom")

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "[ERROR]" in content and "boom" in content
    assert "exc_type=ValueError" in content
    assert "status=error" in content


def test_runlog_systemexit_zero_is_ok():
    with pytest.raises(SystemExit):
        with daylog.RunLog(script="pilot.py", capture_output=False):
            raise SystemExit(0)

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "status=ok" in content
    assert "status=error" not in content


def test_runlog_systemexit_nonzero_is_error():
    with pytest.raises(SystemExit):
        with daylog.RunLog(script="pilot.py", capture_output=False):
            raise SystemExit("issues hard")

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "status=error" in content
    assert "issues hard" in content


def test_runs_share_single_daily_file():
    """Varias ejecuciones del mismo día-log escriben en el mismo fichero."""
    with daylog.RunLog(script="a.py", capture_output=False):
        pass
    with daylog.RunLog(script="b.py", capture_output=False):
        pass

    files = list(daylog.log_dir().iterdir())
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "script=a.py" in content and "script=b.py" in content


def test_logging_failure_never_raises(monkeypatch):
    """Un fallo al escribir se traga (stderr) y no rompe al llamador."""
    def _boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(daylog.Path, "mkdir", _boom)
    # No debe lanzar pese al fallo de escritura.
    with daylog.RunLog(script="pilot.py", capture_output=False) as log:
        log.info("esto no se escribe")


# ---- Captura de stdout/stderr --------------------------------------------

def test_capture_mirrors_stdout_and_stderr():
    with daylog.RunLog(script="pilot.py", capture_output=True):
        print("progreso del pipeline")
        print("algo fue mal", file=sys.stderr)

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "[OUT  ]" in content and "progreso del pipeline" in content
    assert "[ERR  ]" in content and "algo fue mal" in content


def test_capture_restores_streams_after_block():
    saved_out, saved_err = sys.stdout, sys.stderr
    with daylog.RunLog(script="pilot.py", capture_output=True):
        assert sys.stdout is not saved_out  # envuelto por el tee
    assert sys.stdout is saved_out
    assert sys.stderr is saved_err


def test_capture_restores_streams_even_on_error():
    saved_out = sys.stdout
    with pytest.raises(RuntimeError):
        with daylog.RunLog(script="pilot.py", capture_output=True):
            print("antes del fallo")
            raise RuntimeError("kaboom")
    assert sys.stdout is saved_out

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "antes del fallo" in content
    assert "kaboom" in content and "status=error" in content


def test_capture_disabled_does_not_mirror():
    with daylog.RunLog(script="pilot.py", capture_output=False):
        print("esto no debe espejarse")

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "esto no debe espejarse" not in content
    assert "[OUT  ]" not in content


# ---- Usabilidad: contadores, cap de línea, logger, visor -----------------

def test_end_line_reports_line_counts():
    with daylog.RunLog(script="pilot.py", capture_output=True):
        print("linea 1")
        print("linea 2")
        print("fallo", file=sys.stderr)

    end_line = [ln for ln in daylog.log_path().read_text(encoding="utf-8").splitlines()
                if "[END  ]" in ln][0]
    assert "out_lines=2" in end_line
    assert "err_lines=1" in end_line


def test_long_line_is_capped():
    with daylog.RunLog(script="pilot.py", capture_output=False) as log:
        log.info("x" * 5000)

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "…(+3000 chars)" in content


def test_get_logger_writes_correlated_with_active_run():
    with daylog.RunLog(script="pilot.py", capture_output=False) as run:
        daylog.get_logger("modulo_a").info("mensaje del módulo")
        run_id = run.run_id

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "[modulo_a] mensaje del módulo" in content
    assert f"run={run_id}" in content


def test_get_logger_without_active_run_uses_dash():
    daylog.get_logger("modulo_b").warning("aviso suelto")

    content = daylog.log_path().read_text(encoding="utf-8")
    assert "[WARN ]" in content and "aviso suelto" in content
    assert "run=-" in content


def test_get_logger_returns_standard_logger():
    log = daylog.get_logger("modulo_c", log_file="ignorado.log")
    assert hasattr(log, "info") and hasattr(log, "error") and hasattr(log, "debug")


def test_tail_returns_last_lines():
    with daylog.RunLog(script="pilot.py", capture_output=False) as log:
        for i in range(10):
            log.info(f"linea {i}")

    last = daylog.tail(3)
    assert len(last) == 3
    assert "[END  ]" in last[-1]
