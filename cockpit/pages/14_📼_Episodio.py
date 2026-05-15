"""Página Episodio — vista única por episodio.

Muestra guion, PDF, escaleta, audio, logs y verificaciones por contenido.
Si hay errores, botón superior derecho abre sesión con Claude para arreglarlos.

Query param: ?ep=<episode_id>  (e.g. M3, M3_T2)
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import episodes, verifications  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402
from cockpit.ui_components import Stat, page_header, stat_grid  # noqa: E402
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

top = st.columns([5, 2, 2])
with top[0]:
    page_header(
        "Control de episodio",
        eyebrow="Episodio",
        subtitle="Guion, PDF, escaleta, audio, logs y verificaciones — todo en una vista.",
    )

with top[1]:
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

# Estado de verificaciones (necesario para el botón de errores)
checks = verifications.run_all(ep)
has_errors = any(c.status == "fail" for grp in checks.values() for c in grp)

# Botón superior derecho: arreglar con Claude (solo visible si hay errores)
with top[2]:
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    if has_errors:
        if st.button("🛠️ Arreglar con Claude", type="primary", use_container_width=True):
            st.session_state["_open_fix_modal"] = True
    else:
        st.success("Sin errores")

# Métricas
stat_grid([
    Stat("Episodio", ep.id, hint=ep.label),
    Stat("Tipo", "Módulo" if ep.kind == "M" else f"Tema T{ep.number}"),
    Stat("Producidos", f"{len(ep.produced)}/{len(episodes.CONTENT_TYPES)}", color="primary"),
    Stat("Progreso", f"{ep.progress*100:.0f}%"),
    Stat("Errores", "Sí" if has_errors else "No", color="alert" if has_errors else "ok"),
])

st.divider()


# --- Modal de arreglo con Claude ---
@st.dialog("🛠️ Arreglar errores con Claude", width="large")
def _fix_modal() -> None:
    st.markdown(f"**Episodio:** `{ep.id}`  —  {ep.label}")
    st.caption(
        "Sesión dedicada con Claude para diagnosticar y proponer un fix a los errores "
        "detectados. La ejecución del fix sigue la política del sandbox: solo contenido "
        "generado y mapa de componentes; nunca código de la app o pipelines."
    )

    # Resumen de fallos
    fails: list[verifications.CheckResult] = []
    for grp in checks.values():
        fails.extend([c for c in grp if c.status == "fail"])
    if fails:
        st.markdown("**Errores detectados:**")
        for c in fails:
            st.markdown(f"- {c.icon} **{c.label}** — {c.detail}")
    else:
        st.info("No hay errores activos.")

    # Bloque de mejora con contexto del episodio
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


if st.session_state.pop("_open_fix_modal", False):
    _fix_modal()


# --- Tabs de contenidos ---
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
        st.warning("Sin guion. Genera con `generar_guion.py`.")

with tab_pdf:
    if ep.pdf and ep.pdf.exists():
        st.caption(f"`{ep.pdf}`")
        with open(ep.pdf, "rb") as f:
            data = f.read()
        st.download_button("⬇️ Descargar PDF", data, file_name=ep.pdf.name, mime="application/pdf")
        # Embed via base64 — funciona en la mayoría de navegadores
        import base64
        b64 = base64.b64encode(data).decode("ascii")
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="800" style="border:1px solid #3A3A3A;"></iframe>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("Sin PDF fuente.")

with tab_esc:
    _show_text_file(ep.escaleta, lang="markdown")

with tab_audio:
    if ep.audio and ep.audio.exists():
        st.caption(f"`{ep.audio}`")
        st.audio(str(ep.audio))
        sz = ep.audio.stat().st_size
        st.caption(f"Tamaño: {sz:,} bytes")
    else:
        st.warning("Sin audio. Genera con `generar_episodio_v2.py`.")

with tab_logs:
    if not ep.logs:
        st.info("Sin logs de producción.")
    else:
        for lp in ep.logs:
            with st.expander(f"📜 {lp.name}", expanded=False):
                try:
                    txt = lp.read_text(encoding="utf-8", errors="replace")
                except OSError as e:
                    st.error(str(e))
                    continue
                # Subraya errores: tail si es muy largo
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
        title = f"{episodes.CONTENT_ICON.get(kind, '')} {kind.upper()}  · ✅ {n_ok}  ❌ {n_fail}  ⚠️ {n_warn}"
        with st.expander(title, expanded=n_fail > 0):
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
