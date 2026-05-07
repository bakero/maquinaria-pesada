from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import log_parser, state  # noqa: E402

st.set_page_config(page_title="Estado", page_icon="📊", layout="wide")
st.title("📊 Estado de producción")
st.caption("Pulsa cualquier ✅/❌ para ver el resumen de validaciones de la última ejecución.")

states = state.scan()

# ----- Métricas generales -----
total = len(states)
completos = sum(1 for s in states if s.complete)
con_audio = sum(1 for s in states if s.audio_ok)
c1, c2, c3 = st.columns(3)
c1.metric("Módulos totales", total)
c2.metric("Con audio", con_audio)
c3.metric("Completos", completos)

st.divider()

# ----- Modal -----

@st.dialog("Resumen de validaciones", width="large")
def _show_summary(module: str, category: str) -> None:
    summary = log_parser.parse(module, category)
    st.subheader(f"{module} · {category.upper()}")

    if summary.log_path is None:
        st.warning("No hay log de producción para este módulo.")
        st.caption(
            "Espera un log .log en `episodios/`, `output/` o la raíz del repo "
            f"con el token de módulo `{module}` en el nombre."
        )
        return

    cols = st.columns(3)
    cols[0].markdown(f"**Log**\n\n`{summary.log_path.name}`")
    cols[1].markdown(
        f"**Última ejecución**\n\n"
        f"{summary.log_mtime.strftime('%Y-%m-%d %H:%M:%S') if summary.log_mtime else '—'}"
    )
    badge = {"ok": "🟢 OK", "fail": "🔴 con errores", "no-data": "⚪ sin datos"}[summary.status]
    cols[2].markdown(f"**Estado**\n\n{badge}")

    if summary.first_ts or summary.last_ts:
        st.caption(f"Run: {summary.first_ts or '—'}  →  {summary.last_ts or '—'}")

    st.metric("Líneas relevantes", summary.matched_lines)

    if summary.matched_lines == 0:
        st.info(
            "El log existe pero no contiene líneas relacionadas con esta categoría. "
            "Pulsa el icono de **Log** para ver el log completo."
        )
        return

    if summary.errors:
        with st.expander(f"❌ Errores ({len(summary.errors)})", expanded=True):
            for e in summary.errors:
                st.code(e, language="log")

    if summary.warnings:
        with st.expander(f"⚠️ Warnings ({len(summary.warnings)})"):
            for w in summary.warnings:
                st.code(w, language="log")

    if summary.ok_signals:
        with st.expander(f"✅ Señales OK ({len(summary.ok_signals)})"):
            for s in summary.ok_signals:
                st.code(s, language="log")

    if summary.sample:
        with st.expander("📋 Muestra de líneas relevantes"):
            st.code("\n".join(summary.sample), language="log")

    st.caption(f"Log path completo: `{summary.log_path}`")


# ----- Tabla con iconos clicables -----

CATEGORIES = [
    ("pdf",   "PDF"),
    ("guion", "Guion"),
    ("audio", "Audio"),
    ("video", "Vídeo"),
    ("log",   "Log"),
]

hdr = st.columns([1, 1, 1, 1, 1, 1, 1])
hdr[0].markdown("**Módulo**")
for i, (_, label) in enumerate(CATEGORIES):
    hdr[i + 1].markdown(f"**{label}**")
hdr[6].markdown("**Completo**")

st.divider()

for s in states:
    row = st.columns([1, 1, 1, 1, 1, 1, 1])
    row[0].markdown(f"**{s.module}**")
    flags = [s.pdf_ok, s.guion_ok, s.audio_ok, s.video_ok, s.log_ok]
    files_per_cat = [s.pdf, s.guion, s.audio, s.video, s.log]
    for i, ((cat_id, _), ok, files) in enumerate(zip(CATEGORIES, flags, files_per_cat)):
        icon = "✅" if ok else "❌"
        label = icon if len(files) <= 1 else f"{icon} ×{len(files)}"
        if row[i + 1].button(
            label,
            key=f"btn_{s.module}_{cat_id}",
            use_container_width=True,
            help=f"Resumen de validaciones de la última ejecución para {s.module}/{cat_id}",
        ):
            _show_summary(s.module, cat_id)
    row[6].markdown("✅" if s.complete else "—")

st.divider()

with st.expander("Detalle por módulo (paths)"):
    sel = st.selectbox("Módulo", [s.module for s in states])
    s = next(x for x in states if x.module == sel)
    st.json({
        "pdf": [str(p) for p in s.pdf],
        "guion": [str(p) for p in s.guion],
        "audio": [str(p) for p in s.audio],
        "video": [str(p) for p in s.video],
        "log": [str(p) for p in s.log],
    })
