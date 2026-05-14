"""Tests del wrapper ui_map. No depende de tener streamlit-flow instalado."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit import ui_map  # noqa: E402
from cockpit.core import components_map as cm  # noqa: E402


def test_has_flow_lib_devuelve_bool():
    # En CI no estará instalado: queremos que devuelva False sin romper.
    result = ui_map.has_flow_lib()
    assert isinstance(result, bool)


def test_state_to_map_extrae_label_de_data_content():
    import types

    state = types.SimpleNamespace(
        nodes=[
            types.SimpleNamespace(id="x", data={"content": "**Mi label**\n\n_system_"}),
            types.SimpleNamespace(id="y", data={"content": "Otro\n\n_generator_"}),
        ],
        edges=[
            types.SimpleNamespace(source="x", target="y", label="uses"),
        ],
    )
    original = cm.ComponentsMap(
        nodes=[
            cm.Node("x", "X", "system", "desc-x"),
            cm.Node("y", "Y", "generator", "desc-y"),
        ],
        edges=[],
    )
    result = ui_map._state_to_map(state, original)  # noqa: SLF001
    assert result is not None
    assert len(result.nodes) == 2
    by_id = {n.id: n for n in result.nodes}
    assert by_id["x"].label == "Mi label"
    assert by_id["x"].kind == "system"  # preserva del original
    assert by_id["x"].description == "desc-x"
    assert len(result.edges) == 1
    assert result.edges[0].relation == "uses"


def test_state_to_map_nodos_nuevos_caen_a_system_por_defecto():
    import types

    state = types.SimpleNamespace(
        nodes=[
            types.SimpleNamespace(id="nuevo", data={"content": "Recien creado"}),
        ],
        edges=[],
    )
    original = cm.ComponentsMap(nodes=[], edges=[])
    result = ui_map._state_to_map(state, original)  # noqa: SLF001
    assert result is not None
    assert result.nodes[0].kind == "system"
    assert result.nodes[0].description == ""


def test_state_to_map_robusto_ante_attrs_faltantes():
    import types

    state = types.SimpleNamespace(nodes="not-iterable-correctly")
    result = ui_map._state_to_map(state, cm.ComponentsMap())  # noqa: SLF001
    assert result is None
