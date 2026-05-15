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
from cockpit.ui_components import (  # noqa: E402
    Stat,
    page_header,
    section,
    stat_grid,
    status_pill,
)

st.set_page_config(page_title="Módulo", page_icon="🎬", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

# --- Selector de módulo ---
qp_mod = st.query_params.get("m")
modulos = paths.MODULES
default_idx = modulos.index(qp_mod) if qp_mod in modulos else 0

head = st.columns([4, 2])
with head[0]:
    page_header(
        "Detalle del módulo",
        eyebrow="Módulo",
        subtitle="Inspecciona qué episodios están listos, qué falta y dónde hay errores.",
    )
with head[1]:
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    selected = st.selectbox(
        "Módulo",
        modulos,
        index=default_idx,
        key="mod_select",
        label_visibility="collapsed",
    )
    if selected != qp_mod:
        st.query_params["m"] = selected

mod = selected
eps = episodes.scan_module(mod)
status, ratio = episodes.module_status(eps)

_STATUS_KIND = {"listo": "ok", "en_curso": "warn", "sin_empezar": "neutral"}
_STATUS_LABEL = {"listo": "Listo", "en_curso": "En curso", "sin_empezar": "Sin empezar"}

stat_grid([
    Stat("Módulo", mod),
    Stat("Estado", _STATUS_LABEL[status], color="ok" if status == "listo" else "warn" if status == "en_curso" else "default"),
    Stat("Progreso", f"{ratio*100:.0f}%"),
    Stat("Episodios", str(len(eps))),
])

section("Episodios", subtitle="Cada fila muestra qué contenidos están producidos.")

if not eps:
    st.warning("No se ha detectado ningún episodio para este módulo.")
else:
    for e in eps:
        with st.container(border=True):
            row = st.columns([0.9, 4, 4, 1.5, 1.4])

            kind_badge = "M · Módulo" if e.kind == "M" else f"T{e.number} · Tema"
            row[0].markdown(
                f"<div style='font-family:\"JetBrains Mono\", monospace;"
                f"color:var(--mp-primary); font-weight:600;'>{e.id}</div>"
                f"<div style='color:var(--mp-text-mute); font-size:0.78rem;'>{kind_badge}</div>",
                unsafe_allow_html=True,
            )
            row[1].markdown(
                f"<div style='font-weight:500;'>{e.slug.replace('_',' ') or '—'}</div>",
                unsafe_allow_html=True,
            )

            content_pills = []
            for kind, icon in (("pdf","📕"),("guion","📝"),("escaleta","🗂️"),("audio","🎧")):
                if e.has(kind):
                    content_pills.append(status_pill(f"{icon} {kind}", kind="ok"))
                else:
                    content_pills.append(status_pill(f"{icon} {kind}", kind="neutral"))
            row[2].markdown(
                "<div style='display:flex; flex-wrap:wrap; gap:4px;'>"
                + "".join(content_pills)
                + "</div>",
                unsafe_allow_html=True,
            )

            has_errs = episode_has_errors(e)
            row[3].markdown(
                status_pill("Errores" if has_errs else "OK", kind="fail" if has_errs else "ok"),
                unsafe_allow_html=True,
            )

            if row[4].button("Abrir →", key=f"ep_{e.id}", use_container_width=True):
                st.query_params["ep"] = e.id
                st.switch_page("pages/14_📼_Episodio.py")

st.divider()

if st.button("← Volver al Master"):
    st.switch_page("pages/0_🎓_Master.py")
