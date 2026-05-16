"""Reusable Streamlit block for executing a pipeline connector.

Pages embed this block (typically inside ``st.expander`` or ``st.dialog``)
to reuse the form + preview + streaming-execution UI without duplicating
the logic. Used by the dedicated "Lanzar pipeline" page and by contextual
actions on Episodio / Módulo / Master.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from cockpit.connectors.base import Field_, PipelineConnector
from cockpit.core.runner import RunResult


def render_pipeline(
    pipe: PipelineConnector,
    *,
    key: str,
    initial: dict[str, Any] | None = None,
    show_codex: bool = True,
    autorun: bool = False,
    confirm_required: bool = True,
) -> None:
    """Render the full form + preview + execute block for ``pipe``.

    Parameters
    ----------
    key
        Unique prefix used to namespace widget keys. Pass a stable string
        per page-call so the widget state survives reruns.
    initial
        Pre-filled values for fields, keyed by flag (e.g. {"--guion": "..."}).
    show_codex
        If True, include a "command for Codex" expander.
    autorun
        If True, the streamlit form auto-submits with initial values — used
        when the caller already has all required fields filled (e.g. an
        Episode page button that pre-fills the guion path).
    confirm_required
        If True, require checking a confirmation checkbox before running.
    """
    initial = initial or {}

    # Step 1: form (or no-fields shortcut)
    if pipe.fields:
        values, submitted = _render_form(pipe, key=key, initial=initial)
        if not submitted and not autorun:
            return
        if autorun and not values:
            values = {f.flag: initial.get(f.flag, f.default) for f in pipe.fields}
    else:
        st.caption("Este pipeline no acepta flags — se ejecuta tal cual.")
        values = {}

    missing = [
        f.flag for f in pipe.fields
        if f.required and not values.get(f.flag)
    ]
    if missing:
        st.error(f"Faltan campos obligatorios: {', '.join(missing)}")
        return

    # Step 2: preview + run
    st.divider()
    st.markdown("**Vista previa del comando**")
    st.code(pipe.preview(values), language="bash")

    if show_codex:
        with st.expander("Generar comando para Codex (copy-paste)"):
            st.code(pipe.build_command(values), language="bash")

    confirm_key = f"{key}_confirm"
    run_key = f"{key}_run"

    if confirm_required:
        confirm = st.checkbox(
            "Sí, ejecutar este comando ahora",
            key=confirm_key,
            help="Marca para habilitar el botón Ejecutar.",
        )
    else:
        confirm = True

    if st.button(
        "▶ Ejecutar pipeline",
        type="primary",
        disabled=not confirm,
        key=run_key,
    ):
        _stream_run(pipe, values)


def _render_form(
    pipe: PipelineConnector, *, key: str, initial: dict[str, Any]
) -> tuple[dict[str, Any], bool]:
    values: dict[str, Any] = {}
    with st.form(key=f"{key}_form", clear_on_submit=False):
        for f in pipe.fields:
            values[f.flag] = _render_field(
                f,
                key=f"{key}_{f.flag}",
                override=initial.get(f.flag),
            )
        submitted = st.form_submit_button("Preparar comando", type="primary")
    return values, submitted


def _render_field(f: Field_, *, key: str, override: Any | None) -> Any:
    label = f"{f.label} ({f.flag})" + (" *" if f.required else "")
    default = override if override is not None else f.default

    if f.kind == "bool":
        return st.checkbox(label, value=bool(default), key=key, help=f.help or None)
    if f.kind == "int":
        try:
            n = int(default) if default not in (None, "") else 0
        except (TypeError, ValueError):
            n = 0
        return st.number_input(label, value=n, step=1, key=key, help=f.help or None)
    if f.kind == "select":
        opts = list(f.options) or [""]
        idx = opts.index(default) if default in opts else 0
        return st.selectbox(label, opts, index=idx, key=key, help=f.help or None)
    return st.text_input(
        label,
        value=str(default) if default is not None else "",
        placeholder=f.placeholder or None,
        key=key,
        help=f.help or None,
    )


def _stream_run(pipe: PipelineConnector, values: dict[str, Any]) -> None:
    output_area = st.empty()
    log_lines: list[str] = []
    with st.status("Ejecutando…", expanded=True) as status:
        for item in pipe.stream(values):
            if isinstance(item, RunResult):
                if item.returncode == 0:
                    status.update(
                        label=f"✅ Completado en {item.duration_s}s",
                        state="complete",
                    )
                    st.toast(f"{pipe.label} · completado", icon="✅")
                else:
                    status.update(
                        label=f"❌ Falló (exit {item.returncode}) en {item.duration_s}s",
                        state="error",
                    )
                    st.toast(f"{pipe.label} · falló", icon="❌")
            else:
                log_lines.append(item)
                output_area.code("\n".join(log_lines[-200:]), language="text")
