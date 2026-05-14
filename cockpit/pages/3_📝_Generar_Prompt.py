from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402
from cockpit.connectors.base import PipelineConnector  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Generar prompt", page_icon="📝", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()
st.title("GENERAR PROMPT PARA CODEX")
st.caption("Rellena el formulario y copia el comando resultante a Codex. La cockpit no ejecuta nada.")

pipelines = [c for c in connectors.by_category("pipeline") if isinstance(c, PipelineConnector)]
if not pipelines:
    st.warning("No hay pipelines registrados.")
    st.stop()

labels = {p.id: f"{p.icon} {p.label}" for p in pipelines}
sel_id = st.selectbox(
    "Pipeline",
    options=[p.id for p in pipelines],
    format_func=lambda i: labels[i],
)
pipe: PipelineConnector = connectors.get(sel_id)  # type: ignore[assignment]

st.markdown(f"**Script:** `{pipe.script}`")
st.caption(pipe.description)

values: dict[str, object] = {}
with st.form(key=f"form_{pipe.id}"):
    for f in pipe.fields:
        key = f"{pipe.id}_{f.flag}"
        label = f"{f.label} ({f.flag})" + (" *" if f.required else "")
        if f.kind == "bool":
            values[f.flag] = st.checkbox(label, value=bool(f.default), help=f.help)
        elif f.kind == "int":
            default = int(f.default) if f.default not in (None, "") else 0
            values[f.flag] = st.number_input(label, value=default, step=1, help=f.help)
        elif f.kind == "select":
            opts = f.options or [""]
            default_idx = opts.index(f.default) if f.default in opts else 0
            values[f.flag] = st.selectbox(label, opts, index=default_idx, help=f.help)
        else:  # str / path
            values[f.flag] = st.text_input(
                label,
                value=str(f.default) if f.default is not None else "",
                placeholder=f.placeholder,
                help=f.help,
            )
    submitted = st.form_submit_button("Generar comando")

if submitted:
    missing = [f.flag for f in pipe.fields if f.required and not values.get(f.flag)]
    if missing:
        st.error(f"Faltan campos obligatorios: {', '.join(missing)}")
    else:
        st.session_state[f"_values_{pipe.id}"] = values
        cmd = pipe.build_command(values)
        st.success("Comando listo. Copia y pega en Codex:")
        st.code(cmd, language="bash")

values_ready = st.session_state.get(f"_values_{pipe.id}")
if values_ready:
    st.divider()
    st.subheader("Ejecutar localmente")
    st.caption("Lanza el pipeline desde la cockpit. Los logs aparecen en vivo.")
    st.code(pipe.preview(values_ready), language="bash")

    confirm = st.checkbox(
        "Sí, ejecutar este comando ahora",
        key=f"_confirm_{pipe.id}",
        help="Marca esta casilla para habilitar el botón. Evita ejecuciones accidentales.",
    )
    if st.button("▶ Ejecutar", type="primary", disabled=not confirm, key=f"_run_{pipe.id}"):
        from cockpit.core.runner import RunResult

        output_area = st.empty()
        log_lines: list[str] = []
        with st.status("Ejecutando…", expanded=True) as status:
            for item in pipe.stream(values_ready):
                if isinstance(item, RunResult):
                    if item.returncode == 0:
                        status.update(
                            label=f"✅ Completado en {item.duration_s}s",
                            state="complete",
                        )
                    else:
                        status.update(
                            label=f"❌ Falló (exit {item.returncode}) en {item.duration_s}s",
                            state="error",
                        )
                else:
                    log_lines.append(item)
                    output_area.code("\n".join(log_lines[-200:]), language="text")

render_improve_block(
    source=f"pipeline:{pipe.id}",
    context=(
        f"Pipeline «{pipe.label}» (script={pipe.script}, id={pipe.id}). "
        f"Descripción: {pipe.description}. Campos del formulario: "
        + ", ".join(f"{f.flag}({f.kind})" for f in pipe.fields)
    ),
    title="✨ Mejorar este pipeline",
    default_prompt=(
        "Sugiere mejoras al pipeline: validaciones que faltan, flags útiles, "
        "manejo de errores, retry, tests mínimos."
    ),
    kind="update",
)
