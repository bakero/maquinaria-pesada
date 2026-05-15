"""Tests de generadores/shared/pdf_reader.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import pdf_reader as pr  # noqa: E402


def test_read_pdf_missing_file_returns_empty(tmp_path):
    result = pr.read_pdf(tmp_path / "no_existe.pdf")
    assert result.empty
    assert result.estimated_tokens == 0
    assert result.text == ""


def test_estimate_tokens_proportional_to_words():
    # 75 palabras → ~100 tokens (0.75 palabras/token).
    t = pr._estimate_tokens(" ".join(["palabra"] * 75))
    assert 90 <= t <= 110


def test_estimate_tokens_empty_text_returns_zero():
    assert pr._estimate_tokens("") == 0
    assert pr._estimate_tokens("   ") == 0


def test_find_resumen_missing_returns_none(tmp_path):
    (tmp_path / "PDFs" / "resumenes").mkdir(parents=True)
    assert pr.find_resumen(tmp_path, 3) is None


def test_find_resumen_returns_first_match(tmp_path):
    d = tmp_path / "PDFs" / "resumenes"
    d.mkdir(parents=True)
    (d / "RESUMEN_M3_DeepLearning.pdf").write_bytes(b"%PDF-1.4")
    result = pr.find_resumen(tmp_path, 3)
    assert result is not None
    assert result.name.startswith("RESUMEN_M3")


def test_find_tema_missing_returns_none(tmp_path):
    (tmp_path / "PDFs" / "temas").mkdir(parents=True)
    assert pr.find_tema(tmp_path, 3, 2) is None


def test_find_tema_returns_first_match(tmp_path):
    d = tmp_path / "PDFs" / "temas"
    d.mkdir(parents=True)
    (d / "M5_T2_Embeddings.pdf").write_bytes(b"%PDF-1.4")
    result = pr.find_tema(tmp_path, 5, 2)
    assert result is not None


def test_coverage_percent_full():
    text = "Habla de embeddings, RAG y fine-tuning."
    pct = pr.coverage_percent(text, ["embeddings", "rag", "fine-tuning"])
    assert pct == 100.0


def test_coverage_percent_partial():
    text = "Solo habla de embeddings."
    pct = pr.coverage_percent(text, ["embeddings", "rag", "fine-tuning"])
    assert 30.0 <= pct <= 35.0


def test_coverage_percent_empty_concepts_returns_100():
    assert pr.coverage_percent("cualquier texto", []) == 100.0


def test_coverage_percent_zero_when_none_present():
    pct = pr.coverage_percent("texto plano", ["concepto-no-presente"])
    assert pct == 0.0
