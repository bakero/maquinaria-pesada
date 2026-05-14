"""Tests del modelo de episodios."""
from __future__ import annotations

from pathlib import Path

import pytest

from cockpit.core import episodes


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fabrica un repo de prueba con M3 (con audio), M3_T2 (sin audio), M5 vacío."""
    (tmp_path / "Guiones").mkdir()
    (tmp_path / "PDFs").mkdir()
    (tmp_path / "PDFs" / "temas").mkdir()
    (tmp_path / "escaletas").mkdir()
    (tmp_path / "episodios").mkdir()
    (tmp_path / "Videos").mkdir()

    # M3 — episodio módulo completo (pdf+guion+escaleta+audio)
    (tmp_path / "Guiones" / "M3_Machine_Learning_Clasico.txt").write_text(
        "Iago: hola.\nMaría: qué tal." * 200, encoding="utf-8"
    )
    (tmp_path / "PDFs" / "M3_T_Machine_Learning_Clasico.pdf").write_bytes(b"%PDF-1.4" + b"x" * 20_000)
    (tmp_path / "escaletas" / "M3_escaleta.md").write_text("# Escaleta M3\n" + "bloque\n" * 50, encoding="utf-8")
    (tmp_path / "episodios" / "M3.mp3").write_bytes(b"ID3" + b"x" * 300_000)
    (tmp_path / "episodios" / "M3_produccion.log").write_text("ok\n", encoding="utf-8")

    # M3_T2 — solo guion, naming LEGACY (Mn_TX_Tk_slug)
    (tmp_path / "Guiones" / "M3_TX_T2_modelos_clasicos.txt").write_text(
        "Iago: x.\nMaría: y." * 100, encoding="utf-8"
    )

    # M7_T1 — solo guion, naming ACTUAL (Mn_Tk_slug)
    (tmp_path / "Guiones" / "M7_T1_que_es_rag.txt").write_text(
        "Iago: x.\nMaría: y." * 100, encoding="utf-8"
    )

    # M5 — vacío (solo carpetas), pero figura en MODULES

    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    return tmp_path


def test_scan_all_detects_m_and_t_episodes(fake_repo: Path):
    eps = episodes.scan_all()
    ids = {e.id for e in eps}
    assert "M3" in ids
    assert "M3_T2" in ids
    # M5 figura como módulo aunque no tenga contenidos
    assert "M5" in ids


def test_m3_complete_episode(fake_repo: Path):
    m3 = next(e for e in episodes.scan_all() if e.id == "M3")
    assert m3.kind == "M"
    assert m3.has("pdf") and m3.has("guion") and m3.has("escaleta") and m3.has("audio")
    assert m3.complete
    assert m3.progress == 1.0


def test_m3_t2_partial(fake_repo: Path):
    t2 = next(e for e in episodes.scan_all() if e.id == "M3_T2")
    assert t2.kind == "T"
    assert t2.number == 2
    assert t2.has("guion")
    assert not t2.has("audio")
    assert not t2.complete
    assert 0 < t2.progress < 1


def test_naming_actual_t_episode_detectado(fake_repo: Path):
    """El naming actual Mn_Tk_slug (sin TX_) se descubre como episodio T."""
    t1 = next((e for e in episodes.scan_all() if e.id == "M7_T1"), None)
    assert t1 is not None, "M7_T1 (naming Mn_Tk_) no fue detectado"
    assert t1.kind == "T"
    assert t1.number == 1
    assert t1.slug == "que_es_rag"
    assert t1.has("guion")


def test_module_status_listo(fake_repo: Path):
    eps_m3 = [e for e in episodes.scan_module("M3") if e.id == "M3"]
    status, ratio = episodes.module_status(eps_m3)
    assert status == "listo"
    assert ratio == 1.0


def test_module_status_en_curso(fake_repo: Path):
    eps = episodes.scan_module("M3")  # M3 listo + M3_T2 parcial
    status, ratio = episodes.module_status(eps)
    assert status == "en_curso"
    assert 0 < ratio < 1


def test_module_status_sin_empezar(fake_repo: Path):
    eps = episodes.scan_module("M5")
    status, ratio = episodes.module_status(eps)
    assert status == "sin_empezar"
    assert ratio == 0.0


def test_get_episode(fake_repo: Path):
    assert episodes.get_episode("M3").id == "M3"
    assert episodes.get_episode("NO_EXISTE") is None


def test_status_badges_cover_all_states():
    assert set(episodes.STATUS_BADGE) == {"listo", "en_curso", "sin_empezar"}


def test_module_token_disambiguation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """M1 no debe capturar M10/M11/M12."""
    for d in ("Guiones", "PDFs", "PDFs/temas", "escaletas", "episodios", "Videos"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "Guiones" / "M1_Fundamentos.txt").write_text("Iago x María y", encoding="utf-8")
    (tmp_path / "Guiones" / "M10_Sistemas.txt").write_text("Iago x María y", encoding="utf-8")
    (tmp_path / "Guiones" / "M11_Auto.txt").write_text("Iago x María y", encoding="utf-8")
    (tmp_path / "episodios" / "M1.mp3").write_bytes(b"x" * 1000)
    (tmp_path / "episodios" / "M10.mp3").write_bytes(b"x" * 1000)
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))

    by_mod: dict[str, list[episodes.Episode]] = {}
    for e in episodes.scan_all():
        by_mod.setdefault(e.module, []).append(e)
    # M1 solo debe tener su propio episodio, no los de M10/M11
    m1_eps = [e for e in by_mod["M1"] if e.kind == "M"]
    assert len(m1_eps) == 1
    assert m1_eps[0].guion is not None
    assert "M1_Fundamentos" in m1_eps[0].guion.name
