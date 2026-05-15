"""Página Master — vista global de todos los módulos.

Lista los 15 módulos con su estado: 🟢 Listo · 🟡 En curso (%) · ⚪ Sin empezar.
Listo = todos los episodios (M + Tn) tienen los 4 contenidos.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import episodes, paths  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import (  # noqa: E402
    Stat,
    page_header,
    section,
    stat_grid,
    status_pill,
)

st.set_page_config(page_title="Master", page_icon="🎓", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

page_header(
    "Estado por módulo",
    eyebrow="Master",
    subtitle=(
        "Vista global del curso. Un módulo está listo cuando todos sus "
        "episodios — M principal + temas Tₙ — tienen guion, PDF, escaleta y audio."
    ),
)

all_eps = episodes.scan_all()
modules_meta = {m["id"]: m for m in episodes.modules_meta()}

by_mod: dict[str, list[episodes.Episode]] = {m: [] for m in paths.MODULES}
for e in all_eps:
    by_mod.setdefault(e.module, []).append(e)

n_total = len(by_mod)
n_listo = n_curso = n_vacio = 0
for eps in by_mod.values():
    status, _ = episodes.module_status(eps)
    if status == "listo":
        n_listo += 1
    elif status == "en_curso":
        n_curso += 1
    else:
        n_vacio += 1

stat_grid([
    Stat("Módulos", str(n_total)),
    Stat("Listos", str(n_listo), color="ok"),
    Stat("En curso", str(n_curso), color="warn"),
    Stat("Sin empezar", str(n_vacio), color="default"),
])

section("Módulos", subtitle="Pulsa cualquier módulo para abrir su detalle.")


_STATUS_KIND = {"listo": "ok", "en_curso": "warn", "sin_empezar": "neutral"}
_STATUS_LABEL = {"listo": "Listo", "en_curso": "En curso", "sin_empezar": "Sin empezar"}


for mod in paths.MODULES:
    eps = by_mod.get(mod, [])
    status, ratio = episodes.module_status(eps)
    meta = modules_meta.get(mod, {})
    name = meta.get("name", mod)
    short = meta.get("short", "")
    n_eps = len(eps)
    n_complete = sum(1 for e in eps if e.complete)
    n_m = sum(1 for e in eps if e.kind == "M")
    n_t = sum(1 for e in eps if e.kind == "T")

    pill = status_pill(_STATUS_LABEL[status], kind=_STATUS_KIND[status])  # type: ignore[arg-type]
    progress_pct = f"{ratio * 100:.0f}%"

    with st.container(border=True):
        head = st.columns([0.7, 4, 1.6, 1.4])
        head[0].markdown(
            f"<div style='font-family: \"JetBrains Mono\", monospace;"
            f"font-size:1.1rem; color: var(--mp-primary); font-weight:600;'>"
            f"{mod}</div>",
            unsafe_allow_html=True,
        )
        head[1].markdown(
            f"<div style='font-weight:600; font-size:1.02rem;'>{name}</div>"
            f"<div style='color: var(--mp-text-mute); font-size: 0.85rem;'>{short}</div>",
            unsafe_allow_html=True,
        )
        head[2].markdown(pill, unsafe_allow_html=True)
        if head[3].button("Abrir →", key=f"open_{mod}", use_container_width=True):
            st.query_params["m"] = mod
            st.switch_page("pages/13_🎬_Modulo.py")

        meta_row = st.columns([4, 1.4])
        with meta_row[0]:
            st.progress(ratio, text=f"{n_complete}/{n_eps} episodios completos · {progress_pct}")
        with meta_row[1]:
            st.markdown(
                f"<div style='text-align:right; color:var(--mp-text-mute); "
                f"font-size:0.82rem; padding-top:6px;'>"
                f"{n_m} M · {n_t} temas</div>",
                unsafe_allow_html=True,
            )

st.caption(
    "🟢 Listo · todos los contenidos producidos · "
    "🟡 En curso · algún contenido producido · "
    "⚪ Sin empezar · ningún contenido aún."
)
