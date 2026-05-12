"""Página Economics: recargas y saldos por proveedor IA."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import economics  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Economics", page_icon="💳", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

st.title("ECONOMICS — RECARGAS Y SALDOS")
st.caption(
    "El gasto se calcula desde `ai_usage.jsonl`. Las recargas se introducen "
    "manualmente (los proveedores no exponen saldo en API pública o requieren "
    "scraping de la consola)."
)

summary = economics.summary()

st.subheader("Saldo por proveedor")
if not summary:
    st.info("Sin datos. Añade una recarga abajo o lanza alguna llamada IA.")
else:
    cols = st.columns(len(summary))
    for col, (prov, data) in zip(cols, sorted(summary.items()), strict=False):
        with col:
            balance = data["balance"]
            badge = "🟢" if balance > 0 else "🔴" if balance < 0 else "⚪"
            st.markdown(f"### {badge} {prov}")
            st.metric("Saldo USD", f"${balance:.4f}")
            st.caption(
                f"Recargado: ${data['topped_up']:.4f} · Gastado: ${data['spent']:.4f}"
            )
            st.caption(f"Llamadas: {int(data['calls'])}")

st.metric("**Saldo global**", f"${economics.total_balance():.4f}")

st.divider()
st.subheader("Añadir recarga")
with st.form("topup_form"):
    c1, c2, c3 = st.columns(3)
    provider = c1.selectbox("Proveedor", ["anthropic", "openai", "elevenlabs", "kling", "otro"])
    amount = c2.number_input("Importe USD", min_value=0.01, value=10.0, step=1.0)
    note = c3.text_input("Nota (opcional)", placeholder="Recarga mensual…")
    if st.form_submit_button("💳 Registrar recarga"):
        economics.add_topup(provider, amount, note)
        st.success(f"Registrada recarga de ${amount:.2f} en {provider}.")
        st.rerun()

st.divider()
st.subheader("Histórico de recargas")
state = economics.load()
if not state.topups:
    st.caption("Sin recargas todavía.")
else:
    for i, t in enumerate(reversed(state.topups)):
        idx = len(state.topups) - 1 - i
        cols = st.columns([2, 2, 1, 4, 1])
        cols[0].text(t.timestamp)
        cols[1].text(t.provider)
        cols[2].text(f"${t.amount_usd:.2f}")
        cols[3].text(t.note or "—")
        if cols[4].button("🗑", key=f"_del_topup_{idx}"):
            economics.remove_topup(idx)
            st.rerun()

render_improve_block(
    source="page:economics",
    context=(
        "Página que gestiona recargas manuales por proveedor IA y calcula saldo "
        "restante usando ai_usage.jsonl. No hay alertas automáticas ni "
        "proyecciones de agotamiento."
    ),
    default_prompt=(
        "Propón mejoras: alertas cuando saldo < X, proyección de días restantes "
        "según consumo medio, exportación a Excel para contabilidad."
    ),
    kind="update",
)
