"""Tests de generadores/shared/fuentes_loader.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import fuentes_loader as fl  # noqa: E402

SAMPLE = """\
# Glosario

## RAG (Retrieval-Augmented Generation)
**Fuentes:** M0_T1, M0_T2, M5_T2, M7_T1, M7_RESUMEN
**S:** 1
Técnica que combina recuperación con generación.

## Embedding
**Fuentes:** M5_T2, M5_RESUMEN
**S:** 3
Representación vectorial densa de texto.

## BLEU/ROUGE
**Fuentes:** M5_T7
Métricas clásicas de evaluación de traducción y resumen.

## IA
**Fuentes:** base
Concepto general de inteligencia artificial.
"""


def test_parse_glosario_counts_entries():
    entries = fl.parse_glosario(SAMPLE)
    names = [e.name for e in entries]
    assert "RAG" in names
    assert "Embedding" in names
    assert "BLEU/ROUGE" in names
    assert "IA" in names


def test_parse_glosario_extracts_sigla():
    entries = fl.parse_glosario(SAMPLE)
    rag = next(e for e in entries if e.name == "RAG")
    assert rag.sigla == "Retrieval-Augmented Generation"


def test_parse_glosario_extracts_s_number():
    entries = fl.parse_glosario(SAMPLE)
    rag = next(e for e in entries if e.name == "RAG")
    emb = next(e for e in entries if e.name == "Embedding")
    bleu = next(e for e in entries if e.name == "BLEU/ROUGE")
    assert rag.s_number == 1
    assert emb.s_number == 3
    assert bleu.s_number is None


def test_parse_glosario_fuentes_module_extraction():
    entries = fl.parse_glosario(SAMPLE)
    rag = next(e for e in entries if e.name == "RAG")
    modulos = rag.modulos_distintos
    assert "M0" in modulos
    assert "M5" in modulos
    assert "M7" in modulos


def test_parse_glosario_resumen_flag():
    entries = fl.parse_glosario(SAMPLE)
    rag = next(e for e in entries if e.name == "RAG")
    assert rag.aparece_en_resumen
    bleu = next(e for e in entries if e.name == "BLEU/ROUGE")
    assert not bleu.aparece_en_resumen


def test_parse_glosario_ignores_base_in_modulos():
    entries = fl.parse_glosario(SAMPLE)
    ia = next(e for e in entries if e.name == "IA")
    assert ia.fuentes == []


def test_find_entry_case_insensitive():
    entries = fl.parse_glosario(SAMPLE)
    e = fl.find_entry(entries, "rag")
    assert e is not None
    assert e.name == "RAG"


def test_find_entry_by_sigla():
    entries = fl.parse_glosario(SAMPLE)
    e = fl.find_entry(entries, "Retrieval-Augmented Generation")
    assert e is not None
    assert e.name == "RAG"


def test_entries_for_module_filters_correctly():
    entries = fl.parse_glosario(SAMPLE)
    m5 = fl.entries_for_module(entries, "M5")
    names = {e.name for e in m5}
    # RAG, Embedding y BLEU/ROUGE están todos en M5_*.
    assert "RAG" in names
    assert "Embedding" in names
    assert "BLEU/ROUGE" in names
    # IA no tiene módulos asignados.
    assert "IA" not in names


def test_entries_for_module_excludes_unrelated():
    entries = fl.parse_glosario(SAMPLE)
    m99 = fl.entries_for_module(entries, "M99")
    assert m99 == []


def test_load_glosario_missing_path_returns_empty(tmp_path):
    assert fl.load_glosario(tmp_path / "no_existe.md") == []


def test_write_s_number_adds_line(tmp_path):
    path = tmp_path / "glos.md"
    path.write_text(SAMPLE, encoding="utf-8")
    # BLEU/ROUGE no tiene **S:** — añadirla.
    ok = fl.write_s_number(path, "BLEU/ROUGE", 42)
    assert ok is True
    new_text = path.read_text(encoding="utf-8")
    assert "**S:** 42" in new_text
    entries = fl.parse_glosario(new_text)
    bleu = next(e for e in entries if e.name == "BLEU/ROUGE")
    assert bleu.s_number == 42


def test_write_s_number_updates_existing_line(tmp_path):
    path = tmp_path / "glos.md"
    path.write_text(SAMPLE, encoding="utf-8")
    ok = fl.write_s_number(path, "RAG", 99)
    assert ok is True
    entries = fl.parse_glosario(path.read_text(encoding="utf-8"))
    rag = next(e for e in entries if e.name == "RAG")
    assert rag.s_number == 99
