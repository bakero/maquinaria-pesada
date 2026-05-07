from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import state  # noqa: E402

st.set_page_config(page_title="Estado", page_icon="📊", layout="wide")
st.title("📊 Estado de producción")

states = state.scan()

rows = []
for s in states:
    rows.append(
        {
            "Módulo": s.module,
            "PDF": "✅" if s.pdf_ok else "❌",
            "Guion": "✅" if s.guion_ok else "❌",
            "Audio": "✅" if s.audio_ok else "❌",
            "Vídeo": "✅" if s.video_ok else "❌",
            "Log": "✅" if s.log_ok else "❌",
            "Completo": "✅" if s.complete else "—",
        }
    )

st.dataframe(rows, use_container_width=True, hide_index=True)

c1, c2, c3 = st.columns(3)
total = len(states)
completos = sum(1 for s in states if s.complete)
con_audio = sum(1 for s in states if s.audio_ok)
c1.metric("Módulos totales", total)
c2.metric("Con audio", con_audio)
c3.metric("Completos", completos)

st.divider()

view = st.radio("Vista", ["Todos", "Pendientes", "Detalle"], horizontal=True)

if view == "Pendientes":
    pend = state.pendientes(states)
    if not pend:
        st.success("No hay módulos pendientes 🎉")
    for s in pend:
        with st.expander(f"{s.module} — falta: " + ", ".join(
            x for x, ok in [
                ("PDF", s.pdf_ok), ("Guion", s.guion_ok),
                ("Audio", s.audio_ok), ("Vídeo", s.video_ok),
            ] if not ok
        )):
            st.json({
                "pdf": [str(p) for p in s.pdf],
                "guion": [str(p) for p in s.guion],
                "audio": [str(p) for p in s.audio],
                "video": [str(p) for p in s.video],
                "log": [str(p) for p in s.log],
            })

elif view == "Detalle":
    sel = st.selectbox("Módulo", [s.module for s in states])
    s = next(x for x in states if x.module == sel)
    st.json({
        "pdf": [str(p) for p in s.pdf],
        "guion": [str(p) for p in s.guion],
        "audio": [str(p) for p in s.audio],
        "video": [str(p) for p in s.video],
        "log": [str(p) for p in s.log],
    })
