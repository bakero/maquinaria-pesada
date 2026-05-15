"""Página Optimizar: aplica el advisor sobre ai_usage.jsonl."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import optimization_advisor, paths, usage_tracker  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import page_header  # noqa: E402
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Optimizar", page_icon="🧠", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

page_header(
    "Optimizar consumo de tokens",
    eyebrow="Coste IA",
    subtitle=(
        "Analiza el histórico de `ai_usage.jsonl` y propone reducciones de gasto "
        "basadas en heurísticas (sin IA)."
    ),
    help_page_id="optimizar",
)

events = list(usage_tracker.iter_events())
if not events:
    st.info(f"Aún no hay eventos en {paths.ai_usage_log()}. Usa la app para generar uso.")
    st.stop()

recs = optimization_advisor.analyze(events)
agg = usage_tracker.aggregate(events)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Llamadas analizadas", agg["total_calls"])
c2.metric("Gasto total", f"${agg['total_cost_usd']:.4f}")
total_savings = sum(r.savings_estimate_usd for r in recs)
c3.metric("Ahorro potencial", f"${total_savings:.4f}")
c4.metric("Recomendaciones", len(recs))

st.divider()

if not recs:
    st.success("✅ No se han detectado patrones de gasto subóptimos.")
else:
    SEV_BADGE = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
    for r in recs:
        with st.container(border=True):
            badge = SEV_BADGE.get(r.severity, "⚪")
            cols = st.columns([3, 1])
            cols[0].markdown(f"### {badge} {r.title}")
            cols[1].metric("Ahorro", f"${r.savings_estimate_usd:.4f}")
            st.caption(f"Regla: `{r.rule_id}` · severidad: {r.severity}")
            st.markdown(f"**Evidencia:** {r.evidence}")
            st.markdown(f"**Acción:** {r.action}")

render_improve_block(
    source="page:optimizar",
    context=(
        "Página que aplica heurísticas sobre ai_usage.jsonl para detectar "
        "consumo subóptimo. Reglas actuales: T01 (modelo caro para output corto), "
        "HOT-SOURCE (>40% del gasto), FAILS, VERBOSE, CACHE."
    ),
    default_prompt=(
        "Propón 2-3 reglas adicionales que detecten patrones de gasto evitable. "
        "Indica nombre, evidencia detectable en el log y acción concreta."
    ),
    kind="update",
)
