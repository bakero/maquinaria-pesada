"""Página Asistente: conversación libre con Claude para mejorar el sistema.

A diferencia del componente Mejorar-con-IA (one-shot), aquí se mantiene
historial en `st.session_state`. Cada turno se registra en ai_usage.jsonl.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import ai_client, usage_tracker  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402

st.set_page_config(page_title="Asistente", page_icon="💬", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

st.title("ASISTENTE — CONVERSACIÓN CON CLAUDE")
st.caption(
    "Pide cambios al sistema, debate diseño, pregunta sobre prompts. Cada turno "
    "registra tokens y coste en la página *Tokens*."
)

SYSTEM_PROMPT = (
    "Eres el copiloto técnico del sistema MaquinarIA Pesada: pipeline Python que "
    "genera podcasts y vídeos con Anthropic, OpenAI, Whisper, ElevenLabs y Kling. "
    "Conoces la cockpit Streamlit (cockpit/), los pipelines (generar_guion.py, "
    "generar_episodio_v2.py, validar_episodio.py, etc.) y el plan de migración. "
    "Responde en español de España, conciso, accionable. Cuando sugieras código, "
    "indica fichero y zona afectada."
)

if "_chat_msgs" not in st.session_state:
    st.session_state["_chat_msgs"] = []

col_settings, _ = st.columns([1, 3])
with col_settings:
    model = st.selectbox(
        "Modelo",
        ["claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-7"],
        index=0,
        key="_chat_model",
    )
    if st.button("🗑️ Limpiar conversación"):
        st.session_state["_chat_msgs"] = []
        st.rerun()

for m in st.session_state["_chat_msgs"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Escribe tu mensaje…")
if prompt:
    st.session_state["_chat_msgs"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    user_concat = "\n\n".join(
        f"[{m['role']}] {m['content']}" for m in st.session_state["_chat_msgs"]
    )
    try:
        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                text, usage = ai_client.improve_with_claude(
                    system=SYSTEM_PROMPT,
                    user=user_concat,
                    source="page:asistente",
                    kind="improvement",
                    model=model,
                    max_tokens=2048,
                )
            st.markdown(text)
            st.caption(
                f"in {usage.input_tokens} · out {usage.output_tokens} · "
                f"${usage.cost_usd:.4f} · {usage.latency_ms} ms"
            )
        st.session_state["_chat_msgs"].append({"role": "assistant", "content": text})
    except ai_client.AIClientError as e:
        st.error(f"Error: {e}")

# Estadística rápida de la conversación.
if st.session_state["_chat_msgs"]:
    agg = usage_tracker.aggregate(
        ev for ev in usage_tracker.iter_events() if ev.get("source") == "page:asistente"
    )
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Turnos asistente", agg["total_calls"])
    c2.metric("Tokens totales", agg["total_input_tokens"] + agg["total_output_tokens"])
    c3.metric("Coste acumulado", f"${agg['total_cost_usd']:.4f}")
