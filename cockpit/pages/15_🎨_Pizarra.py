"""Pizarra — vista visual del generador.

Esferas = componentes ejecutables (Claude, scripts del pipeline).
Cuadrados = contenidos (PDF, GUION, ESCALETA, EPISODIO).
Flechas conectan: componente → contenido producido → componente siguiente.

Al seleccionar una esfera se muestra su código fuente debajo.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import pizarra  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402

st.set_page_config(page_title="Pizarra", page_icon="🎨", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

st.title("PIZARRA · GENERADOR VISUAL")
st.caption(
    "Esferas = componentes (Claude + scripts). "
    "Cuadrados = contenidos. Selecciona un componente para revisar su código."
)

piezas, flechas = pizarra.pipeline_default()

# --- Render gráfico ---
dot = pizarra.to_dot(piezas, flechas)
st.graphviz_chart(dot, use_container_width=True)

st.divider()

# --- Inspector de componentes ---
left, right = st.columns([1, 3])
componentes = [p for p in piezas if p.kind == "component"]
contenidos = [p for p in piezas if p.kind == "content"]

with left:
    st.markdown("### Componentes")
    sel_id = st.radio(
        "Seleccionar",
        [p.id for p in componentes],
        format_func=lambda pid: next(
            (f"{p.icon} {p.label}" for p in componentes if p.id == pid), pid
        ),
        key="pizarra_sel",
    )

    st.markdown("### Contenidos")
    for c in contenidos:
        st.markdown(f"- {c.icon} **{c.label}**  \n  <small>{c.description}</small>",
                    unsafe_allow_html=True)

selected = next((p for p in componentes if p.id == sel_id), None)

with right:
    if selected is None:
        st.info("Selecciona un componente.")
    else:
        st.markdown(f"## {selected.icon} {selected.label}")
        st.caption(selected.description)

        # Conexiones entrantes y salientes
        entrantes = [f for f in flechas if f.dst == selected.id]
        salientes = [f for f in flechas if f.src == selected.id]
        cols = st.columns(2)
        with cols[0]:
            st.markdown("**Entradas**")
            if not entrantes:
                st.caption("—")
            for f in entrantes:
                p = next((x for x in piezas if x.id == f.src), None)
                if p:
                    st.markdown(f"- {p.icon} {p.label}")
        with cols[1]:
            st.markdown("**Salidas**")
            if not salientes:
                st.caption("—")
            for f in salientes:
                p = next((x for x in piezas if x.id == f.dst), None)
                if p:
                    st.markdown(f"- {p.icon} {p.label}")

        st.divider()

        # Código del componente
        code_path = selected.code_full_path()
        if code_path is None:
            st.warning("Este componente no tiene path de código asociado.")
        elif not code_path.exists():
            st.error(f"No se encuentra el código: `{selected.code_path}`")
        else:
            st.markdown(f"**Código:** `{selected.code_path}`")
            try:
                src = code_path.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                st.error(f"Error leyendo el código: {e}")
            else:
                lines = src.count("\n") + 1
                st.caption(f"{lines:,} líneas · {len(src):,} chars")
                if len(src) > 120_000:
                    st.info("Archivo largo: se muestran las primeras 3 000 líneas.")
                    src = "\n".join(src.splitlines()[:3000])
                st.code(src, language="python")

st.divider()
st.caption(
    "Nota: el pipeline mostrado es el flujo canónico de generación. "
    "Para una vista más libre (nodos editables, IA del mapa) usa la página 🗺️ Mapa."
)
