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

st.set_page_config(page_title="Master", page_icon="🎓", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

st.title("MASTER · ESTADO POR MÓDULO")
st.caption("Vista global del curso. Listo cuando todos los episodios del módulo "
           "tienen guion + PDF + escaleta + audio.")

all_eps = episodes.scan_all()

# Agrupa por módulo en el orden M0..M14
by_mod: dict[str, list[episodes.Episode]] = {m: [] for m in paths.MODULES}
for e in all_eps:
    by_mod.setdefault(e.module, []).append(e)

# Métricas agregadas
n_total = len(by_mod)
n_listo = 0
n_curso = 0
n_vacio = 0
for eps in by_mod.values():
    status, _ = episodes.module_status(eps)
    if status == "listo":
        n_listo += 1
    elif status == "en_curso":
        n_curso += 1
    else:
        n_vacio += 1

c1, c2, c3, c4 = st.columns(4)
c1.metric("Módulos", n_total)
c2.metric("🟢 Listos", n_listo)
c3.metric("🟡 En curso", n_curso)
c4.metric("⚪ Sin empezar", n_vacio)

st.divider()

# Cabecera
hdr = st.columns([1, 4, 2, 2, 2])
hdr[0].markdown("**Módulo**")
hdr[1].markdown("**Episodios**")
hdr[2].markdown("**Estado**")
hdr[3].markdown("**Progreso**")
hdr[4].markdown("**Acción**")
st.divider()

for mod in paths.MODULES:
    eps = by_mod.get(mod, [])
    status, ratio = episodes.module_status(eps)
    badge = episodes.STATUS_BADGE[status]

    n_eps = len(eps)
    n_complete = sum(1 for e in eps if e.complete)
    label = f"{n_complete}/{n_eps} ep. completos · {sum(1 for e in eps if e.kind == 'T')} temas + {sum(1 for e in eps if e.kind == 'M')} M"

    row = st.columns([1, 4, 2, 2, 2])
    row[0].markdown(f"### {mod}")
    row[1].markdown(label)
    row[2].markdown(badge)
    row[3].progress(ratio, text=f"{ratio*100:.0f}%")
    if row[4].button("Abrir →", key=f"open_{mod}", use_container_width=True):
        st.query_params["m"] = mod
        st.switch_page("pages/13_🎬_Modulo.py")

st.divider()
st.caption(
    "🟢 Listo · 🟡 En curso · ⚪ Sin empezar. "
    "Pulsa **Abrir** para entrar al detalle del módulo."
)
