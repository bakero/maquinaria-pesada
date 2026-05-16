"""Shared UI fragments used by every Streamlit page."""
from __future__ import annotations

import html
import time
from pathlib import Path

from cockpit.core import monitor


def render_status_sidebar(auto_refresh_seconds: int = 5) -> None:
    """Render the persistent "Producción en vivo" panel in the sidebar.

    Call at the top of every page (and app.py). Streamlit re-renders the
    sidebar per page, so each page must call this function.
    """
    import streamlit as st

    with st.sidebar:
        st.markdown("### Producción en vivo")

        if not monitor._HAS_PSUTIL:
            st.error("`psutil` no está instalado.")
            return

        try:
            from streamlit_autorefresh import st_autorefresh  # type: ignore
            st_autorefresh(interval=auto_refresh_seconds * 1000, key="sidebar_status_refresh")
        except ImportError:
            st.caption("⚠️ `streamlit-autorefresh` no instalado — refresh manual.")

        running = monitor.scan_running()

        if not running:
            _render_idle_card(st)
            _render_recent_outputs_block(
                st,
                monitor.recent_outputs(max_age_s=60),
                title="Últimos archivos · 60s",
            )
            st.caption(f"Refresh cada {auto_refresh_seconds}s")
            return

        for rp in running:
            tail = ""
            if rp.log_tail:
                last = rp.log_tail[-1].strip()
                if last:
                    tail = (
                        '<div class="mp-side-tail">'
                        f"{html.escape(last[:140])}"
                        "</div>"
                    )
            log_line = (
                f'<div class="mp-side-log">📜 {html.escape(rp.active_log.name)}</div>'
                if rp.active_log
                else '<div class="mp-side-log">sin log activo</div>'
            )
            st.markdown(
                f"""
<div class="mp-run-card">
  <div class="mp-run-head">
    <span class="mp-pill ok">{html.escape(rp.label)}</span>
    <span class="mp-side-elapsed">{html.escape(monitor.format_elapsed(rp.elapsed_s))}</span>
  </div>
  <div class="mp-side-meta">
    <code>{html.escape(rp.script)}</code> · PID {rp.pid} · {rp.memory_mb:.0f} MB
  </div>
  {log_line}
  {tail}
</div>
                """,
                unsafe_allow_html=True,
            )

        all_outputs = running[0].recent_outputs if running else []
        _render_recent_outputs_block(st, all_outputs, title="Generándose ahora")
        st.caption(f"{len(running)} proceso(s) · refresh {auto_refresh_seconds}s")

    _inject_sidebar_css()


def _render_idle_card(st) -> None:
    st.markdown(
        """
<div class="mp-run-card idle">
  <div class="mp-run-head">
    <span class="mp-pill neutral">Inactivo</span>
  </div>
  <div class="mp-side-meta">Sin scripts del pipeline detectados.</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_recent_outputs_block(st, outputs: list[Path], title: str) -> None:
    if not outputs:
        return
    with st.expander(f"📂 {title} ({len(outputs)})", expanded=True):
        now = time.time()
        for f in outputs[:8]:
            try:
                age = now - f.stat().st_mtime
                size_kb = f.stat().st_size / 1024
                st.caption(
                    f"`{f.name}` · {monitor.format_age(age)} ago · {size_kb:.0f} KB"
                )
            except OSError:
                continue


_SIDEBAR_CSS_KEY = "_mp_sidebar_css_injected"
_SIDEBAR_CSS = """
<style>
.mp-run-card {
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius);
    background: var(--mp-panel);
    padding: 10px 12px;
    margin: 8px 0;
}
.mp-run-card.idle { opacity: 0.85; }
.mp-run-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}
.mp-side-elapsed {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--mp-text-dim);
}
.mp-side-meta {
    font-size: 0.78rem;
    color: var(--mp-text-mute);
    line-height: 1.45;
    margin-bottom: 4px;
}
.mp-side-meta code { background: transparent; border: none; padding: 0; color: var(--mp-text-dim); }
.mp-side-log {
    font-size: 0.78rem;
    color: var(--mp-text-dim);
    margin-bottom: 4px;
}
.mp-side-tail {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--mp-text-mute);
    background: #07090C;
    border: 1px solid var(--mp-border);
    border-radius: var(--mp-radius-sm);
    padding: 6px 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 4px;
}
</style>
"""


def _inject_sidebar_css() -> None:
    import streamlit as st
    if st.session_state.get(_SIDEBAR_CSS_KEY):
        return
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
    st.session_state[_SIDEBAR_CSS_KEY] = True
