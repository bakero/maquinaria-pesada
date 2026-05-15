"""Cockpit home page — loaded by app.py via st.navigation."""
from __future__ import annotations

import streamlit as st

from cockpit import connectors
from cockpit.core import paths
from cockpit.theme import inject_theme, render_logo
from cockpit.ui import render_status_sidebar
from cockpit.ui_components import Stat, page_header, section, stat_grid

inject_theme()
render_logo()
render_status_sidebar()

page_header(
    "MaquinarIA Pesada — Cockpit",
    eyebrow="Inicio",
    subtitle=(
        "Centro de control del sistema de podcasts y vídeos con IA. "
        "Lanza pipelines, audita contenido, controla gasto y conversa "
        "con Claude para mejorar cada episodio."
    ),
)

n_pdfs = len(list(paths.pdfs_dir().glob("*.pdf"))) if paths.pdfs_dir().exists() else 0

stat_grid(
    [
        Stat("Conectores", str(len(connectors.REGISTRY)), hint="Pipelines + servicios"),
        Stat("PDFs detectados", str(n_pdfs), hint=str(paths.pdfs_dir())),
        Stat("Repo raíz", paths.repo_root().name, hint=str(paths.repo_root())),
    ]
)

section(
    "Por dónde empezar",
    subtitle="Cada sección de la barra lateral agrupa páginas relacionadas.",
)

cols = st.columns(3)

with cols[0]:
    with st.container(border=True):
        st.markdown("#### 🎓 Contenido")
        st.caption(
            "Drill-down por módulos y episodios. "
            "Inspecciona guiones, audios y verificaciones."
        )
        st.markdown(
            "- **Master** · vista global del curso  \n"
            "- **Módulo** · detalle de un Mₙ  \n"
            "- **Episodio** · control completo  \n"
            "- **Previsualizar** · audio + guion"
        )

with cols[1]:
    with st.container(border=True):
        st.markdown("#### 🏭 Producción")
        st.caption(
            "Operación día a día: lanzar pipelines, "
            "consultar fuentes PDF y revisar logs."
        )
        st.markdown(
            "- **Generar prompt** · plantillas por pipeline  \n"
            "- **Fuentes** · auxiliares, resúmenes, temas  \n"
            "- **Logs** · trazas de generación"
        )

with cols[2]:
    with st.container(border=True):
        st.markdown("#### 💸 Coste IA")
        st.caption(
            "Token tracking, gasto histórico y consejos "
            "para reducir factura sin sacrificar calidad."
        )
        st.markdown(
            "- **Tokens** · uso por modelo  \n"
            "- **Economics** · gasto por episodio  \n"
            "- **Optimizar** · advisor de ahorro"
        )

cols2 = st.columns(3)

with cols2[0]:
    with st.container(border=True):
        st.markdown("#### 📡 Difusión")
        st.caption("Métricas en Spotify, iVoox, LinkedIn.")
        st.markdown("- **Rendimiento** · KPIs por episodio")

with cols2[1]:
    with st.container(border=True):
        st.markdown("#### ⚙️ Sistema")
        st.caption("Conectores, claves, arquitectura y pizarra.")
        st.markdown(
            "- **Conectores** · pipelines y servicios  \n"
            "- **API Keys** · estado de proveedores  \n"
            "- **Mapa** · componentes del sistema  \n"
            "- **Pizarra** · notas libres"
        )

with cols2[2]:
    with st.container(border=True):
        st.markdown("#### 🤖 Asistente")
        st.caption("Conversación libre con Claude.")
        st.markdown(
            "Pregunta sobre el sistema, pide diagnósticos o "
            "redacción asistida. Sigue la política sandbox."
        )

st.divider()

st.markdown(
    """
**🔒 Sandbox IA** — las sesiones de Claude lanzadas desde la app solo pueden
escribir en contenido generado y mapa de componentes. Nunca tocan el código
del cockpit ni los pipelines top-level. Cambia el repo objetivo con la
variable de entorno `REPO_ROOT`.
"""
)

if not paths.repo_root().exists():
    st.error(
        f"REPO_ROOT no existe: `{paths.repo_root()}`. "
        "Ajusta la variable de entorno antes de continuar."
    )
