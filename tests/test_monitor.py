"""Tests del monitor de procesos. No depende de psutil para los unitarios puros."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import monitor  # noqa: E402


def test_match_script_detecta_pipelines_conocidos():
    assert monitor._match_script(["python", "generar_guion.py"]) == "generar_guion.py"  # noqa: SLF001
    assert monitor._match_script(["python", "/path/to/validar_episodio.py"]) == "validar_episodio.py"  # noqa: SLF001
    assert monitor._match_script(["python", "C:\\repo\\generar_episodio_v2.py"]) == "generar_episodio_v2.py"  # noqa: SLF001


def test_match_script_devuelve_none_si_no_hay_match():
    assert monitor._match_script(["python", "random_script.py"]) is None  # noqa: SLF001
    assert monitor._match_script([]) is None  # noqa: SLF001


def test_pipeline_scripts_tiene_los_principales():
    must_have = {
        "generar_guion.py",
        "generar_episodio_v2.py",
        "validar_episodio.py",
        "podcast_spec.py",
    }
    assert must_have.issubset(set(monitor.PIPELINE_SCRIPTS.keys()))


def test_tail_lines_devuelve_ultimas_n(tmp_path):
    log = tmp_path / "x.log"
    log.write_text("\n".join(f"line {i}" for i in range(10)), encoding="utf-8")
    out = monitor.tail_lines(log, n=3)
    assert out == ["line 7", "line 8", "line 9"]


def test_tail_lines_filtra_lineas_vacias(tmp_path):
    log = tmp_path / "x.log"
    log.write_text("a\n\n\nb\n\nc\n", encoding="utf-8")
    out = monitor.tail_lines(log, n=10)
    assert out == ["a", "b", "c"]


def test_tail_lines_log_inexistente_devuelve_vacio(tmp_path):
    out = monitor.tail_lines(tmp_path / "no-existe.log", n=5)
    assert out == []


def test_find_active_log_devuelve_none_si_no_hay(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    assert monitor.find_active_log() is None


def test_find_active_log_elige_mas_reciente(monkeypatch, tmp_path):
    import time

    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    epis = tmp_path / "episodios"
    epis.mkdir()
    old = epis / "old.log"
    old.write_text("a")
    # Ajustar mtime: el "viejo" recibe mtime actual, el "nuevo" un instante después.
    time.sleep(0.05)
    new = epis / "new.log"
    new.write_text("b")
    assert monitor.find_active_log() == new


def test_recent_outputs_filtra_por_edad(monkeypatch, tmp_path):
    import os
    import time

    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    epis = tmp_path / "episodios"
    epis.mkdir()
    new = epis / "new.mp3"
    new.write_bytes(b"x")
    old = epis / "old.mp3"
    old.write_bytes(b"x")
    # Forzar mtime antiguo en `old`
    very_old = time.time() - 10_000
    os.utime(old, (very_old, very_old))

    items = monitor.recent_outputs(max_age_s=600)
    assert new in items
    assert old not in items


def test_scan_running_sin_psutil_devuelve_vacio(monkeypatch):
    monkeypatch.setattr(monitor, "_HAS_PSUTIL", False)
    assert monitor.scan_running() == []
