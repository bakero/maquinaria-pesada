"""Cockpit MaquinarIA Pesada — entry point.

Run:  streamlit run cockpit/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the cockpit package is importable when run via `streamlit run cockpit/app.py`.
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402,F401  (auto-registers all)
from cockpit.core import paths  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402

st.set_page_config(
    page_title="MaquinarIA Pesada — Cockpit",
    page_icon="🎙️",
    layout="wide",
)
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
    ### Páginas
    - **📊 Estado** — inventario por módulo (M0–M14).
    - **🔌 Conectores** — servicios, pipelines y fuentes registrados.
    - **📝 Generar Prompt** — formularios → comandos CLI listos para Codex.
    - **📚 Fuentes** — explorador de PDFs, guiones, audio, vídeo y logs.
    - **📜 Logs** — visor de logs de producción con auto-refresh.

    Cambia el repo objetivo con la variable de entorno `REPO_ROOT`.
    """
)

if not paths.repo_root().exists():
    st.error(
        f"REPO_ROOT no existe: `{paths.repo_root()}`. "
        "Ajusta la variable de entorno antes de continuar."
    )
