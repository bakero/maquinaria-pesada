"""Tests del modelo de la pizarra (pipeline visual)."""
from __future__ import annotations

from cockpit.core import pizarra


def test_pipeline_default_structure():
    piezas, flechas = pizarra.pipeline_default()
    ids = {p.id for p in piezas}
    # Flujo canónico
    for required in ("claude", "pdf", "gen_guion", "guion", "gen_escaleta", "escaleta", "gen_audio", "episodio"):
        assert required in ids, f"falta nodo {required}"

    # Componentes y contenidos alternan
    kinds = {p.id: p.kind for p in piezas}
    assert kinds["claude"] == "component"
    assert kinds["pdf"] == "content"
    assert kinds["gen_guion"] == "component"
    assert kinds["guion"] == "content"
    assert kinds["gen_audio"] == "component"
    assert kinds["episodio"] == "content"


def test_pipeline_arrows_are_consistent():
    piezas, flechas = pizarra.pipeline_default()
    ids = {p.id for p in piezas}
    for f in flechas:
        assert f.src in ids
        assert f.dst in ids
    # Cada componente debe tener al menos una salida hacia contenido
    by_kind = {p.id: p.kind for p in piezas}
    componentes = [p for p in piezas if p.kind == "component"]
    for c in componentes:
        salidas = [f for f in flechas if f.src == c.id]
        assert any(by_kind[s.dst] == "content" for s in salidas), \
            f"componente {c.id} no produce ningún contenido"


def test_components_have_code_path():
    piezas, _ = pizarra.pipeline_default()
    for p in piezas:
        if p.kind == "component":
            assert p.code_path, f"componente {p.id} sin code_path"


def test_to_dot_renders_all_nodes_and_edges():
    piezas, flechas = pizarra.pipeline_default()
    dot = pizarra.to_dot(piezas, flechas)
    assert dot.startswith("digraph Pizarra")
    for p in piezas:
        assert f'"{p.id}"' in dot
    for f in flechas:
        assert f'"{f.src}" -> "{f.dst}"' in dot


def test_to_dot_styles_differ_by_kind():
    piezas, flechas = pizarra.pipeline_default()
    dot = pizarra.to_dot(piezas, flechas)
    # Esferas (componentes) = circle, contenidos = box
    assert "shape=circle" in dot
    assert "shape=box" in dot


def test_code_full_path_resolves(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    pieza = pizarra.Pieza(id="x", label="x", kind="component", code_path="foo/bar.py")
    assert pieza.code_full_path() == tmp_path.resolve() / "foo" / "bar.py"


def test_content_pieces_have_no_code_path():
    piezas, _ = pizarra.pipeline_default()
    for p in piezas:
        if p.kind == "content":
            assert p.code_path is None
            assert p.code_full_path() is None
