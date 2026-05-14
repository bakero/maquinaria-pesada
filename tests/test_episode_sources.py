"""Tests del mapeo episodio → PDF + script (cockpit.core.episode_sources)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cockpit.core import episode_sources as es


def test_source_for_modulo_m():
    src = es.source_for("M3")
    assert src is not None
    assert src.kind == "M"
    assert src.module == "M3"
    assert src.script == "generar_guion.py"
    assert src.pdf.endswith(".pdf")
    assert src.flags == ["--modulo", "3", "--pdf", src.pdf]


def test_source_for_tema_t():
    src = es.source_for("M7_T1")
    assert src is not None
    assert src.kind == "T"
    assert src.module == "M7"
    assert src.script == "generar_guion_t.py"
    assert src.flags == ["--pdf", src.pdf]


def test_source_for_unknown_returns_none():
    assert es.source_for("M999") is None
    assert es.source_for("M3_T99") is None
    assert es.source_for("basura") is None
    assert es.source_for("") is None


def test_all_sources_has_m_and_t():
    sources = es.all_sources()
    assert len(sources) == len(es.M_PDFS) + len(es.T_PDFS)
    kinds = {s.kind for s in sources}
    assert kinds == {"M", "T"}
    # M va antes que T
    first_t = next(i for i, s in enumerate(sources) if s.kind == "T")
    assert all(s.kind == "M" for s in sources[:first_t])


def test_t_pdf_ids_well_formed():
    for ep_id in es.T_PDFS:
        assert ep_id.count("_T") == 1
        src = es.source_for(ep_id)
        assert src is not None and src.ep_id == ep_id
