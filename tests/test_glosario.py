"""Tests del parser y la cobertura del glosario unificado (podcast_spec)."""
from __future__ import annotations

from pathlib import Path

import podcast_spec as ps

GLOSARIO_SAMPLE = """\
# Glosario Unificado — MaquinarIA Pesada

Texto introductorio que no es una entrada.

---

## Conceptos base

## RAG (Retrieval-Augmented Generation)
**Fuentes:** M7_T1, M7_T5, M0_RESUMEN
Técnica que combina recuperación y generación.

## Módulo 7 — Sistemas RAG

## Chunking (fixed-size)
**Fuentes:** M7_T1, M7_T3
División de documentos en fragmentos.

## Gap prototipo-producción (RAG)
**Fuentes:** M7_T5
Diferencia entre un prototipo y un sistema en producción.

## LoRA (Low-Rank Adaptation)
**Fuentes:** M2_T1, M8_T3
Técnica de fine-tuning eficiente.
"""


def _write_glossary(tmp_path: Path) -> Path:
    path = tmp_path / "glosario_unificado.md"
    path.write_text(GLOSARIO_SAMPLE, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# parse_glossary
# ---------------------------------------------------------------------------

def test_parse_glossary_extrae_terminos_y_fuentes(tmp_path: Path) -> None:
    glossary = ps.parse_glossary(_write_glossary(tmp_path))
    assert glossary["RAG (Retrieval-Augmented Generation)"] == ["M7_T1", "M7_T5", "M0_RESUMEN"]
    assert glossary["LoRA (Low-Rank Adaptation)"] == ["M2_T1", "M8_T3"]


def test_parse_glossary_ignora_encabezados_de_seccion(tmp_path: Path) -> None:
    glossary = ps.parse_glossary(_write_glossary(tmp_path))
    assert "Conceptos base" not in glossary
    assert not any(t.lower().startswith("módulo") for t in glossary)


def test_parse_glossary_archivo_inexistente_devuelve_dict_vacio(tmp_path: Path) -> None:
    assert ps.parse_glossary(tmp_path / "no_existe.md") == {}


# ---------------------------------------------------------------------------
# source_code_from_pdf_path
# ---------------------------------------------------------------------------

def test_source_code_desde_pdf_de_tema() -> None:
    assert ps.source_code_from_pdf_path("PDFs/temas/M7_T1_que_es_rag.pdf") == "M7_T1"
    assert ps.source_code_from_pdf_path("PDFs/temas/M10_T8_protocolos.pdf") == "M10_T8"


def test_source_code_desde_pdf_resumen() -> None:
    assert ps.source_code_from_pdf_path(
        "PDFs/resumenes/RESUMEN_M3_Machine_Learning_Clasico.pdf"
    ) == "M3_RESUMEN"


def test_source_code_desde_pdf_de_modulo() -> None:
    assert ps.source_code_from_pdf_path("PDFs/M3_T_Machine_Learning_Clasico.pdf") == "M3"


def test_source_code_sin_patron_devuelve_none() -> None:
    assert ps.source_code_from_pdf_path("PDFs/auxiliares/glosario.md") is None


# ---------------------------------------------------------------------------
# glossary_concepts_for_sources
# ---------------------------------------------------------------------------

def test_concepts_for_sources_filtra_por_codigo(tmp_path: Path) -> None:
    glossary = ps.parse_glossary(_write_glossary(tmp_path))
    conceptos = ps.glossary_concepts_for_sources("M7_T1", glossary=glossary)
    assert "RAG (Retrieval-Augmented Generation)" in conceptos
    assert "Chunking (fixed-size)" in conceptos
    assert "LoRA (Low-Rank Adaptation)" not in conceptos


def test_concepts_for_sources_acepta_lista(tmp_path: Path) -> None:
    glossary = ps.parse_glossary(_write_glossary(tmp_path))
    conceptos = ps.glossary_concepts_for_sources(["M2_T1", "M0_RESUMEN"], glossary=glossary)
    assert set(conceptos) == {
        "RAG (Retrieval-Augmented Generation)",
        "LoRA (Low-Rank Adaptation)",
    }


# ---------------------------------------------------------------------------
# glossary_term_aliases / concept_in_text
# ---------------------------------------------------------------------------

def test_aliases_expande_acronimo_y_definicion() -> None:
    aliases = ps.glossary_term_aliases("LoRA (Low-Rank Adaptation)")
    assert "lora" in aliases
    assert "low-rank adaptation" in aliases


def test_aliases_no_usa_parentesis_de_referencia_cruzada() -> None:
    # "RAG" es una referencia cruzada, no un sinónimo de este término.
    aliases = ps.glossary_term_aliases("Gap prototipo-producción (RAG)")
    assert "rag" not in aliases


def test_concept_in_text_detecta_alias() -> None:
    assert ps.concept_in_text("Hoy hablamos de LoRA en detalle.", "LoRA (Low-Rank Adaptation)")
    assert not ps.concept_in_text("Hoy hablamos de otra cosa.", "LoRA (Low-Rank Adaptation)")


# ---------------------------------------------------------------------------
# compute_glossary_coverage
# ---------------------------------------------------------------------------

def test_coverage_calcula_porcentaje() -> None:
    conceptos = ["RAG (Retrieval-Augmented Generation)", "LoRA (Low-Rank Adaptation)"]
    cov = ps.compute_glossary_coverage("Solo mencionamos RAG aquí.", conceptos)
    assert cov["total"] == 2
    assert cov["coverage_pct"] == 50
    assert cov["covered"] == ["RAG (Retrieval-Augmented Generation)"]
    assert cov["missing"] == ["LoRA (Low-Rank Adaptation)"]


def test_coverage_lista_vacia() -> None:
    cov = ps.compute_glossary_coverage("texto cualquiera", [])
    assert cov == {"total": 0, "covered": [], "missing": [], "coverage_pct": 0}


# ---------------------------------------------------------------------------
# Glosario real del repo
# ---------------------------------------------------------------------------

def test_glosario_real_es_parseable() -> None:
    real_path = Path(__file__).parent.parent / "PDFs" / "auxiliares" / "glosario_unificado.md"
    glossary = ps.parse_glossary(real_path)
    assert len(glossary) > 200
    assert "RAG (Retrieval-Augmented Generation)" in glossary
    # Toda entrada tiene al menos una fuente declarada.
    assert all(codes for codes in glossary.values())
