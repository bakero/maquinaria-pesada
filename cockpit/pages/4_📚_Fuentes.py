from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402
from cockpit.connectors.base import SourceConnector  # noqa: E402

st.set_page_config(page_title="Fuentes", page_icon="📚", layout="wide")
st.title("📚 Fuentes de contenido")

sources = [c for c in connectors.by_category("source") if isinstance(c, SourceConnector)]
if not sources:
    st.warning("No hay fuentes registradas.")
    st.stop()

labels = {s.id: f"{s.icon} {s.label}" for s in sources}
sel = st.radio(
    "Tipo",
    options=[s.id for s in sources],
    format_func=lambda i: labels[i],
    horizontal=True,
)
src: SourceConnector = connectors.get(sel)  # type: ignore[assignment]

st.caption(src.description)

items = src.list_items()
if not items:
    st.info(f"Sin items en este tipo. Verifica que las rutas existen en el repo.")
    st.stop()

filter_text = st.text_input("Filtrar por nombre (substring)", "")
filtered = [p for p in items if filter_text.lower() in p.name.lower()] if filter_text else items
st.caption(f"{len(filtered)} de {len(items)} items")

if not filtered:
    st.info("Ningún item coincide con el filtro.")
    st.stop()

picked_name = st.selectbox("Elegir", [p.name for p in filtered])
picked = next(p for p in filtered if p.name == picked_name)

st.divider()
src.render_viewer(picked)
