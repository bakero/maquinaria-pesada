"""Página Economics: recargas, gastos manuales y suscripciones por proveedor IA."""
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

st.title("ECONOMICS · RECARGAS, GASTOS Y SUSCRIPCIONES")
st.caption(
    "Saldo = topups − (gastos manuales + ai_usage.jsonl). Las suscripciones "
    "(Claude Max, ElevenLabs Starter…) se contabilizan aparte como tarifa plana."
)

# ----- Métricas globales -----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Topups totales", f"${economics.total_topped_up():.2f}")
c2.metric("Gasto total", f"${economics.total_spent():.2f}")
c3.metric("Saldo global", f"${economics.total_balance():.2f}")
c4.metric("Suscripciones / mes", f"${economics.total_subscription_monthly():.2f}")

st.divider()

state = economics.load()
if not state.topups and not state.spends and not state.subscriptions:
    st.info(
        "Sin movimientos registrados. Usa las pestañas de abajo para añadir "
        "recargas, gastos manuales o suscripciones."
    )

# ----- Saldo por proveedor -----
summary = economics.summary()
st.subheader("Saldo por proveedor")
if not summary:
    st.caption("Sin movimientos todavía.")
else:
    cols = st.columns(len(summary))
    for col, (prov, data) in zip(cols, sorted(summary.items()), strict=False):
        with col:
            balance = data["balance"]
            badge = "🟢" if balance > 0 else "🔴" if balance < 0 else "⚪"
            st.markdown(f"### {badge} {prov}")
            st.metric("Saldo USD", f"${balance:.2f}")
            st.caption(
                f"Topups: ${data['topped_up']:.2f}  ·  "
                f"Gasto: ${data['spent']:.2f}"
            )
            if data["spent_manual"] and data["spent_tracked"]:
                st.caption(
                    f"  manual: ${data['spent_manual']:.2f}  ·  "
                    f"tracked: ${data['spent_tracked']:.2f}"
                )
            st.caption(f"Llamadas IA registradas: {int(data['calls'])}")
            if data["subscription_monthly"]:
                st.caption(
                    f"🔁 Suscripción: ${data['subscription_monthly']:.2f}/mes "
                    f"({int(data['subscriptions'])})"
                )

st.divider()

# ----- Tabs de gestión -----
tab_top, tab_spend, tab_sub = st.tabs(
    ["💳 Recargas (Topups)", "💸 Gastos manuales", "🔁 Suscripciones"]
)

with tab_top:
    st.markdown("Registra una recarga pay-as-you-go (cargo en el panel del proveedor).")
    with st.form("topup_form"):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 4])
        provider = c1.selectbox(
            "Proveedor", ["anthropic", "openai", "elevenlabs", "kling", "otro"],
            key="topup_provider",
        )
        amount = c2.number_input("Importe USD", min_value=0.01, value=10.0, step=1.0,
                                  key="topup_amount")
        date_str = c3.text_input("Fecha (YYYY-MM-DD)", value="",
                                 placeholder="opcional", key="topup_date")
        note = c4.text_input("Nota", placeholder="Recarga manual…", key="topup_note")
        if st.form_submit_button("💳 Registrar recarga"):
            economics.add_topup(provider, amount, note, timestamp=date_str or None)
            st.success(f"Registrada recarga de ${amount:.2f} en {provider}.")
            st.rerun()

    state = economics.load()
    if state.topups:
        st.markdown("**Histórico:**")
        for i, t in enumerate(reversed(state.topups)):
            idx = len(state.topups) - 1 - i
            cols = st.columns([2, 2, 1, 5, 1])
            cols[0].text(t.timestamp)
            cols[1].text(t.provider)
            cols[2].text(f"${t.amount_usd:.2f}")
            cols[3].text(t.note or "—")
            if cols[4].button("🗑", key=f"_del_top_{idx}"):
                economics.remove_topup(idx)
                st.rerun()

