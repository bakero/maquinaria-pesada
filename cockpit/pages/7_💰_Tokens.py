"""Página Tokens: consumo agregado de IA por modelo / kind / source."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import paths, usage_tracker  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import page_header  # noqa: E402
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Tokens", page_icon="💰", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()


def _to_rows(bucket: dict) -> list[dict]:
    rows = []
    for key, slot in sorted(bucket.items(), key=lambda kv: kv[1]["cost"], reverse=True):
        rows.append(
            {
                "key": key,
                "calls": slot["calls"],
                "in": slot["in"],
                "out": slot["out"],
                "cost_usd": round(slot["cost"], 4),
            }
        )
    return rows

log_path = paths.ai_usage_log()
page_header(
    "Consumo de tokens y coste",
    eyebrow="Coste IA",
    subtitle=f"Fuente: `{log_path}`. Cada llamada IA via ai_client se registra aquí.",
    help_page_id="tokens",
)

if not log_path.exists():
    st.info(
        "Aún no hay eventos registrados. Lanza una mejora con IA o un check de API "
        "para empezar a poblar `ai_usage.jsonl`."
    )
else:
    events = list(usage_tracker.iter_events())
    if not events:
        st.info("El log existe pero está vacío.")
    else:
        agg = usage_tracker.aggregate(events)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Llamadas", agg["total_calls"])
        c2.metric("Tokens IN", f"{agg['total_input_tokens']:,}")
        c3.metric("Tokens OUT", f"{agg['total_output_tokens']:,}")
        c4.metric("Coste USD", f"${agg['total_cost_usd']:.4f}")

        st.divider()
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Por modelo")
            st.dataframe(_to_rows(agg["by_model"]), use_container_width=True)
            st.subheader("Por tipo (kind)")
            st.dataframe(_to_rows(agg["by_kind"]), use_container_width=True)
        with col_r:
            st.subheader("Por origen (source)")
            st.dataframe(_to_rows(agg["by_source"]), use_container_width=True)

        st.divider()
        st.subheader("Últimos 50 eventos")
        st.dataframe(events[-50:][::-1], use_container_width=True)

render_improve_block(
    source="page:tokens",
    context=(
        "Dashboard que lee logs/ai_usage.jsonl y agrega por modelo, kind y source. "
        "Muestra totales y últimos 50 eventos. No tiene gráficos ni alertas de "
        "presupuesto."
    ),
    default_prompt=(
        "Propón mejoras al dashboard: gráficos relevantes, alertas cuando coste "
        "diario supere umbral, exportación a CSV, etc. Máx 5 ideas concretas."
    ),
    kind="update",
)
