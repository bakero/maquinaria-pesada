"""Página Episodio — vista única por episodio.

Muestra guion, PDF, escaleta, audio, logs y verificaciones por contenido.
Tiene action bar contextual con acciones según el estado del episodio:
generar guion / generar audio / validar / arreglar errores con Claude.

Query param: ?ep=<episode_id>  (e.g. M3, M3_T2)
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit import connectors  # noqa: E402
from cockpit.connectors.base import PipelineConnector  # noqa: E402
from cockpit.core import episodes, paths, verifications  # noqa: E402
from cockpit.pipeline_runner import render_pipeline  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import (  # noqa: E402
    Action,
    ActionGroup,
    Stat,
    action_bar,
    info_callout,
    page_header,
    stat_grid,
    status_pill,
)
from cockpit.ui_improve import render_improve_block  # noqa: E402

st.set_page_config(page_title="Episodio", page_icon="📼", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()

# --- Selección de episodio ---
all_eps = episodes.scan_all()
qp_ep = st.query_params.get("ep")
ids = [e.id for e in all_eps]
default_idx = ids.index(qp_ep) if qp_ep in ids else 0

head = st.columns([5, 2])
with head[0]:
    page_header(
        "Control de episodio",
        eyebrow="Episodio",
        subtitle="Guion, PDF, escaleta, audio, logs y verificaciones — todo en una vista.",
        help_page_id="episodio",
        breadcrumb=[
            ("Master", "pages/0_🎓_Master.py"),
            ("Módulo", "pages/13_🎬_Modulo.py"),
            ("Episodio", None),
        ],
    )
with head[1]:
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    selected = st.selectbox(
        "Episodio",
        ids,
        index=default_idx if ids else 0,
        format_func=lambda eid: next((e.label for e in all_eps if e.id == eid), eid),
        key="ep_select",
        label_visibility="collapsed",
    )
    if selected != qp_ep:
        st.query_params["ep"] = selected

ep = next((e for e in all_eps if e.id == selected), None)
if ep is None:
    st.error("No se ha encontrado el episodio. Vuelve al Master.")
    st.stop()

checks = verifications.run_all(ep)
has_errors = any(c.status == "fail" for grp in checks.values() for c in grp)

stat_grid([
    Stat("Episodio", ep.id, hint=ep.label),
    Stat("Tipo", "Módulo" if ep.kind == "M" else f"Tema T{ep.number}"),
    Stat("Producidos", f"{len(ep.produced)}/{len(episodes.CONTENT_TYPES)}", color="primary"),
    Stat("Progreso", f"{ep.progress*100:.0f}%"),
    Stat("Errores", "Sí" if has_errors else "No", color="alert" if has_errors else "ok"),
])

# ---------------------------------------------------------------
# Action bar contextual — acciones disponibles según estado
# ---------------------------------------------------------------

# Triggers que se setean al pulsar un botón del action bar.
def _open_pipeline(pipe_id: str, initial: dict | None = None) -> None:
    st.session_state["_open_pipeline_modal"] = True
    st.session_state["_pipeline_modal_pipe"] = pipe_id
    st.session_state["_pipeline_modal_init"] = initial or {}


def _open_fix() -> None:
    st.session_state["_open_fix_modal"] = True


# Estado de archivos para decidir qué acciones mostrar
has_guion = bool(ep.guion and ep.guion.exists())
has_audio = bool(ep.audio and ep.audio.exists())
has_pdf = bool(ep.pdf and ep.pdf.exists())

actions: list[Action] = []

# 1. Generar guion (si no hay)
if not has_guion:
    if ep.kind == "M":
        actions.append(Action(
            key=f"act_gen_guion_M_{ep.id}",
            label="Generar guion",
            icon="📝",
            primary=True,
            help="Lanza generar_guion.py para este módulo.",
            callback=lambda: _open_pipeline(
                "generar_guion",
                initial={
                    "--modulo": int(ep.module.removeprefix("M")),
                    "--pdf": str(_find_resumen_pdf(ep.module) or ""),
                },
            ),
        ))
    else:
        actions.append(Action(
            key=f"act_gen_guion_T_{ep.id}",
            label="Generar guion T",
            icon="📑",
            primary=True,
            help="Lanza generar_guion_t.py para este sub-tema.",
            callback=lambda: _open_pipeline(
                "generar_guion_t",
                initial={"--pdf": str(_find_tema_pdf(ep) or "")},
            ),
        ))

# 2. Generar audio (si hay guion pero no audio)
if has_guion and not has_audio:
    actions.append(Action(
        key=f"act_gen_audio_{ep.id}",
        label="Generar audio",
        icon="🎧",
        primary=not actions,
        help="Sintetiza el audio con ElevenLabs.",
        callback=lambda: _open_pipeline(
            "generar_episodio",
            initial={"--guion": str(ep.guion), "--ep": ep.id},
        ),
    ))

# 3. Validar (si hay audio)
if has_audio:
    actions.append(Action(
        key=f"act_validar_{ep.id}",
        label="Validar",
        icon="✅",
        help="Comprueba MP3, duración, bloques, reproducibilidad.",
        callback=lambda: _open_pipeline(
            "validar_episodio",
            initial={
                "--ep": ep.id,
                "--guion": str(ep.guion) if ep.guion else "",
                "--mp3": str(ep.audio),
            },
        ),
    ))

# 4. Arreglar con Claude (si hay errores)
if has_errors:
    actions.append(Action(
        key=f"act_fix_{ep.id}",
        label="Arreglar con Claude",
        icon="🛠️",
        primary=not any(a.primary for a in actions),
        help="Sesión Claude con los errores y logs como contexto.",
        callback=_open_fix,
    ))

# 5. Regenerar audio (si ya hay)
if has_audio:
    actions.append(Action(
        key=f"act_regen_audio_{ep.id}",
        label="Regenerar audio",
        icon="🔄",
        help="Vuelve a sintetizar todo el audio.",
        callback=lambda: _open_pipeline(
            "generar_episodio",
            initial={"--guion": str(ep.guion) if ep.guion else "", "--ep": ep.id},
        ),
    ))

if actions:
    action_bar(ActionGroup(
        title="Acciones disponibles",
        hint="Las acciones aparecen según el estado actual del episodio.",
        actions=actions,
    ))


# ---------------------------------------------------------------
# Helpers para localizar PDFs fuente
# ---------------------------------------------------------------


def _find_resumen_pdf(module: str) -> Path | None:
    """Busca PDFs/resumenes/RESUMEN_<module>_*.pdf."""
    resumenes = paths.pdfs_dir() / "resumenes"
    if not resumenes.exists():
        return None
    cand = sorted(resumenes.glob(f"RESUMEN_{module}_*.pdf"))
    return cand[0] if cand else None


def _find_tema_pdf(ep_obj) -> Path | None:
    """Busca PDFs/temas/<module>_T<n>_*.pdf."""
    temas = paths.pdfs_dir() / "temas"
    if not temas.exists():
        return None
    cand = sorted(temas.glob(f"{ep_obj.module}_T{ep_obj.number}_*.pdf"))
    return cand[0] if cand else None


# ---------------------------------------------------------------
# Modales: pipeline y fix con Claude
# ---------------------------------------------------------------


@st.dialog("Lanzar pipeline", width="large")
def _pipeline_dialog() -> None:
    pipe_id = st.session_state.get("_pipeline_modal_pipe")
    initial = st.session_state.get("_pipeline_modal_init") or {}
    try:
        pipe = connectors.get(pipe_id)
    except KeyError:
        st.error(f"Pipeline `{pipe_id}` no encontrado.")
        return
    if not isinstance(pipe, PipelineConnector):
        st.error(f"`{pipe_id}` no es un pipeline.")
        return

    st.markdown(
        f"<div class='mp-eyebrow'>{pipe.icon} {pipe.label}</div>"
        f"<div style='color:var(--mp-text-dim); margin-top:6px;'>{pipe.description}</div>",
        unsafe_allow_html=True,
    )
    if initial:
        info_callout(
            "Algunos campos se han pre-rellenado con el contexto del episodio "
            f"`{ep.id}`. Revisa antes de ejecutar.",
            kind="tip",
        )
    render_pipeline(
        pipe,
        key=f"epdlg_{ep.id}_{pipe.id}",
        initial=initial,
        show_codex=True,
    )


@st.dialog("🛠️ Arreglar errores con Claude", width="large")
def _fix_modal() -> None:
    st.markdown(f"**Episodio:** `{ep.id}`  —  {ep.label}")
    st.caption(
        "Sesión dedicada con Claude para diagnosticar y proponer un fix a los errores "
        "detectados. La ejecución del fix sigue la política del sandbox: solo contenido "
        "generado y mapa de componentes; nunca código de la app o pipelines."
    )

    fails: list[verifications.CheckResult] = []
    for grp in checks.values():
        fails.extend([c for c in grp if c.status == "fail"])
    if fails:
        st.markdown("**Errores detectados:**")
        for c in fails:
            st.markdown(f"- {c.icon} **{c.label}** — {c.detail}")
    else:
        st.info("No hay errores activos.")

    extra = []
    extra.append(f"Episodio: {ep.id}  ({ep.label})")
    extra.append(f"Módulo: {ep.module} · Tipo: {ep.kind}")
    extra.append("")
    extra.append("Estado de archivos:")
    for c in episodes.CONTENT_TYPES:
        p = getattr(ep, c, None)
        extra.append(f"  - {c}: {p.name if p else 'FALTA'}")
    if ep.logs:
        extra.append("Logs:")
        for lp in ep.logs:
            extra.append(f"  - {lp.name}")
    extra.append("")
    extra.append("Verificaciones:")
    for kind, lst in checks.items():
        for c in lst:
            extra.append(f"  [{c.status.upper()}] {kind}.{c.id}: {c.label} — {c.detail}")

    render_improve_block(
        source=f"episode:{ep.id}:fix",
        context=(
            "Sesión de arreglo de errores de generación de un episodio. "
            "Diagnostica las causas raíz a partir de logs + verificaciones y propón "
            "un fix mínimo. Si requiere regenerar contenido, indica qué pipeline."
        ),
        default_prompt=(
            "Analiza los errores listados y propón el fix más simple. "
            "Si hay que regenerar contenido, indica el comando exacto."
        ),
        extra_context_builder=lambda: "\n".join(extra),
        kind="fix",
        title="🛠️ Diagnóstico y fix",
    )


# Abrir modales si toca (mismo patrón que _fix_modal: flag → pop → call)
if st.session_state.pop("_open_fix_modal", False):
    _fix_modal()
if st.session_state.pop("_open_pipeline_modal", False):
    _pipeline_dialog()


# ---------------------------------------------------------------
# Tabs de contenidos
# ---------------------------------------------------------------

tab_g, tab_pdf, tab_esc, tab_audio, tab_logs, tab_ver = st.tabs([
    "📝 Guion",
    "📕 PDF",
    "🗂️ Escaleta",
    "🎧 Audio",
    "📜 Logs",
    "✅ Verificaciones",
])


def _show_text_file(path: Path | None, lang: str = "markdown") -> None:
    if path is None or not path.exists():
        st.warning("Archivo no disponible.")
        return
    st.caption(f"`{path}`")
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        st.error(f"Error leyendo el archivo: {e}")
        return
    st.download_button(
        "⬇️ Descargar",
        content,
        file_name=path.name,
        mime="text/plain",
        key=f"dl_{path.name}",
    )
    if len(content) > 100_000:
        st.info(f"Archivo largo ({len(content):,} chars). Se muestra primer fragmento.")
        content = content[:100_000] + "\n\n[... truncado]"
    st.code(content, language=lang)


with tab_g:
    if ep.guion:
        _show_text_file(ep.guion, lang="markdown")
    else:
        st.warning("Sin guion. Pulsa **Generar guion** en el action bar superior.")

with tab_pdf:
    if has_pdf:
        st.caption(f"`{ep.pdf}`")
        with open(ep.pdf, "rb") as f:
            data = f.read()
        st.download_button(
            "⬇️ Descargar PDF", data, file_name=ep.pdf.name, mime="application/pdf",
        )
        b64 = base64.b64encode(data).decode("ascii")
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="800" style="border:1px solid var(--mp-border);"></iframe>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("Sin PDF fuente.")

with tab_esc:
    _show_text_file(ep.escaleta, lang="markdown")

with tab_audio:
    if has_audio:
        st.caption(f"`{ep.audio}`")
        st.audio(str(ep.audio))
        sz = ep.audio.stat().st_size
        st.caption(f"Tamaño: {sz:,} bytes  ·  {sz / 1_048_576:.1f} MB")
    else:
        st.warning("Sin audio. Pulsa **Generar audio** en el action bar superior.")

with tab_logs:
    if not ep.logs:
        st.info("Sin logs de producción para este episodio.")
    else:
        for lp in ep.logs:
            with st.expander(f"📜 {lp.name}", expanded=False):
                try:
                    txt = lp.read_text(encoding="utf-8", errors="replace")
                except OSError as e:
                    st.error(str(e))
                    continue
                if len(txt) > 80_000:
                    st.caption(f"Log de {len(txt):,} chars — mostrando últimos 80 000.")
                    txt = txt[-80_000:]
                st.code(txt, language="log")

with tab_ver:
    st.markdown("### Verificaciones por contenido")
    for kind in ("pdf", "guion", "escaleta", "audio", "logs"):
        results = checks.get(kind, [])
        if not results:
            continue
        n_ok = sum(1 for c in results if c.status == "ok")
        n_fail = sum(1 for c in results if c.status == "fail")
        n_warn = sum(1 for c in results if c.status == "warn")
        pills = (
            status_pill(f"{n_ok} OK", kind="ok")
            + " " + status_pill(f"{n_warn} warn", kind="warn")
            + " " + status_pill(f"{n_fail} fail", kind="fail")
        )
        title = f"{episodes.CONTENT_ICON.get(kind, '')} {kind.upper()}"
        with st.expander(title, expanded=n_fail > 0):
            st.markdown(pills, unsafe_allow_html=True)
            st.markdown("")
            for c in results:
                st.markdown(f"- {c.icon} **{c.label}** — {c.detail or '—'}")

    if has_errors:
        st.divider()
        if st.button("🛠️ Abrir sesión Claude para arreglar", type="primary"):
            st.session_state["_open_fix_modal"] = True
            st.rerun()


st.divider()
nav = st.columns([1, 1, 4])
if nav[0].button("← Módulo", use_container_width=True):
    st.query_params["m"] = ep.module
    st.switch_page("pages/13_🎬_Modulo.py")
if nav[1].button("← Master", use_container_width=True):
    st.switch_page("pages/0_🎓_Master.py")