with tab_spend:
    st.markdown(
        "Gasto manual: importes que NO vienen de `ai_usage.jsonl` (consumos "
        "históricos antes del tracker, facturas externas, etc.)."
    )
    with st.form("spend_form"):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 4])
        provider = c1.selectbox(
            "Proveedor", ["anthropic", "openai", "elevenlabs", "kling", "otro"],
            key="spend_provider",
        )
        amount = c2.number_input("Importe USD", min_value=0.01, value=10.0, step=1.0,
                                  key="spend_amount")
        date_str = c3.text_input("Fecha (YYYY-MM-DD)", value="",
                                 placeholder="opcional", key="spend_date")
        note = c4.text_input("Nota", placeholder="Generación M0…", key="spend_note")
        if st.form_submit_button("💸 Registrar gasto"):
            economics.add_spend(provider, amount, note, timestamp=date_str or None)
            st.success(f"Registrado gasto de ${amount:.2f} en {provider}.")
            st.rerun()

    state = economics.load()
    if state.spends:
        st.markdown("**Histórico:**")
        for i, s in enumerate(reversed(state.spends)):
            idx = len(state.spends) - 1 - i
            cols = st.columns([2, 2, 1, 5, 1])
            cols[0].text(s.timestamp)
            cols[1].text(s.provider)
            cols[2].text(f"${s.amount_usd:.2f}")
            cols[3].text(s.note or "—")
            if cols[4].button("🗑", key=f"_del_sp_{idx}"):
                economics.remove_spend(idx)
                st.rerun()

with tab_sub:
    st.markdown("Suscripciones (tarifa plana mensual). No descuentan saldo de topups.")
    with st.form("sub_form"):
        c1, c2, c3 = st.columns([3, 2, 2])
        name = c1.text_input("Nombre del plan", placeholder="Claude Max",
                              key="sub_name")
        provider = c2.selectbox(
            "Proveedor", ["anthropic", "openai", "elevenlabs", "kling", "otro"],
            key="sub_provider",
        )
        monthly = c3.number_input("USD / mes", min_value=0.01, value=10.0, step=1.0,
                                   key="sub_monthly")
        c4, c5 = st.columns([2, 4])
        started = c4.text_input("Desde (YYYY-MM)", value="",
                                placeholder="2026-05", key="sub_started")
        note = c5.text_input("Nota", placeholder="Plan Max 5×, etc.",
                              key="sub_note")
        if st.form_submit_button("🔁 Registrar suscripción"):
            economics.add_subscription(name or provider, provider, monthly,
                                       started_on=started, note=note)
            st.success(f"Registrada suscripción «{name}» (${monthly:.2f}/mes).")
            st.rerun()

    state = economics.load()
    if state.subscriptions:
        st.markdown("**Suscripciones activas:**")
        for i, sub in enumerate(reversed(state.subscriptions)):
            idx = len(state.subscriptions) - 1 - i
            cols = st.columns([3, 2, 2, 4, 1])
            cols[0].text(sub.name)
            cols[1].text(sub.provider)
            cols[2].text(f"${sub.monthly_usd:.2f}/mes")
            cols[3].text(sub.note or sub.started_on or "—")
            if cols[4].button("🗑", key=f"_del_sub_{idx}"):
                economics.remove_subscription(idx)
                st.rerun()

st.divider()

render_improve_block(
    source="page:economics",
    context=(
        "Página de economics: topups + gastos manuales + suscripciones por "
        "proveedor IA. Calcula saldo restante por proveedor y global, contabiliza "
        "ai_usage.jsonl automáticamente. No tiene proyección de agotamiento "
        "ni alertas de umbral."
    ),
    default_prompt=(
        "Propón mejoras: alertas saldo < umbral, proyección días restantes según "
        "consumo medio diario, exportar a CSV/Excel, gráfica de evolución mensual."
    ),
    kind="update",
)
