"""Tests de generadores/shared/pronunciation_overrides.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import pronunciation_overrides as po  # noqa: E402


def test_load_overrides_returns_baseline_when_no_file(tmp_path):
    overrides = po.load_overrides(tmp_path / "no.json")
    assert "LLM" in overrides
    assert "RAG" in overrides
    assert overrides["RAG"] == "rag"


def test_save_and_load_roundtrip(tmp_path):
    data = {"FOO": "fuu", "BAR": "bar"}
    path = tmp_path / "ov.json"
    po.save_overrides(data, path)
    loaded = po.load_overrides(path)
    # baseline + custom
    assert loaded["FOO"] == "fuu"
    assert "LLM" in loaded  # baseline persists


def test_load_overrides_corrupt_json_falls_back_to_baseline(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{ not valid json", encoding="utf-8")
    overrides = po.load_overrides(path)
    assert "LLM" in overrides


def test_apply_overrides_replaces_known_term():
    out = po.apply_overrides("Hoy hablamos de LLM y RAG.",
                              overrides={"LLM": "elemen", "RAG": "rag"})
    assert "elemen" in out
    assert "rag" in out


def test_apply_overrides_preserves_word_boundaries():
    # "Mall" no debe ser sustituido por la regla de "LL".
    out = po.apply_overrides("Visitamos un Mall hoy.",
                              overrides={"LL": "doble ele"})
    assert "Mall" in out


def test_apply_overrides_longest_match_first():
    # "fine-tuning" debe coger la regla larga antes que "tuning" suelto.
    out = po.apply_overrides("hablamos de fine-tuning",
                              overrides={"fine-tuning": "fain tiuning",
                                         "tuning": "tuning"})
    assert "fain tiuning" in out
    assert "tuning" not in out.replace("fain tiuning", "")


def test_extract_from_glosario_detects_siglas():
    text = "## LLM (Large Language Model)\n**Fuentes:** M0_T1\nDef.\n## RAG (Retrieval-Augmented Generation)\n**Fuentes:** M7_T1\nDef.\n"
    extracted = po.extract_from_glosario(text)
    assert "LLM" in extracted
    assert "RAG" in extracted
    assert "ele ele eme" in extracted["LLM"].lower()


def test_extract_from_glosario_ignores_lowercase_headings():
    text = "## embeddings\n**Fuentes:** M5_T2\nDef.\n"
    extracted = po.extract_from_glosario(text)
    # No es sigla → no se incluye automaticamente.
    assert "embeddings" not in extracted


def test_save_overrides_emits_sorted_json(tmp_path):
    path = tmp_path / "ov.json"
    po.save_overrides({"Z": "zeta", "A": "a"}, path)
    raw = path.read_text(encoding="utf-8")
    assert raw.index('"A"') < raw.index('"Z"')
    # Y es JSON válido
    json.loads(raw)
