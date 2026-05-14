from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402
from cockpit.connectors.base import SourceConnector  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Logs", page_icon="📜", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()
st.title("LOGS DE PRODUCCIÓN")

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


def _tail_for_ai() -> str:
    try:
        text = sel.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"(no se pudo leer: {e})"
    lines = text.splitlines()
    return "\n".join(lines[-150:])


render_improve_block(
    source=f"log:{sel.name}",
    context=(
        f"Log de producción «{sel.name}» ({sel.stat().st_size} bytes). "
        "Al pulsar Generar, se añaden las últimas 150 líneas como contexto."
    ),
    extra_context_builder=_tail_for_ai,
    title="✨ Diagnóstico con IA",
    default_prompt=(
        "Analiza estas últimas líneas del log y detecta: errores recurrentes, "
        "warnings que ignorar, próximas acciones recomendadas."
    ),
    kind="improvement",
)
