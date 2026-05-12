"""Tests del mapa de componentes."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.core import components_map as cm  # noqa: E402


def test_default_map_tiene_los_tres_tipos_de_nodo():
    m = cm._default_map()  # noqa: SLF001
    kinds = {n.kind for n in m.nodes}
    assert kinds == {"system", "generated", "generator"}


def test_default_map_aristas_referencian_nodos_existentes():
    m = cm._default_map()  # noqa: SLF001
    ids = {n.id for n in m.nodes}
    for e in m.edges:
        assert e.src in ids
        assert e.dst in ids


def test_to_dot_contiene_todos_los_nodos():
    m = cm._default_map()  # noqa: SLF001
    dot = cm.to_dot(m)
    for n in m.nodes:
        assert f'"{n.id}"' in dot
    assert dot.startswith("digraph G {")


def test_add_node_rechaza_duplicado():
    m = cm.ComponentsMap(nodes=[cm.Node("x", "X", "system")])
    with pytest.raises(ValueError):
        cm.add_node(m, cm.Node("x", "Otro", "generator"))


def test_add_edge_rechaza_si_falta_nodo():
    m = cm.ComponentsMap(nodes=[cm.Node("a", "A", "system")])
    with pytest.raises(ValueError):
        cm.add_edge(m, cm.Edge("a", "b"))


def test_remove_node_borra_aristas_asociadas():
    m = cm.ComponentsMap(
        nodes=[cm.Node("a", "A", "system"), cm.Node("b", "B", "system")],
        edges=[cm.Edge("a", "b"), cm.Edge("b", "a")],
    )
    cm.remove_node(m, "a")
    assert len(m.nodes) == 1
    assert m.edges == []


def test_save_load_roundtrip(tmp_path, monkeypatch):
    target = tmp_path / "components_map.json"
    monkeypatch.setattr(cm, "map_path", lambda: target)

    original = cm.ComponentsMap(
        nodes=[cm.Node("x", "X", "generator", "desc")],
        edges=[],
    )
    cm.save(original)
    loaded = cm.load()
    assert len(loaded.nodes) == 1
    assert loaded.nodes[0].id == "x"
    assert loaded.nodes[0].description == "desc"


def test_load_inexistente_devuelve_default(tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "map_path", lambda: tmp_path / "no.json")
    m = cm.load()
    assert len(m.nodes) > 0
