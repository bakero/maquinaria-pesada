"""Wrapper de render visual del mapa de componentes.

Estrategia:
  1. Si está instalado `streamlit-flow-component` (xyflow/react-flow), renderiza
     un mapa drag&drop interactivo.
  2. Si no, cae al fallback con `st.graphviz_chart` (siempre disponible).

Para activar drag&drop:
    pip install streamlit-flow-component

El wrapper convierte nuestro ComponentsMap a formato react-flow (nodes con
id/type/position/data, edges con id/source/target/label) y devuelve eventos de
edición si los hay (nodos añadidos, movidos, eliminados).
"""
from __future__ import annotations

from cockpit.core import components_map as cm


def has_flow_lib() -> bool:
    try:
        import streamlit_flow  # noqa: F401
        return True
    except ImportError:
        return False


def render_map(m: cm.ComponentsMap, *, key: str = "flow_map") -> cm.ComponentsMap | None:
    """Renderiza el mapa. Devuelve un mapa MODIFICADO si el usuario hizo cambios,
    o None si no hubo cambios o se usó el fallback.

    El fallback (graphviz) no es editable visualmente; los cambios deben hacerse
    en la pestaña «✏️ Editar».
    """
    import streamlit as st

    if has_flow_lib():
        return _render_flow(m, key=key)

    # Fallback: graphviz solo-lectura
    st.graphviz_chart(cm.to_dot(m), use_container_width=True)
    st.caption(
        "💡 Instala `streamlit-flow-component` para habilitar edición drag&drop "
        "visual del mapa."
    )
    return None


def _render_flow(m: cm.ComponentsMap, *, key: str) -> cm.ComponentsMap | None:
    """Render real con streamlit-flow. Aislamos imports para que el fallback
    nunca falle por dependencias rotas."""
    import streamlit as st

    try:
        from streamlit_flow import streamlit_flow
        from streamlit_flow.elements import StreamlitFlowEdge, StreamlitFlowNode
        from streamlit_flow.layouts import LayeredLayout
        from streamlit_flow.state import StreamlitFlowState
    except ImportError as e:
        st.warning(f"streamlit-flow detectado pero falló al importar: {e}. Uso fallback.")
        st.graphviz_chart(cm.to_dot(m), use_container_width=True)
        return None

    # Colores por kind (igual que graphviz).
    style_by_kind = {
        "generator": {"backgroundColor": "#dbeafe", "color": "#111"},
        "system": {"backgroundColor": "#1f2937", "color": "white"},
        "generated": {"backgroundColor": "#fef3c7", "color": "#111"},
    }

    nodes = []
    for i, n in enumerate(m.nodes):
        nodes.append(
            StreamlitFlowNode(
                id=n.id,
                pos=(150 * (i % 4), 100 * (i // 4)),
                data={"content": f"**{n.label}**\n\n_{n.kind}_"},
                node_type="default",
                source_position="right",
                target_position="left",
                style=style_by_kind.get(n.kind, {}),
                draggable=True,
            )
        )
    edges = [
        StreamlitFlowEdge(
            id=f"{i}-{e.src}-{e.dst}",
            source=e.src,
            target=e.dst,
            label=e.relation,
            animated=False,
        )
        for i, e in enumerate(m.edges)
    ]

    state_key = f"_{key}_state"
    if state_key not in st.session_state:
        st.session_state[state_key] = StreamlitFlowState(nodes=nodes, edges=edges)

    new_state = streamlit_flow(
        key=key,
        state=st.session_state[state_key],
        layout=LayeredLayout(direction="right"),
        fit_view=True,
        get_node_on_click=True,
        get_edge_on_click=True,
        show_minimap=True,
        show_controls=True,
        allow_new_edges=True,
        animate_new_edges=True,
        enable_node_menu=True,
        enable_edge_menu=True,
        enable_pane_menu=True,
    )

    # Detectar cambios y reconstruir ComponentsMap si el usuario tocó algo.
    if new_state is None:
        return None
    return _state_to_map(new_state, m)


def _state_to_map(state, original: cm.ComponentsMap) -> cm.ComponentsMap | None:
    """Convierte el state de streamlit-flow a ComponentsMap.

    Mantiene `kind` y `description` del mapa original (los nodos nuevos creados
    por drag desde el menú se marcan como 'system' por defecto).
    """
    try:
        new_nodes = []
        kind_by_id = {n.id: n.kind for n in original.nodes}
        desc_by_id = {n.id: n.description for n in original.nodes}
        for sn in getattr(state, "nodes", []):
            nid = sn.id
            label = sn.data.get("content", nid).split("\n")[0].strip("* ")
            new_nodes.append(
                cm.Node(
                    id=nid,
                    label=label,
                    kind=kind_by_id.get(nid, "system"),
                    description=desc_by_id.get(nid, ""),
                )
            )
        new_edges = [
            cm.Edge(
                src=se.source,
                dst=se.target,
                relation=getattr(se, "label", "") or "uses",
            )
            for se in getattr(state, "edges", [])
        ]
        return cm.ComponentsMap(nodes=new_nodes, edges=new_edges)
    except (AttributeError, KeyError):
        return None
