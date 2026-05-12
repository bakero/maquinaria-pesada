"""Tests del módulo state (escaneo de módulos M0..M14)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import paths, state  # noqa: E402


def test_has_module_acepta_variantes():
    h = state._has_module  # noqa: SLF001
    assert h("M3_T_ML.txt", "M3")
    assert h("EP_M03_intro.pdf", "M3")
    assert h("RESUMEN_MOD003.pdf", "M3")
    assert h("mod3_legacy.log", "M3")


def test_has_module_rechaza_colisiones():
    h = state._has_module  # noqa: SLF001
    assert not h("M30_otro.txt", "M3"), "M30 no debe matchear M3"
    assert not h("RESUMEN_M10_*.pdf", "M1"), "M10 no debe matchear M1"
    assert not h("EXAMEN.pdf", "M3"), "Sin token = no match"


def test_modulestatus_complete_requiere_todo():
    s = state.ModuleStatus(module="M0")
    assert s.complete is False
    s.pdf = [Path("a.pdf")]
    assert s.complete is False  # falta el resto
    s.guion = [Path("a.txt")]
    s.audio = [Path("a.mp3")]
    s.video = [Path("a.mp4")]
    assert s.complete is True


def test_modulestatus_propiedades_individuales():
    s = state.ModuleStatus(module="M0")
    assert s.pdf_ok is False
    s.pdf = [Path("x")]
    assert s.pdf_ok is True


def test_scan_devuelve_un_status_por_modulo(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    # Sin directorios → todos vacíos pero presentes.
    out = state.scan()
    assert len(out) == len(paths.MODULES)
    for s in out:
        assert s.pdf == s.guion == s.audio == s.video == s.log == []
        assert s.complete is False


def test_scan_detecta_ficheros_por_modulo(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    (tmp_path / "PDFs").mkdir()
    (tmp_path / "PDFs" / "M3_test.pdf").write_text("x")
    (tmp_path / "Guiones").mkdir()
    (tmp_path / "Guiones" / "M3_guion.txt").write_text("x")
    (tmp_path / "episodios").mkdir()
    (tmp_path / "episodios" / "M3_audio.mp3").write_bytes(b"")
    (tmp_path / "episodios" / "M3_run.log").write_text("ok")
    (tmp_path / "Videos").mkdir()
    (tmp_path / "Videos" / "M3_video.mp4").write_bytes(b"")

    out = {s.module: s for s in state.scan()}
    assert len(out["M3"].pdf) == 1
    assert len(out["M3"].guion) == 1
    assert len(out["M3"].audio) == 1
    assert len(out["M3"].video) == 1
    assert len(out["M3"].log) == 1
    assert out["M3"].complete is True
    assert out["M0"].pdf == []  # M0 sin nada


def test_pendientes_excluye_modulos_completos(monkeypatch, tmp_path):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    states = state.scan()
    states[0].pdf = [Path("a.pdf")]
    states[0].guion = [Path("a.txt")]
    states[0].audio = [Path("a.mp3")]
    states[0].video = [Path("a.mp4")]
    assert states[0].complete is True
    pend = state.pendientes(states)
    assert states[0] not in pend
    assert len(pend) == len(states) - 1
