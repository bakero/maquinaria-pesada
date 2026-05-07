"""Shared UI fragments used by every Streamlit page."""
from __future__ import annotations

import time
from pathlib import Path

from cockpit.core import monitor


def render_status_sidebar(auto_refresh_seconds: int = 5) -> None:
    """Render the persistent 'Producción en vivo' panel in the sidebar.

    Call at the top of every page (and app.py). The sidebar persists across
    navigation, but its contents are re-rendered per page, so each page must
    call this function.
    """
    import streamlit as st

    with st.sidebar:
        st.markdown("### 🎬 Producción en vivo")

        if not monitor._HAS_PSUTIL:
            st.error("`psutil` no está instalado. `pip install psutil` para detección de procesos.")
            return

        try:
            from streamlit_autorefresh import st_autorefresh  # type: ignore
            st_autorefresh(interval=auto_refresh_seconds * 1000, key="sidebar_status_refresh")
        except ImportError:
            st.caption("⚠️ `streamlit-autorefresh` no instalado: refresh manual.")

        running = monitor.scan_running()

        if not running:
            st.info("Inactivo. Sin scripts del pipeline detectados.")
            _render_recent_outputs_block(st, monitor.recent_outputs(max_age_s=60), title="Últimos archivos (60s)")
            st.caption(f"Refresh: {auto_refresh_seconds}s")
            return

        for rp in running:
            with st.container(border=True):
                st.markdown(f"**{rp.label}**")
                st.caption(f"`{rp.script}` · PID {rp.pid} · {monitor.format_elapsed(rp.elapsed_s)}")
                st.caption(f"📍 RAM {rp.memory_mb:.0f} MB")

                if rp.active_log:
                    st.caption(f"📜 `{rp.active_log.name}`")
                    if rp.log_tail:
                        st.code("\n".join(rp.log_tail[-3:]), language="log")
                else:
                    st.caption("📜 sin log activo detectado")

        # Files appearing during this run.
        all_outputs = running[0].recent_outputs if running else []
        _render_recent_outputs_block(st, all_outputs, title="Generándose ahora")
        st.caption(f"Refresh: {auto_refresh_seconds}s · {len(running)} proceso(s)")


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
