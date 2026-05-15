"""Tests de los generadores especialistas m/t/s_generator (sin red).

Verifican la construcción de prompts y la integración con run_pipeline.
Mockean anthropic_client.generate para no llamar a la API real.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores import m_generator, s_generator, t_generator  # noqa: E402
from generadores.shared import anthropic_client as ac  # noqa: E402

GLOSARIO_SAMPLE = """\
## RAG (Retrieval-Augmented Generation)
**Fuentes:** M0_T1, M5_T2, M7_T1, M7_RESUMEN
**S:** 1
Técnica que combina recuperación con generación.
"""


# ---- m_generator ----------------------------------------------------------


def test_m_build_user_prompt_includes_module_n(tmp_path):
    (tmp_path / "PDFs" / "auxiliares").mkdir(parents=True)
    for n in ("BIBLIA_SISTEMA", "PRIMERPODCAST", "VIDEOPODCAST", "PODCAST"):
        (tmp_path / f"{n}.md").write_text("contenido", encoding="utf-8")
    prompt = m_generator.build_user_prompt(episode_id="M3", repo_root=tmp_path)
    assert "M3" in prompt or "módulo 3" in prompt


def test_m_build_user_prompt_warns_missing_master_pdf(tmp_path):
    """Si falta master IA.pdf, el prompt emite un AVISO explícito."""
    for n in ("BIBLIA_SISTEMA", "PRIMERPODCAST", "VIDEOPODCAST", "PODCAST"):
        (tmp_path / f"{n}.md").write_text("contenido", encoding="utf-8")
    prompt = m_generator.build_user_prompt(episode_id="M3", repo_root=tmp_path)
    assert "AVISO" in prompt
    assert "master IA.pdf" in prompt


def test_m_build_user_prompt_lists_temas_pdfs(tmp_path):
    """Si hay PDFs de temas del módulo, los enumera en el prompt."""
    for n in ("BIBLIA_SISTEMA", "PRIMERPODCAST", "VIDEOPODCAST", "PODCAST"):
        (tmp_path / f"{n}.md").write_text("contenido", encoding="utf-8")
    temas = tmp_path / "PDFs" / "temas"
    temas.mkdir(parents=True)
    (temas / "M3_T1_uno.pdf").write_bytes(b"%PDF-1.4")
    (temas / "M3_T2_dos.pdf").write_bytes(b"%PDF-1.4")
    prompt = m_generator.build_user_prompt(episode_id="M3", repo_root=tmp_path)
    assert "M3_T1_uno.pdf" in prompt
    assert "M3_T2_dos.pdf" in prompt


def test_m_build_user_prompt_invalid_id_raises(tmp_path):
    with pytest.raises(ValueError):
        m_generator.build_user_prompt(episode_id="basura", repo_root=tmp_path)


def test_m_generate_runs_pipeline_with_mock(monkeypatch, tmp_path):
    """Mocking the LLM call: la pipeline corre sin tocar la API real."""
    monkeypatch.setattr(
        ac, "generate",
        lambda **kw: ac.GenerationResult(
            text="# HOOK\nMARIA: [directo] hola\n", model="m",
            input_tokens=10, output_tokens=5, cost_usd=0.001,
        ),
    )
    for n in ("BIBLIA_SISTEMA", "PRIMERPODCAST", "VIDEOPODCAST", "PODCAST"):
        (tmp_path / f"{n}.md").write_text("contenido", encoding="utf-8")
    result = m_generator.generate("M0", repo_root=tmp_path)
    assert result.generation.ok
    # Hay validation_results (porque hay validate_fn).
    assert result.validation_results
    # Costes registrados.
    assert (tmp_path / "costes_generacion.log").exists()


# ---- t_generator ----------------------------------------------------------


def test_t_build_user_prompt_extracts_module_and_tema(tmp_path):
    prompt = t_generator.build_user_prompt(
        episode_id="M3_T2", repo_root=tmp_path)
    assert "módulo 3" in prompt or "M3" in prompt
    assert "tema 2" in prompt or "T2" in prompt


def test_t_build_user_prompt_warns_missing_pdf(tmp_path):
    prompt = t_generator.build_user_prompt(
        episode_id="M3_T2", repo_root=tmp_path)
    assert "AVISO" in prompt


def test_t_build_user_prompt_invalid_id_raises(tmp_path):
    with pytest.raises(ValueError):
        t_generator.build_user_prompt(episode_id="M3", repo_root=tmp_path)


def test_t_generate_runs_pipeline_with_mock(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ac, "generate",
        lambda **kw: ac.GenerationResult(
            text="# HOOK\nIAGO: [directo] hola\n", model="m",
            input_tokens=10, output_tokens=5, cost_usd=0.001,
        ),
    )
    result = t_generator.generate("M3_T1", repo_root=tmp_path)
    assert result.generation.ok


# ---- s_generator ----------------------------------------------------------


def test_s_build_user_prompt_loads_glosario(tmp_path):
    (tmp_path / "PDFs" / "auxiliares").mkdir(parents=True)
    glos = tmp_path / "PDFs" / "auxiliares" / "glosario_unificado.md"
    glos.write_text(GLOSARIO_SAMPLE, encoding="utf-8")
    prompt = s_generator.build_user_prompt(
        episode_id="S1", term="RAG", repo_root=tmp_path)
    assert "RAG" in prompt
    assert "Más sobre" in prompt


def test_s_build_user_prompt_unknown_term_warns(tmp_path):
    (tmp_path / "PDFs" / "auxiliares").mkdir(parents=True)
    glos = tmp_path / "PDFs" / "auxiliares" / "glosario_unificado.md"
    glos.write_text(GLOSARIO_SAMPLE, encoding="utf-8")
    prompt = s_generator.build_user_prompt(
        episode_id="S99", term="termino_inventado", repo_root=tmp_path)
    assert "AVISO" in prompt


def test_s_generate_invalid_id_raises(tmp_path):
    with pytest.raises(ValueError):
        s_generator.generate("X1", term="RAG", repo_root=tmp_path)


def test_s_generate_runs_pipeline_with_mock(monkeypatch, tmp_path):
    (tmp_path / "PDFs" / "auxiliares").mkdir(parents=True)
    glos = tmp_path / "PDFs" / "auxiliares" / "glosario_unificado.md"
    glos.write_text(GLOSARIO_SAMPLE, encoding="utf-8")
    monkeypatch.setattr(
        ac, "generate",
        lambda **kw: ac.GenerationResult(
            text="Texto del Short. Más sobre RAG en el episodio T de MaquinarIA Pesada.",
            model="m", input_tokens=10, output_tokens=5, cost_usd=0.001,
        ),
    )
    result = s_generator.generate("S1_RAG", term="RAG", repo_root=tmp_path)
    assert result.generation.ok
    # Costes registrados con kind="S".
    log = (tmp_path / "costes_generacion.log").read_text(encoding="utf-8")
    assert ",S," in log


def test_s_voice_parity_is_iago_for_odd(tmp_path):
    """S1 → impar → voz IAGO (verificada por la validación interna)."""
    (tmp_path / "PDFs" / "auxiliares").mkdir(parents=True)
    glos = tmp_path / "PDFs" / "auxiliares" / "glosario_unificado.md"
    glos.write_text(GLOSARIO_SAMPLE, encoding="utf-8")
    # Solo build_user_prompt + comprobar a través de la validación.
    from validators.shared.parity import opener_for
    assert opener_for(1) == "IAGO"
    assert opener_for(2) == "MARIA"
