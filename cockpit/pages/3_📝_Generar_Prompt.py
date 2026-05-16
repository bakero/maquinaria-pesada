"""Lanzador de pipelines — formulario + ejecución para cualquier pipeline registrado."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402
from cockpit.connectors.base import PipelineConnector  # noqa: E402
from cockpit.pipeline_runner import render_pipeline  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import (  # noqa: E402
    info_callout,
    page_header,
    section,
    status_pill,
)
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Lanzar pipeline", page_icon="📝", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

page_header(
    "Lanzar pipeline",
    eyebrow="Producción",
    subtitle=(
        "Selecciona un pipeline, rellena el formulario y ejecútalo "
        "desde el cockpit con streaming de logs. También puedes "
        "generar el comando equivalente para pegarlo en Codex."
    ),
    help_page_id="lanzador",
)

pipelines = [
    c for c in connectors.by_category("pipeline") if isinstance(c, PipelineConnector)
]
if not pipelines:
    st.warning("No hay pipelines registrados.")
    st.stop()

# Agrupación temática para reducir carga cognitiva.
GROUPS: dict[str, list[str]] = {
    "🎙️ Generación de contenido": [
        "generar_guion", "generar_guion_t", "generar_episodio",
    ],
    "✅ Validación": [
        "validar_episodio", "validar_episodio_v6",
    ],
    "⚙️ Operación masiva": [
        "produce_pending", "estado_proyecto",
    ],
    "🧰 Utilidades": [
        "normalizar_guiones", "dual_debate",
    ],
}


def _pipe_label(p: PipelineConnector) -> str:
    return f"{p.icon} {p.label}"


# Mapa id → connector para acceso rápido
by_id: dict[str, PipelineConnector] = {p.id: p for p in pipelines}

info_callout(
    "Los pipelines marcados como ⚠️ legacy se conservan por compatibilidad "
    "pero **no** se usan para generación nueva. Para guiones nuevos usa "
    "**Generar guion M** o **Generar guion T**.",
    kind="tip",
)

# Restablecer selección si venimos de otro flujo
default_id = st.session_state.get("_lanzador_preselect")

tabs = st.tabs(list(GROUPS.keys()))
for tab, (group_name, ids) in zip(tabs, GROUPS.items(), strict=True):
    with tab:
        in_group = [by_id[i] for i in ids if i in by_id]
        if not in_group:
            st.caption("Sin pipelines en este grupo.")
            continue

        # Selector dentro de la pestaña
        idx = 0
        if default_id and default_id in [p.id for p in in_group]:
            idx = [p.id for p in in_group].index(default_id)
            st.session_state["_lanzador_preselect"] = None

        sel_id = st.selectbox(
            "Pipeline",
            options=[p.id for p in in_group],
            format_func=lambda i: _pipe_label(by_id[i]),
            index=idx,
            key=f"_lanzador_select_{group_name}",
            label_visibility="collapsed",
        )
        pipe = by_id[sel_id]

        # Metadatos del pipeline
        meta = st.columns([3, 2])
        with meta[0]:
            st.markdown(f"**Script** · `{pipe.script}`")
            st.caption(pipe.description)
        with meta[1]:
            status = pipe.status()
            kind = "ok" if status.ok else "fail"
            label = "Script presente" if status.ok else status.detail or "no disponible"
            st.markdown(status_pill(label, kind=kind), unsafe_allow_html=True)
            if pipe.fields:
                st.caption(f"{len(pipe.fields)} flag{'s' if len(pipe.fields) != 1 else ''} configurables")
            else:
                st.caption("Sin flags configurables")

        section("Configuración", subtitle="Rellena los campos y pulsa Preparar comando.")

        render_pipeline(
            pipe,
            key=f"lanzador_{pipe.id}",
            show_codex=True,
        )

        # Bloque de mejora con Claude (contextual al pipeline)
        st.divider()
        render_improve_block(
            source=f"pipeline:{pipe.id}",
            context=(
                f"Pipeline «{pipe.label}» (script={pipe.script}, id={pipe.id}). "
                f"Descripción: {pipe.description}. Campos del formulario: "
                + ", ".join(f"{f.flag}({f.kind})" for f in pipe.fields)
            ),
            title="✨ Mejorar este pipeline",
            default_prompt=(
                "Sugiere mejoras al pipeline: validaciones que faltan, flags "
                "útiles, manejo de errores, retry, tests mínimos."
            ),
            kind="update",
        )
