"""Página de inicio del cockpit. Cargada por `app.py` vía st.navigation."""
from __future__ import annotations

import streamlit as st

from cockpit import connectors
from cockpit.core import paths
from cockpit.theme import inject_theme, render_logo
from cockpit.ui import render_status_sidebar

inject_theme()
render_logo()
render_status_sidebar()

st.title("MAQUINARIA PESADA · COCKPIT")
st.caption("Centraliza estado, fuentes, conectores y prompts para Codex.")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Repo root", str(paths.repo_root()))
with col2:
    st.metric("Conectores registrados", len(connectors.REGISTRY))
with col3:
    n_pdfs = len(list(paths.pdfs_dir().glob("*.pdf"))) if paths.pdfs_dir().exists() else 0
    st.metric("PDFs detectados", n_pdfs)

st.markdown(
    """
    Usa la **navegación lateral** para entrar a cada sección:

    - **🎓 Contenido** — drill-down por módulos y episodios producidos.
    - **🏭 Producción** — lanzar pipelines, consultar fuentes y logs.
    - **💸 Coste IA** — tokens, economics y optimización.
    - **📡 Difusión** — métricas en Spotify / iVoox / LinkedIn.
    - **⚙️ Sistema** — conectores, API keys, mapa y pizarra.
    - **🤖 Asistente** — conversación libre con Claude.

    Cambia el repo objetivo con la variable de entorno `REPO_ROOT`.
    Las llamadas a IA se registran en `logs/ai_usage.jsonl`. Las recargas en
    `logs/economics.json`. El mapa en `cockpit/components_map.json`.

    🔒 **Sandbox IA**: las sesiones de Claude en la app solo pueden modificar
    contenido generado y el mapa de componentes. Nunca el código de la app.
    """
)

if not paths.repo_root().exists():
    st.error(
        f"REPO_ROOT no existe: `{paths.repo_root()}`. "
        "Ajusta la variable de entorno antes de continuar."
    )
