"""Cockpit home page — loaded by app.py via st.navigation."""
from __future__ import annotations

import streamlit as st

from cockpit import connectors
from cockpit.core import episodes, paths
from cockpit.theme import inject_theme, render_logo
from cockpit.ui import render_status_sidebar
from cockpit.ui_components import (
    Stat,
    info_callout,
    page_header,
    section,
    stat_grid,
)

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
    help_page_id="home",
)

# ---- Métricas globales ----
all_eps = episodes.scan_all()
n_complete = sum(1 for e in all_eps if e.complete)
n_total_eps = len(all_eps)
n_pdfs = len(list(paths.pdfs_dir().glob("*.pdf"))) if paths.pdfs_dir().exists() else 0

# Conteo por estado de módulo
n_mod_listo = n_mod_curso = n_mod_vacio = 0
for m in paths.MODULES:
    eps_m = [e for e in all_eps if e.module == m]
    s, _ = episodes.module_status(eps_m)
    if s == "listo":
        n_mod_listo += 1
    elif s == "en_curso":
        n_mod_curso += 1
    else:
        n_mod_vacio += 1

stat_grid([
    Stat("Módulos listos", f"{n_mod_listo}/{len(paths.MODULES)}", color="ok"),
    Stat("En curso", str(n_mod_curso), color="warn"),
    Stat("Episodios completos", f"{n_complete}/{n_total_eps}"),
    Stat("PDFs fuente", str(n_pdfs), hint=str(paths.pdfs_dir())),
    Stat("Conectores", str(len(connectors.REGISTRY)), hint="Pipelines + servicios"),
])

# ---- Quick actions ----
section("Acciones rápidas", subtitle="Atajos a los flujos más comunes.")

qa = st.columns(4)
with qa[0]:
    if st.button("📊  Ver Master", use_container_width=True):
        st.switch_page("pages/0_🎓_Master.py")
with qa[1]:
    if st.button("📝  Lanzar pipeline", use_container_width=True):
        st.switch_page("pages/3_📝_Generar_Prompt.py")
with qa[2]:
    if st.button("📜  Ver logs", use_container_width=True):
        st.switch_page("pages/5_📜_Logs.py")
with qa[3]:
    if st.button("💸  Ver coste IA", use_container_width=True):
        st.switch_page("pages/11_💳_Economics.py")

# ---- Map de secciones ----
section("Por dónde empezar", subtitle="La barra lateral agrupa las páginas en seis bloques.")

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
            "Operación día a día: lanzar pipelines, consultar fuentes y revisar logs."
        )
        st.markdown(
            "- **Lanzar pipeline** · 9 pipelines registrados  \n"
            "- **Fuentes** · auxiliares, resúmenes, temas  \n"
            "- **Logs** · trazas de generación"
        )

with cols[2]:
    with st.container(border=True):
        st.markdown("#### 💸 Coste IA")
        st.caption("Token tracking, gasto histórico y optimización.")
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

info_callout(
    "**Sandbox IA** — las sesiones de Claude lanzadas desde la app solo pueden "
    "escribir en contenido generado y mapa de componentes. Nunca tocan el código "
    "del cockpit ni los pipelines top-level. Cambia el repo objetivo con la "
    "variable de entorno `REPO_ROOT`.",
    kind="info",
)

if not paths.repo_root().exists():
    st.error(
        f"REPO_ROOT no existe: `{paths.repo_root()}`. "
        "Ajusta la variable de entorno antes de continuar."
    )
