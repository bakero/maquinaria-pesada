"""Página API Keys: estado y verificación de proveedores."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import api_keys, paths  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import page_header  # noqa: E402
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="API Keys", page_icon="🔑", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

page_header(
    "API Keys",
    eyebrow="Sistema",
    subtitle=(
        f"Estado de credenciales de los proveedores. Se leen de `{paths.env_file()}` "
        "+ entorno. Las claves no se muestran ni se persisten."
    ),
    help_page_id="api_keys",
)

force = st.button("🔄 Re-verificar ahora (ignora caché 5 min)")
items = api_keys.check_all(force=force)

cols = st.columns(len(items))
for col, st_info in zip(cols, items, strict=False):
    with col:
        if not st_info.present:
            badge = "⚪ ausente"
        elif st_info.ok:
            badge = "🟢 OK"
        else:
            badge = "🔴 ERROR"
        st.markdown(f"### {st_info.provider}")
        st.write(f"**Estado:** {badge}")
        st.code(st_info.env_var, language="text")
        if st_info.detail:
            st.caption(st_info.detail)
        if st_info.present:
            st.caption(f"Latencia: {st_info.latency_ms} ms")
        st.caption(f"Comprobado: {st_info.checked_at}")

st.divider()
st.subheader("Resumen")
ok = sum(1 for i in items if i.ok)
present = sum(1 for i in items if i.present)
st.metric("Operativas", f"{ok}/{len(items)}")
st.metric("Presentes en .env", f"{present}/{len(items)}")

render_improve_block(
    source="page:api_keys",
    context=(
        "Página que verifica el estado de las API keys de Anthropic, OpenAI y "
        "ElevenLabs llamando a un endpoint barato y cacheando 5 minutos. "
        "Hoy solo soporta esos 3 proveedores; el chequeo es síncrono."
    ),
    default_prompt=(
        "Propón 3 mejoras concretas a este sistema de verificación de keys "
        "(p. ej. chequeos asíncronos, alertas de expiración, nuevos proveedores)."
    ),
    kind="update",
)
