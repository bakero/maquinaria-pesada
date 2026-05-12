"""Página Mapa: grafo de componentes con visualización + edición + chat IA.

El mapa se persiste en `cockpit/components_map.json` (path en la whitelist del
sandbox). Una IA puede sugerir/aplicar cambios solo sobre ese fichero — nunca
sobre el código de la app.

Render: usa `streamlit-flow-component` si está instalado (drag&drop), si no
cae a graphviz solo-lectura.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import ui_map  # noqa: E402
from cockpit.core import ai_client, components_map, sandbox  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402

SLOW_WARNING_S = 120  # 2 minutos

st.set_page_config(page_title="Mapa", page_icon="🗺️", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()


def _extract_json_map(text: str) -> dict | None:
    """Busca un bloque ```json … ``` con campos nodes/edges."""
    import re

    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "nodes" not in data or "edges" not in data:
        return None
    return data


st.title("MAPA DE COMPONENTES")
flow_active = ui_map.has_flow_lib()
st.caption(
    f"Persistido en `{components_map.map_path()}`. Tipos de nodo: "
    "🟦 generator (motor IA) · ⬛ system (pipeline/módulo) · 🟨 generated (output). "
    + ("🎨 Modo **drag&drop** activo (streamlit-flow)."
       if flow_active else
       "📐 Render: graphviz (solo lectura). `pip install streamlit-flow-component` activa drag&drop.")
)

if "_map" not in st.session_state:
    st.session_state["_map"] = components_map.load()
m: components_map.ComponentsMap = st.session_state["_map"]

# ---------------- Grafo ----------------
st.subheader("Vista")
maybe_new = ui_map.render_map(m, key="flow_main")
if maybe_new is not None and flow_active:
    if st.button("💾 Guardar cambios del drag&drop", type="primary"):
        components_map.save(maybe_new)
        st.session_state["_map"] = maybe_new
        st.success("Mapa guardado desde la vista visual.")
        st.rerun()

# ---------------- Edición ----------------
edit_tab, chat_tab = st.tabs(["✏️ Editar (tabla)", "💬 Asistente del mapa"])

with edit_tab:
    st.markdown("#### Nodos")
    node_rows = [
        {"id": n.id, "label": n.label, "kind": n.kind, "description": n.description}
        for n in m.nodes
    ]
    edited_nodes = st.data_editor(
        node_rows,
        num_rows="dynamic",
        column_config={
            "kind": st.column_config.SelectboxColumn(
                options=["system", "generated", "generator"], required=True
            ),
        },
        key="_nodes_editor",
        use_container_width=True,
    )

    st.markdown("#### Aristas")
    node_ids = [n["id"] for n in edited_nodes if n.get("id")]
    edge_rows = [{"src": e.src, "dst": e.dst, "relation": e.relation} for e in m.edges]
    edited_edges = st.data_editor(
        edge_rows,
        num_rows="dynamic",
        column_config={
            "src": st.column_config.SelectboxColumn(options=node_ids, required=True),
            "dst": st.column_config.SelectboxColumn(options=node_ids, required=True),
            "relation": st.column_config.SelectboxColumn(
                options=["uses", "produces", "feeds", "depends_on"], required=True
            ),
        },
        key="_edges_editor",
        use_container_width=True,
    )

    col_s, col_r = st.columns(2)
    if col_s.button("💾 Guardar cambios", type="primary", key="_save_table"):
        try:
            new_map = components_map.ComponentsMap(
                nodes=[
                    components_map.Node(
                        id=r["id"],
                        label=r.get("label", r["id"]),
                        kind=r.get("kind", "system"),
                        description=r.get("description", ""),
                    )
                    for r in edited_nodes
                    if r.get("id")
                ],
                edges=[
                    components_map.Edge(
                        src=r["src"], dst=r["dst"], relation=r.get("relation", "uses")
                    )
                    for r in edited_edges
                    if r.get("src") and r.get("dst")
                ],
            )
            components_map.save(new_map)
            st.session_state["_map"] = new_map
            st.success("Mapa guardado.")
            st.rerun()
        except (KeyError, ValueError) as e:
            st.error(f"No se pudo guardar: {e}")
    if col_r.button("↩ Restaurar mapa por defecto"):
        components_map.save(components_map._default_map())  # noqa: SLF001
        st.session_state["_map"] = components_map.load()
        st.rerun()

with chat_tab:
    st.caption(
        "Conversa con Claude para mejorar el mapa. **Sandbox activo**: el "
        "asistente solo puede modificar `cockpit/components_map.json` — nada más. "
        "Modo verbose: streaming visible + aviso si supera 2 min."
    )

    if "_map_chat" not in st.session_state:
        st.session_state["_map_chat"] = []

    for msg in st.session_state["_map_chat"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ejemplo: añade un nodo «RRSS publisher» que consuma out-audio…")
    if prompt:
        st.session_state["_map_chat"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        current_json = json.dumps(m.to_dict(), ensure_ascii=False, indent=2)
        system = (
            "Eres un experto en arquitectura de sistemas. Estás editando el mapa "
            "de componentes de MaquinarIA Pesada. "
            + sandbox.explain_policy()
            + "\n\nResponde SIEMPRE en español de España. Cuando propongas un "
            "cambio al mapa, devuélvelo como un bloque ```json``` con la "
            "estructura COMPLETA del mapa actualizado (campos: nodes, edges). "
            "Si la petición no es sobre el mapa, contesta normal sin bloque JSON."
        )
        user = (
            f"## Estado actual del mapa\n```json\n{current_json}\n```\n\n"
            f"## Petición del usuario\n{prompt}"
        )
        try:
            with st.chat_message("assistant"):
                status = st.status("Conectando con Claude…", expanded=True)
                timer = status.empty()
                area = status.empty()
                t0 = time.monotonic()
                chunks: list[str] = []
                usage = None
                warned = False
                for tag, payload in ai_client.improve_with_claude_stream(
                    system=system,
                    user=user,
                    source="page:mapa:chat",
                    kind="update",
                    max_tokens=3000,
                ):
                    elapsed = time.monotonic() - t0
                    marker = "🟢" if elapsed < 30 else "🟡" if elapsed < SLOW_WARNING_S else "🔴"
                    if tag == "text":
                        chunks.append(payload)  # type: ignore[arg-type]
                        area.markdown("".join(chunks))
                    elif tag == "usage":
                        usage = payload
                    timer.caption(
                        f"{marker} {elapsed:.1f}s · "
                        f"{sum(len(c) for c in chunks) // 4} tokens recibidos"
                    )
                    if not warned and elapsed > SLOW_WARNING_S:
                        warned = True
                        st.warning(
                            f"⏱️ La generación lleva {elapsed:.0f}s "
                            f"(>{SLOW_WARNING_S}s). Considera cancelar y usar haiku."
                        )

                text = "".join(chunks)
                if usage is not None:
                    status.update(
                        label=(
                            f"✅ Completado · {usage.input_tokens} in / "
                            f"{usage.output_tokens} out · ${usage.cost_usd:.4f}"
                        ),
                        state="complete",
                    )

                proposed = _extract_json_map(text)
                if proposed is not None:
                    st.divider()
                    st.markdown("**Vista previa de la propuesta:**")
                    try:
                        preview_map = components_map.ComponentsMap.from_dict(proposed)
                        st.graphviz_chart(
                            components_map.to_dot(preview_map),
                            use_container_width=True,
                        )
                        apply_key = f"_apply_{len(st.session_state['_map_chat'])}"
                        if st.button("✅ Aplicar este mapa", key=apply_key):
                            allowed, reason = sandbox.is_write_allowed(
                                components_map.map_path()
                            )
                            if not allowed:
                                st.error(f"Bloqueado por sandbox: {reason}")
                            else:
                                components_map.save(preview_map)
                                st.session_state["_map"] = preview_map
                                st.success("Mapa aplicado.")
                                st.rerun()
                    except (TypeError, KeyError) as e:
                        st.warning(f"La propuesta no es un mapa válido: {e}")

            st.session_state["_map_chat"].append(
                {"role": "assistant", "content": text}
            )
        except ai_client.AIClientError as e:
            st.error(f"Error: {e}")
