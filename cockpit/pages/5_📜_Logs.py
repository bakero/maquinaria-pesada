from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402
from cockpit.connectors.base import SourceConnector  # noqa: E402

st.set_page_config(page_title="Logs", page_icon="📜", layout="wide")
st.title("📜 Logs de producción")

src: SourceConnector = connectors.get("log")  # type: ignore[assignment]

logs = src.list_items()
if not logs:
    st.info("No se han encontrado logs.")
    st.stop()

names = [p.name for p in logs]
default_idx = len(names) - 1  # last by mtime not guaranteed, but we sort by name
sel_name = st.selectbox("Log", names, index=default_idx)
sel = next(p for p in logs if p.name == sel_name)

auto = st.toggle("Auto-refresh cada 5 s", value=False)
if auto:
    try:
        from streamlit_autorefresh import st_autorefresh  # type: ignore
        st_autorefresh(interval=5000, key="log_refresh")
    except ImportError:
        st.warning("Instala `streamlit-autorefresh` para auto-refresh.")

st.divider()
src.render_viewer(sel)
