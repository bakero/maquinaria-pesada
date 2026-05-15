"""Tests del selector/ordenador automático de Shorts.

5 tests críticos del spec PODCAST_S_SPEC.md: idempotencia, estabilidad,
correctitud del filtro, correctitud del score, desempate.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generadores.shared.fuentes_loader import parse_glosario  # noqa: E402
from scripts import seleccionar_y_ordenar_shorts as sel  # noqa: E402

GLOSARIO_FIXTURE = """\
# Glosario test

## RAG (Retrieval-Augmented Generation)
**Fuentes:** M0_T1, M0_T2, M5_T2, M7_T1, M7_RESUMEN
Definición de RAG.

## Embedding
**Fuentes:** M5_T2, M5_RESUMEN
Definición de embedding.

## Fine-tuning
**Fuentes:** M5_T3, M5_T4, M5_T5, M5_T6, M5_T7
Definición de fine-tuning.

## BLEU/ROUGE
**Fuentes:** M5_T7
Definición de BLEU/ROUGE.

## Beam Search en ToT
**Fuentes:** M6_T3
Beam Search dentro del Tree of Thoughts.

## Sycophancy (sobreconformidad)
**Fuentes:** M5_T8
Tendencia de los LLM a coincidir con el usuario.

## LLM (Large Language Model)
**Fuentes:** M0_T1, M0_T2, M5_T2, M5_T3
Modelo de lenguaje a gran escala.
"""


def _write_glosario(tmp_path: Path) -> Path:
    path = tmp_path / "PDFs" / "auxiliares" / "glosario_unificado.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(GLOSARIO_FIXTURE, encoding="utf-8")
    return path


# ---- Filtro ---------------------------------------------------------------


def test_filtro_transversal_pasa():
    """Un término en ≥2 módulos distintos es candidato."""
    entries = parse_glosario(GLOSARIO_FIXTURE)
    rag = next(e for e in entries if e.name == "RAG")
    ok, motivo = sel.es_candidato(rag)
    assert ok is True
    assert motivo == "transversal_2plus_modulos"


def test_filtro_denso_pasa():
    """Un término con ≥4 menciones aunque sea de 1 módulo es candidato."""
    entries = parse_glosario(GLOSARIO_FIXTURE)
    ft = next(e for e in entries if e.name == "Fine-tuning")
    ok, motivo = sel.es_candidato(ft)
    assert ok is True
    assert motivo == "denso_4plus_menciones"


def test_filtro_resumen_pasa():
    """Un término que aparece en _RESUMEN es candidato aunque sea de 1 módulo."""
    entries = parse_glosario(GLOSARIO_FIXTURE)
    emb = next(e for e in entries if e.name == "Embedding")
    ok, motivo = sel.es_candidato(emb)
    assert ok is True


def test_filtro_excluye_termino_nicho():
    """1 módulo + 1 mención + no en RESUMEN → excluido."""
    entries = parse_glosario(GLOSARIO_FIXTURE)
    bleu = next(e for e in entries if e.name == "BLEU/ROUGE")
    ok, _ = sel.es_candidato(bleu)
    assert ok is False
    bs = next(e for e in entries if e.name == "Beam Search en ToT")
    ok, _ = sel.es_candidato(bs)
    assert ok is False


# ---- Score ----------------------------------------------------------------


def test_score_formula_correcta():
    """score = transversalidad*3 + min(densidad, 20) + 5_si_RESUMEN."""
    entries = parse_glosario(GLOSARIO_FIXTURE)
    rag = next(e for e in entries if e.name == "RAG")
    # transv=3 (M0, M5, M7), densidad=5, en_resumen=True
    assert sel.calcular_score(rag) == 3 * 3 + 5 + 5  # = 19


def test_score_densidad_capada_a_20():
    """Una entrada con densidad > 20 cuenta solo 20 en el score."""
    text = (
        "## SuperDenso\n"
        "**Fuentes:** " + ", ".join(f"M0_T{i}" for i in range(1, 30)) + "\n"
        "Definición.\n"
    )
    entries = parse_glosario(text)
    e = entries[0]
    assert len(e.fuentes) > 20
    # transv=1, densidad=29 capada a 20, no en RESUMEN
    assert sel.calcular_score(e) == 1 * 3 + 20


# ---- Desempate ------------------------------------------------------------


def test_desempate_por_transversalidad():
    """Score idéntico → gana mayor transversalidad."""
    text = """\
## TermA
**Fuentes:** M0_T1, M0_T2, M0_T3, M0_T4, M0_T5
Definición.

## TermB
**Fuentes:** M0_T1, M1_T1, M2_T1
Definición.
"""
    entries = parse_glosario(text)
    asignaciones, _ = sel.seleccionar_y_ordenar(entries)
    # A: transv=1, densidad=5 → score = 3 + 5 = 8
    # B: transv=3, densidad=3 → score = 9 + 3 = 12 → B antes que A
    assert asignaciones[0].name == "TermB"


def test_desempate_alfabetico_cuando_todo_empata():
    text = """\
