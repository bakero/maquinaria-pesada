"""Shared UI fragments used by every Streamlit page."""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path

from cockpit.core import monitor


def render_planner_widget() -> None:
    """Compact planner alert block for the sidebar."""
    import streamlit as st

    try:
        from cockpit.core import planner
    except Exception as exc:
        st.caption(f"⚠️ planner indisponible: {exc!r}")
        return

    tasks = planner.load_tasks()
    if not tasks:
        st.caption("Sin planificador cargado.")
        st.caption("→ `python planner/import_from_md.py`")
        return

    today = date.today()
    s = planner.alert_summary(tasks, today=today)

    # Render summary line with chips
    chips = []
    if s.overdue:
        chips.append(f"🔴 {s.overdue} atras.")
    if s.due_today:
        chips.append(f"🟡 {s.due_today} hoy")
    if s.publishing_today:
        chips.append(f"📤 {s.publishing_today} publ.")
    if s.upcoming_critical:
        chips.append(f"⚠️ {s.upcoming_critical} crít.")

    if chips:
        st.markdown(" · ".join(chips))
    else:
        st.success("Sin alertas")

    # Progress
    pct = (s.done / s.total * 100) if s.total else 0
    st.caption(f"Progreso: **{s.done}/{s.total}** ({pct:.0f}%)")
    st.progress(pct / 100, text=None)

    # Quick list of today's tasks (top 3)
    due = planner.due_today(tasks, today=today)
    if due:
        with st.expander(f"🟡 Hoy ({len(due)})", expanded=False):
            for t in sorted(due, key=lambda x: (x.lista_time or "23:59"))[:5]:
                hour = f"`{t.lista_time}`" if t.lista_time else "•"
                critmark = "🔴" if t.critical else ""
                st.caption(f"{hour} {critmark} **{t.id}** {t.title[:48]}")

    # Quick list of overdue (top 3)
    od = planner.overdue(tasks, today=today)
    if od:
        with st.expander(f"🔴 Atrasadas ({len(od)})", expanded=False):
            for t in sorted(od, key=lambda x: x.lista_date or "9999")[:5]:
                dt = t.lista_date or t.lista_raw
                critmark = "🔴" if t.critical else ""
                st.caption(f"📅 {dt} {critmark} **{t.id}** {t.title[:48]}")


def render_status_sidebar(auto_refresh_seconds: int = 5) -> None:
    """Render the persistent 'Producción en vivo' panel in the sidebar.

    Call at the top of every page (and app.py). The sidebar persists across
    navigation, but its contents are re-rendered per page, so each page must
    call this function.
    """
    import streamlit as st

    with st.sidebar:
        st.markdown("### 📋 PLANIFICADOR")
        render_planner_widget()
        st.divider()

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
