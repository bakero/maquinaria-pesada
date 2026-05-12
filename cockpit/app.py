"""Cockpit MaquinarIA Pesada — entry point.

Run: ``streamlit run cockpit/app.py``
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
    - **🎓 Master** — estado por módulo (Listo / En curso % / Sin empezar).
    - **🎬 Módulo** — detalle de un módulo: episodios M + Tn con su estado.
    - **📼 Episodio** — vista única por episodio: guion, PDF, escaleta, audio,
      logs, verificaciones y botón **🛠️ Arreglar con Claude** si hay errores.
    - **🎨 Pizarra** — generador visual: esferas = componentes, cuadrados =
      contenidos, flechas entre ellos. Click en componente → ver código.
    - **📊 Estado** — inventario por módulo (M0–M14). *Mejorar-con-IA.*
    - **🔌 Conectores** — servicios, pipelines, fuentes. *Mejorar por conector.*
    - **📝 Generar Prompt** — formularios + **ejecutor en vivo**.
    - **📚 Fuentes** — explorador de PDFs, guiones, audio, vídeo, logs.
    - **📜 Logs** — visor con auto-refresh **+ diagnóstico IA**.
    - **🔑 API Keys** — verifica Anthropic / OpenAI / ElevenLabs.
    - **💰 Tokens** — consumo agregado por modelo / kind / origen.
    - **🎧 Previsualizar** — audio y vídeo desde la UI.
    - **💬 Asistente** — conversación libre con Claude.
    - **🧠 Optimizar** — recomendaciones automáticas de ahorro de tokens.
    - **💳 Economics** — recargas y saldos por proveedor IA.
    - **🗺️ Mapa** — grafo de componentes editable + chat IA del mapa.

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
