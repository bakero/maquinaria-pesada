"""Página Módulo — listado de episodios de un módulo (M + Tn).

Recibe el módulo por query param ?m=Mn. Si no se pasa, ofrece selector.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import episodes, paths  # noqa: E402
from cockpit.core.verifications import episode_has_errors  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402

st.set_page_config(page_title="Módulo", page_icon="🎬", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

# --- Selector de módulo ---
qp_mod = st.query_params.get("m")
modulos = paths.MODULES
default_idx = modulos.index(qp_mod) if qp_mod in modulos else 0

top = st.columns([4, 2])
with top[0]:
    st.title("MÓDULO · DETALLE")
with top[1]:
    selected = st.selectbox("Módulo", modulos, index=default_idx, key="mod_select")
    if selected != qp_mod:
        st.query_params["m"] = selected

mod = selected
eps = episodes.scan_module(mod)
status, ratio = episodes.module_status(eps)

# Resumen
c1, c2, c3, c4 = st.columns(4)
c1.metric("Módulo", mod)
c2.metric("Estado", episodes.STATUS_BADGE[status])
c3.metric("Progreso", f"{ratio*100:.0f}%")
c4.metric("Episodios", len(eps))

st.divider()

# Tabla de episodios
if not eps:
    st.warning("No se ha detectado ningún episodio para este módulo.")
else:
    hdr = st.columns([1, 5, 1, 1, 1, 1, 1, 2])
    hdr[0].markdown("**Tipo**")
    hdr[1].markdown("**Episodio**")
    hdr[2].markdown("**📕 PDF**")
    hdr[3].markdown("**📝 Guion**")
    hdr[4].markdown("**🗂️ Esc.**")
    hdr[5].markdown("**🎧 Audio**")
    hdr[6].markdown("**Errores**")
    hdr[7].markdown("**Acción**")
    st.divider()

    for e in eps:
        row = st.columns([1, 5, 1, 1, 1, 1, 1, 2])
        kind_badge = "🅼 Módulo" if e.kind == "M" else f"🅃 T{e.number}"
        row[0].markdown(kind_badge)
        row[1].markdown(f"**{e.id}**  \n{e.slug.replace('_', ' ') or '—'}")
        row[2].markdown("✅" if e.has("pdf") else "❌")
        row[3].markdown("✅" if e.has("guion") else "❌")
        row[4].markdown("✅" if e.has("escaleta") else "❌")
        row[5].markdown("✅" if e.has("audio") else "❌")
        has_errs = episode_has_errors(e)
        row[6].markdown("🔴 Sí" if has_errs else "🟢 No")
        if row[7].button("Abrir →", key=f"ep_{e.id}", use_container_width=True):
            st.query_params["ep"] = e.id
            st.switch_page("pages/14_📼_Episodio.py")

st.divider()

# Volver al master
col = st.columns([1, 4, 1])
if col[0].button("← Master", use_container_width=True):
    st.switch_page("pages/0_🎓_Master.py")
