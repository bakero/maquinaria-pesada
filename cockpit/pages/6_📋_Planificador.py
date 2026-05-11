from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st  # noqa: E402

from cockpit.core import planner  # noqa: E402
from cockpit.theme import inject_theme, render_logo  # noqa: E402
from cockpit.ui import render_status_sidebar  # noqa: E402

st.set_page_config(page_title="Planificador", page_icon="📋", layout="wide")
inject_theme()
render_logo()
render_status_sidebar()
st.title("PLANIFICADOR DE TAREAS")

# ----- Load -----
tasks = planner.load_tasks()
if not tasks:
    st.error(
        "No se han encontrado tareas. Ejecuta `python planner/import_from_md.py` "
        "para generar `planner/tareas.json` desde el source markdown."
    )
    st.stop()

today = date.today()
summary = planner.alert_summary(tasks, today=today)

# ----- Métricas globales -----
m = st.columns(6)
m[0].metric("Total", summary.total)
m[1].metric("Hechas", f"{summary.done}", delta=f"{summary.done/summary.total*100:.0f}%" if summary.total else None)
m[2].metric("Atrasadas", summary.overdue, delta="!" if summary.overdue else None, delta_color="inverse")
m[3].metric("Hoy", summary.due_today)
m[4].metric("Publicación hoy", summary.publishing_today)
m[5].metric("Críticas (14d)", summary.upcoming_critical)

st.divider()

# ----- Tabs -----
tab_hoy, tab_atrasadas, tab_criticas, tab_explorar, tab_admin = st.tabs([
    "🔥 HOY",
    "⚠️ ATRASADAS",
    "🔴 CRÍTICAS PRÓXIMAS",
    "🔍 EXPLORAR",
    "⚙️ ADMIN",
])


def _render_task(t: planner.Task, key_prefix: str = "") -> None:
    """Render a single task as an interactive container."""
    border_emoji = "🔴" if t.critical else ("🔍" if t.is_check else "📝")
    status_emoji = {
        "pending": "⬜",
        "in_progress": "🟡",
        "done": "✅",
        "blocked": "🟥",
    }.get(t.status, "⬜")

    with st.container(border=True):
        head = st.columns([6, 1.5, 1.5])
        head[0].markdown(
            f"**{t.id}** · {border_emoji} {t.title}"
        )
        head[1].markdown(f"{status_emoji} `{t.status}`")
        head[2].markdown(f"👤 `{t.owner or '—'}`")

        info = st.columns([1.5, 1.5, 3])
        # LISTA
        lista_display = t.lista_raw or "—"
        if t.lista_date:
            iso_today = today.isoformat()
            if t.lista_date < iso_today:
                lista_display = f"🔴 {t.lista_date}" + (f" {t.lista_time}" if t.lista_time else "")
            elif t.lista_date == iso_today:
                lista_display = f"🟡 HOY" + (f" {t.lista_time}" if t.lista_time else "")
            else:
                lista_display = f"📅 {t.lista_date}" + (f" {t.lista_time}" if t.lista_time else "")
        info[0].caption(f"LISTA · {lista_display}")
        # SALE
        sale_display = t.sale_raw if t.sale_raw and t.sale_raw != "—" else "—"
        if t.sale_date:
            sale_display = f"📤 {t.sale_date}" + (f" {t.sale_time}" if t.sale_time else "")
        info[1].caption(f"SALE · {sale_display}")
        # Block context
        info[2].caption(f"📂 {t.block}" + (f" · {t.subsection}" if t.subsection else ""))

        # Deps
        if t.deps:
            st.caption("Dependencias: " + " · ".join(f"`{d}`" for d in t.deps))

        # Acciones
        cols = st.columns([1, 1, 1, 1, 4])
        if cols[0].button("✅ Done", key=f"{key_prefix}_done_{t.id}",
                          disabled=(t.status == "done"),
                          use_container_width=True):
            planner.set_status(t.id, "done")
            st.rerun()
        if cols[1].button("🟡 In prog.", key=f"{key_prefix}_inp_{t.id}",
                          disabled=(t.status == "in_progress"),
                          use_container_width=True):
            planner.set_status(t.id, "in_progress")
            st.rerun()
        if cols[2].button("🟥 Blocked", key=f"{key_prefix}_blk_{t.id}",
                          disabled=(t.status == "blocked"),
                          use_container_width=True):
            planner.set_status(t.id, "blocked")
            st.rerun()
        if cols[3].button("⬜ Reset", key=f"{key_prefix}_rst_{t.id}",
                          disabled=(t.status == "pending"),
                          use_container_width=True):
            planner.set_status(t.id, "pending")
            st.rerun()

        if t.completed_at:
            cols[4].caption(f"✅ Completada: {t.completed_at[:19]}")

        # Notes
        with st.expander("📝 Notas", expanded=bool(t.notes)):
            new_notes = st.text_area(
                "Notas", value=t.notes, key=f"{key_prefix}_notes_{t.id}",
                label_visibility="collapsed", height=80,
            )
            if new_notes != t.notes:
                if st.button("Guardar notas", key=f"{key_prefix}_save_notes_{t.id}"):
                    planner.set_notes(t.id, new_notes)
                    st.rerun()


