"""Tests de generadores/shared/pre_writing.py."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared import pre_writing as pw  # noqa: E402

SAMPLE_PDF_TEXT = """
Resumen ejecutivo del módulo. El 80% de las empresas usa IA de forma puntual,
pero solo el 33% la escala en producción. McKinsey publicó en 2024 un informe
que confirma esta tendencia y aporta cifras concretas sobre adopción real.

Sorprendentemente, la mayoría de proyectos fallan por falta de datos limpios,
no por limitación del modelo. Esto contradice la creencia común de que el
problema es la complejidad técnica del modelo.

OpenAI, Anthropic y Google publican datos muy distintos sobre el mismo
fenómeno. La encuesta IBM AI in Action 2024 sitúa la adopción real en torno
al 42% en grandes empresas. El paper de Stanford de 2023 aporta otra cifra.

Lo curioso es que el ROI medido no aparece hasta los 18 meses de uso.
"""


def test_extract_pre_writing_finds_numeric_data():
    res = pw.extract_pre_writing(SAMPLE_PDF_TEXT)
    assert len(res.datos_numericos) >= 4
    # Debe haber algún porcentaje detectado.
    assert any("%" in d for d in res.datos_numericos)


def test_extract_pre_writing_finds_named_orgs():
    res = pw.extract_pre_writing(SAMPLE_PDF_TEXT)
    names = res.casos_nombre_propio
    assert "OpenAI" in names
    assert "McKinsey" in names
    assert len(names) >= 3


def test_extract_pre_writing_finds_frase_fuerza():
    res = pw.extract_pre_writing(SAMPLE_PDF_TEXT)
    assert res.frase_fuerza  # no vacía
    # Es una frase del primer tramo.
    assert "empresas" in res.frase_fuerza or "IA" in res.frase_fuerza


def test_extract_pre_writing_finds_contraintuitivos():
    res = pw.extract_pre_writing(SAMPLE_PDF_TEXT)
    assert len(res.contraintuitivos) >= 2
    # Al menos uno debe contener algún marcador.
    text_contras = " ".join(res.contraintuitivos).lower()
    assert any(m in text_contras for m in
               ("sorprendentemente", "contradice", "lo curioso"))


def test_extract_pre_writing_empty_pdf():
    res = pw.extract_pre_writing("")
    assert res.datos_numericos == []
    assert res.casos_nombre_propio == []
    assert res.frase_fuerza == ""
    assert res.contraintuitivos == []


def test_meets_minimum_when_complete():
    res = pw.extract_pre_writing(SAMPLE_PDF_TEXT)
    assert res.meets_minimum(datos_min=3, casos_min=2, contraintuitivos_min=2)


def test_meets_minimum_fails_on_thin_pdf():
    res = pw.extract_pre_writing("Texto plano sin datos ni casos.")
    assert not res.meets_minimum(datos_min=3, casos_min=2,
                                  contraintuitivos_min=2)


def test_summary_returns_counts():
    res = pw.extract_pre_writing(SAMPLE_PDF_TEXT)
    s = res.summary()
    assert s["datos_numericos_count"] >= 4
    assert s["casos_nombre_propio_count"] >= 3
    assert s["has_frase_fuerza"] is True


def test_extract_pre_writing_cached_creates_file(tmp_path):
    cache_dir = tmp_path / "cache"
    res = pw.extract_pre_writing_cached(SAMPLE_PDF_TEXT, cache_dir)
    files = list(cache_dir.glob("*.json"))
    assert len(files) == 1
    assert res.datos_numericos


def test_extract_pre_writing_cached_uses_cache_on_second_call(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    pw.extract_pre_writing_cached(SAMPLE_PDF_TEXT, cache_dir)

    calls = {"n": 0}
    real = pw.extract_pre_writing

    def spy(text):
        calls["n"] += 1
        return real(text)

    monkeypatch.setattr(pw, "extract_pre_writing", spy)
    pw.extract_pre_writing_cached(SAMPLE_PDF_TEXT, cache_dir)
    assert calls["n"] == 0  # cache hit, no recomputo


def test_extract_pre_writing_cached_different_texts_get_different_files(tmp_path):
    cache_dir = tmp_path / "cache"
    pw.extract_pre_writing_cached(SAMPLE_PDF_TEXT, cache_dir)
    pw.extract_pre_writing_cached(SAMPLE_PDF_TEXT + " extra", cache_dir)
    assert len(list(cache_dir.glob("*.json"))) == 2


def test_extract_pre_writing_cached_empty_text_returns_empty():
    res = pw.extract_pre_writing_cached("", Path("/no/se/usa"))
    assert res.datos_numericos == []
    assert res.casos_nombre_propio == []
