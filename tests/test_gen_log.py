"""Tests del parseo de trazas de generación (cockpit.core.gen_log)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cockpit.core import gen_log

_TRACE_OK = (
    "  [3/4] Generando guion (intento 1/3)...\n"
    "         Issues hard: 1 | soft: 2\n"
    "         [HARD] M3 tiene 900 palabras (minimo: 1200)\n"
    "         [WARN] bloque 4 con solo 2 frases\n"
    "         [WARN] CTA ausente\n"
    "  [3/4] Generando guion (intento 2/3)...\n"
    "         [PASS] Validacion OK\n"
    "  [4/4] Guardando guion...\n"
    "  GUION GENERADO : Guiones/M3_x.txt\n"
)


def test_parse_gen_log_pass():
    out = gen_log.parse_gen_log(_TRACE_OK)
    assert out["verdict"] == "ok"
    assert out["attempts"] == 2
    assert out["saved"] is True
    assert out["hard_issues"] == ["M3 tiene 900 palabras (minimo: 1200)"]
    assert len(out["soft_issues"]) == 2


def test_parse_gen_log_exhausted_is_warn():
    text = (
        "  [3/4] Generando guion (intento 3/3)...\n"
        "         [HARD] sigue corto\n"
        "  [WARN] Superado máximo de intentos. Guardando mejor intento.\n"
        "  GUION GENERADO : Guiones/M3_x.txt\n"
    )
    out = gen_log.parse_gen_log(text)
    assert out["verdict"] == "warn"
    assert out["saved"] is True


def test_parse_gen_log_running_when_not_saved():
    text = "  [3/4] Generando guion (intento 1/3)...\n         Issues hard: 0\n"
    out = gen_log.parse_gen_log(text)
    assert out["verdict"] == "running"
    assert out["saved"] is False


def test_gen_log_path_convention(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    for mod in list(sys.modules):
        if mod.startswith("cockpit.core"):
            del sys.modules[mod]
    from cockpit.core import gen_log as gl
    p = gl.gen_log_path("M7_T1")
    assert p.name == "M7_T1_gen.log"
    assert p.parent.name == "logs"


def test_read_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    for mod in list(sys.modules):
        if mod.startswith("cockpit.core"):
            del sys.modules[mod]
    from cockpit.core import gen_log as gl
    out = gl.read("M3")
    assert out["ok"] is False
    assert out["exists"] is False