# ----- TAB: HOY -----
with tab_hoy:
    st.subheader(f"Tareas con `LISTA` = {today.isoformat()}")
    due = sorted(planner.due_today(tasks, today=today),
                 key=lambda x: (x.lista_time or "23:59", x.id))
    if not due:
        st.success("Sin tareas con fecha límite hoy 🎉")
    for t in due:
        _render_task(t, key_prefix="hoy")

    st.divider()
    st.subheader(f"Publicaciones con `SALE` = {today.isoformat()}")
    pub = sorted(planner.publishing_today(tasks, today=today),
                 key=lambda x: (x.sale_time or "23:59", x.id))
    if not pub:
        st.info("Sin publicaciones programadas para hoy.")
    for t in pub:
        _render_task(t, key_prefix="pub")


# ----- TAB: ATRASADAS -----
with tab_atrasadas:
    od = sorted(planner.overdue(tasks, today=today),
                key=lambda x: (x.lista_date or "9999", x.lista_time or "23:59"))
    st.subheader(f"{len(od)} tareas atrasadas (LISTA < hoy, sin done)")
    if not od:
        st.success("Sin atrasos 💪")
    for t in od[:50]:
        _render_task(t, key_prefix="od")
    if len(od) > 50:
        st.caption(f"... y {len(od) - 50} más. Cierra o avanza algunas para ver el resto.")


# ----- TAB: CRÍTICAS PRÓXIMAS -----
with tab_criticas:
    days = st.slider("Horizonte (días)", 1, 60, 14)
    crit = sorted(planner.upcoming_critical(tasks, days=days, today=today),
                  key=lambda x: (x.lista_date or "9999", x.lista_time or "23:59"))
    st.subheader(f"{len(crit)} hitos críticos 🔴 en los próximos {days} días")
    if not crit:
        st.info(f"Sin hitos críticos en los próximos {days} días.")
    for t in crit:
        _render_task(t, key_prefix="crit")


# ----- TAB: EXPLORAR -----
with tab_explorar:
    f = st.columns([2, 2, 2, 3])
    blocks = sorted({t.block for t in tasks if t.block})
    sel_block = f[0].selectbox("Bloque/Semana", ["(todos)"] + blocks, index=0)
    owners = sorted({t.owner for t in tasks if t.owner})
    sel_owner = f[1].selectbox("Owner", ["(todos)"] + owners, index=0)
    statuses = ["(todos)"] + list(planner.VALID_STATUSES)
    sel_status = f[2].selectbox("Status", statuses, index=0)
    search = f[3].text_input("Buscar en título", "")

    show_critical_only = st.checkbox("🔴 Solo críticas", value=False)
    show_checks = st.checkbox("Incluir tareas CHECK", value=True)
    show_recurring = st.checkbox("Incluir recurrentes (diario/continuo)", value=False)

    filtered = tasks
    if sel_block != "(todos)":
        filtered = [t for t in filtered if t.block == sel_block]
    if sel_owner != "(todos)":
        filtered = [t for t in filtered if t.owner == sel_owner]
    if sel_status != "(todos)":
        filtered = [t for t in filtered if t.status == sel_status]
    if search:
        s = search.lower()
        filtered = [t for t in filtered if s in t.title.lower() or s in t.id.lower()]
    if show_critical_only:
        filtered = [t for t in filtered if t.critical]
    if not show_checks:
        filtered = [t for t in filtered if not t.is_check]
    if not show_recurring:
        filtered = [t for t in filtered if not t.recurring]

    st.caption(f"Mostrando {len(filtered)} de {len(tasks)} tareas")

    # Compact dataframe overview
    rows = []
    for t in filtered:
        rows.append({
            "ID": t.id,
            "🔴": "🔴" if t.critical else "",
            "✓": "✅" if t.is_done else ("🟡" if t.status == "in_progress" else ("🟥" if t.status == "blocked" else "⬜")),
            "Título": t.title[:80],
            "Owner": t.owner,
            "LISTA": (t.lista_date or t.lista_raw or "") + (f" {t.lista_time}" if t.lista_time else ""),
            "SALE": (t.sale_date or "") + (f" {t.sale_time}" if t.sale_time else ""),
            "Bloque": t.block.split("—")[0].strip() if t.block else "",
        })
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True, height=480)

    st.divider()
    detail_id = st.text_input("Ver detalle por ID (ej: T093)", "")
    if detail_id:
        match = next((t for t in tasks if t.id.upper() == detail_id.strip().upper()), None)
        if match:
            _render_task(match, key_prefix="detail")
        else:
            st.warning(f"No encontrado: {detail_id}")


# ----- TAB: ADMIN -----
with tab_admin:
    st.subheader("Re-importar desde markdown")
    st.write(
        "Si has actualizado `planner/source/*.md`, ejecuta:\n\n"
        "```powershell\npython planner/import_from_md.py\n```\n\n"
        "Eso regenera `planner/tareas.json` desde el último .md por orden lexicográfico. "
        "El estado de las tareas (`planner/_state.json`) se preserva."
    )

    st.divider()
    st.subheader("Distribución por status")
    by = planner.by_status(tasks)
    for status in planner.VALID_STATUSES:
        items = by.get(status, [])
        st.write(f"- **{status}**: {len(items)}")

    st.divider()
    st.subheader("Recurrentes")
    rec = [t for t in tasks if t.recurring]
    st.caption(f"{len(rec)} tareas marcadas como recurrentes (diario/continuo)")
    for t in rec:
        st.write(f"- `{t.id}` ({t.lista_raw}): {t.title[:80]}")
