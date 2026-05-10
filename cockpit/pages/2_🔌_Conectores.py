from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402

st.set_page_config(page_title="Conectores", page_icon="🔌", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()
st.title("CONECTORES")
st.caption(
    "Servicios externos, pipelines del repo y tipos de fuente. "
    "Añade un fichero en `cockpit/connectors/{services,pipelines,sources}/` para registrar uno nuevo."
)

CATEGORIES = [
    ("service", "Servicios externos"),
    ("pipeline", "Pipelines (scripts del repo)"),
    ("source", "Fuentes de contenido"),
]

for cat, title in CATEGORIES:
    items = connectors.by_category(cat)  # type: ignore[arg-type]
    st.header(f"{title} ({len(items)})")
    if not items:
        st.info("Ninguno registrado.")
        continue
    cols = st.columns(min(3, len(items)))
    for idx, c in enumerate(items):
        with cols[idx % len(cols)]:
            with st.container(border=True):
                c.render_card()
                with st.expander("Configuración"):
                    c.render_config()
    st.divider()