## Zorro
**Fuentes:** M0_T1, M1_T1
Def.

## Alfa
**Fuentes:** M0_T1, M1_T1
Def.
"""
    entries = parse_glosario(text)
    asignaciones, _ = sel.seleccionar_y_ordenar(entries)
    # Mismo score, misma transv, misma densidad → alfabético: Alfa antes que Zorro
    assert asignaciones[0].name == "Alfa"
    assert asignaciones[1].name == "Zorro"


# ---- Idempotencia ---------------------------------------------------------


def test_idempotencia_dos_ejecuciones_mismo_glosario_dan_mismo_resultado(tmp_path):
    path = _write_glosario(tmp_path)
    sel.run(tmp_path, dry_run=False)
    contenido_1 = path.read_text(encoding="utf-8")
    sel.run(tmp_path, dry_run=False)
    contenido_2 = path.read_text(encoding="utf-8")
    assert contenido_1 == contenido_2


def test_idempotencia_resumen_ranking_estable(tmp_path):
    _write_glosario(tmp_path)
    sel.run(tmp_path, dry_run=False)
    r1 = (tmp_path / "PDFs" / "auxiliares" / "glosario_shorts_ranking.md"
          ).read_text(encoding="utf-8")
    sel.run(tmp_path, dry_run=False)
    r2 = (tmp_path / "PDFs" / "auxiliares" / "glosario_shorts_ranking.md"
          ).read_text(encoding="utf-8")
    # Quitamos la línea de fecha (cambia entre ejecuciones).
    r1_lines = [line for line in r1.splitlines() if "Ranking" not in line]
    r2_lines = [line for line in r2.splitlines() if "Ranking" not in line]
    assert r1_lines == r2_lines


# ---- Estabilidad ----------------------------------------------------------


def test_estabilidad_terminos_nuevos_no_reordenan_existentes(tmp_path):
    path = _write_glosario(tmp_path)
    sel.run(tmp_path, dry_run=False)
    # Capturamos las asignaciones actuales.
    entries_v1 = parse_glosario(path.read_text(encoding="utf-8"))
    asignaciones_v1 = {e.name: e.s_number for e in entries_v1 if e.s_number}

    # Añadimos términos nuevos al final del glosario.
    additional = "\n## NuevoTermAlto\n**Fuentes:** M0_T1, M1_T1, M2_T1, M3_T1, M4_T1\nDef.\n"
    additional += "## NuevoTermBajo\n**Fuentes:** M0_T1, M1_T1\nDef.\n"
    path.write_text(path.read_text(encoding="utf-8") + additional, encoding="utf-8")

    sel.run(tmp_path, dry_run=False)
    entries_v2 = parse_glosario(path.read_text(encoding="utf-8"))
    asignaciones_v2 = {e.name: e.s_number for e in entries_v2 if e.s_number}

    # Los términos que ya tenían N mantienen su N.
    for name, n in asignaciones_v1.items():
        assert asignaciones_v2.get(name) == n, (
            f"{name} cambió de S{n} a S{asignaciones_v2.get(name)}")
    # Los nuevos se asignan tras el máximo previo.
    max_existing = max(asignaciones_v1.values())
    assert asignaciones_v2["NuevoTermAlto"] > max_existing
    assert asignaciones_v2["NuevoTermBajo"] > max_existing


# ---- Smoke test del pipeline completo -------------------------------------


def test_run_completo_genera_ranking_y_actualiza_glosario(tmp_path):
    path = _write_glosario(tmp_path)
    summary = sel.run(tmp_path, dry_run=False)
    assert summary["total_entries"] == 7
    # 4 candidatos: RAG, Fine-tuning, LLM, Embedding (los demás están en 1 módulo
    # sin RESUMEN).
    assert summary["selected"] == 4
    assert summary["excluded"] == 3
    # Ranking creado.
    ranking_path = tmp_path / "PDFs" / "auxiliares" / "glosario_shorts_ranking.md"
    assert ranking_path.exists()
    txt = ranking_path.read_text(encoding="utf-8")
    assert "RAG" in txt
    assert "BLEU/ROUGE" in txt  # listado en excluidos
    # Glosario con **S:** N escrito.
    glos = path.read_text(encoding="utf-8")
    assert "**S:** " in glos


def test_run_dry_run_no_modifica_glosario(tmp_path):
    path = _write_glosario(tmp_path)
    original = path.read_text(encoding="utf-8")
    sel.run(tmp_path, dry_run=True)
    assert path.read_text(encoding="utf-8") == original
    assert not (tmp_path / "PDFs" / "auxiliares"
                / "glosario_shorts_ranking.md").exists()
