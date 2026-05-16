"""Reusable UI primitives for the cockpit.

Helpers that render polished blocks (page headers, stat grids, status pills,
section labels, empty states, breadcrumbs, action bars, info callouts) using
the CSS classes injected by ``cockpit.theme``. Pages should prefer these
over hand-rolling HTML so the look stays consistent.

Every helper is a thin wrapper around Streamlit primitives + a tiny bit of
HTML. No state, no side-effects beyond rendering.
"""
from __future__ import annotations

import html
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Literal

import streamlit as st

from cockpit import help as _help

PillKind = Literal["ok", "warn", "fail", "info", "primary", "neutral"]
StatColor = Literal["default", "ok", "warn", "alert", "primary"]
CalloutKind = Literal["info", "tip", "warn", "success"]


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


# =====================================================================
# Page header (eyebrow + title + subtitle + optional help button)
# =====================================================================


def page_header(
    title: str,
    *,
    eyebrow: str | None = None,
    subtitle: str | None = None,
    help_page_id: str | None = None,
    breadcrumb: list[tuple[str, str | None]] | None = None,
) -> None:
    """Editorial page header: optional breadcrumb + eyebrow + title + subtitle.

    Pass ``help_page_id`` to render a ``?`` button that opens the help
    dialog for this page. The id must exist in ``cockpit.help.HELP``.
    """
    if breadcrumb:
        _render_breadcrumb(breadcrumb)

    parts = ['<div class="mp-page-header">']
    if eyebrow:
        parts.append(f'<div class="mp-eyebrow">{_esc(eyebrow)}</div>')
    parts.append(f"<h1>{_esc(title)}</h1>")
    if subtitle:
        parts.append(f'<p class="mp-subtitle">{_esc(subtitle)}</p>')
    parts.append("</div>")

    if help_page_id and _help.get(help_page_id):
        cols = st.columns([12, 1])
        with cols[0]:
            st.markdown("".join(parts), unsafe_allow_html=True)
        with cols[1]:
            st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
            if st.button(
                "ⓘ Ayuda",
                key=f"_help_btn_{help_page_id}",
                use_container_width=True,
                help="Abrir guía rápida de esta página",
            ):
                st.session_state[f"_open_help_{help_page_id}"] = True
        _maybe_open_help_dialog(help_page_id)
    else:
        st.markdown("".join(parts), unsafe_allow_html=True)


def _render_breadcrumb(items: list[tuple[str, str | None]]) -> None:
    """Render a breadcrumb. Items are (label, page_path). Last is unlinked."""
    parts = ['<nav class="mp-crumbs">']
    for i, (label, target) in enumerate(items):
        if i > 0:
            parts.append('<span class="mp-crumbs-sep">›</span>')
        if target and i < len(items) - 1:
            parts.append(f'<span class="mp-crumbs-link">{_esc(label)}</span>')
        else:
            parts.append(f'<span class="mp-crumbs-current">{_esc(label)}</span>')
    parts.append("</nav>")
    st.markdown("".join(parts), unsafe_allow_html=True)


# =====================================================================
# Help dialog
# =====================================================================


def _maybe_open_help_dialog(page_id: str) -> None:
    key = f"_open_help_{page_id}"
    if not st.session_state.get(key):
        return
    st.session_state[key] = False
    _help_dialog(page_id)


@st.dialog("Ayuda", width="large")
def _help_dialog(page_id: str) -> None:
    page = _help.get(page_id)
    if page is None:
        st.warning(f"No hay ayuda registrada para `{page_id}`.")
        return
    st.markdown(
        f'<div class="mp-help-eyebrow">Guía rápida</div>'
        f'<h2 class="mp-help-title">{_esc(page.title)}</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="mp-help-summary">{page.summary}</div>',
        unsafe_allow_html=True,
    )

    for section in page.sections:
        st.markdown(
            f'<div class="mp-help-section-title">{_esc(section.title)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(section.body)

    if page.related:
        st.markdown(
            '<div class="mp-help-section-title">Páginas relacionadas</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(min(len(page.related), 3))
        for i, (label, target) in enumerate(page.related):
            with cols[i % len(cols)]:
                if st.button(f"→ {label}", key=f"_help_goto_{page_id}_{i}",
                             use_container_width=True):
                    st.switch_page(target)


# =====================================================================
# Section heading
# =====================================================================


def section(title: str, *, subtitle: str | None = None) -> None:
    parts = ['<div class="mp-section">']
    parts.append(f'<div class="mp-section-title">{_esc(title)}</div>')
    if subtitle:
        parts.append(f'<div class="mp-section-subtitle">{_esc(subtitle)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


# =====================================================================
# Stat cards / grid
# =====================================================================


@dataclass(frozen=True)
class Stat:
    label: str
    value: str
    hint: str | None = None
    color: StatColor = "default"


def _stat_card_html(stat: Stat) -> str:
    color_cls = "" if stat.color == "default" else f" {stat.color}"
    hint = (
        f'<div class="mp-stat-hint">{_esc(stat.hint)}</div>'
        if stat.hint
        else ""
    )
    return (
        '<div class="mp-stat-card">'
        f'<div class="mp-stat-label">{_esc(stat.label)}</div>'
        f'<div class="mp-stat-value{color_cls}">{_esc(stat.value)}</div>'
        f"{hint}"
        "</div>"
    )


def stat_grid(stats: Iterable[Stat], *, columns: int | None = None) -> None:
    stats_list = list(stats)
    if not stats_list:
        return
    n = columns if columns is not None else len(stats_list)
    cols = st.columns(n)
    for idx, stat in enumerate(stats_list):
        with cols[idx % n]:
            st.markdown(_stat_card_html(stat), unsafe_allow_html=True)


# =====================================================================
# Status pills
# =====================================================================


def status_pill(label: str, *, kind: PillKind = "neutral") -> str:
    """Return inline HTML for a status pill. Embed it inside other markdown."""
    return f'<span class="mp-pill {kind}">{_esc(label)}</span>'


def render_pill(label: str, *, kind: PillKind = "neutral") -> None:
    st.markdown(status_pill(label, kind=kind), unsafe_allow_html=True)


# =====================================================================
# Action bar (contextual actions, e.g. on Episodio page)
# =====================================================================


@dataclass
class Action:
    """A button in an action bar."""

    key: str
    label: str
    callback: Callable[[], None] | None = None
    primary: bool = False
    disabled: bool = False
    help: str = ""
    icon: str = ""


@dataclass
class ActionGroup:
    """Group of actions rendered as a sticky-ish bar."""

    title: str = ""
    hint: str = ""
    actions: list[Action] = field(default_factory=list)


def action_bar(group: ActionGroup) -> None:
    """Render a row of contextual action buttons.

    The first action with ``primary=True`` becomes the prominent CTA.
    Callbacks run when the user clicks. Use Streamlit session_state if
    you need state to persist across reruns.
    """
    if not group.actions:
        return

    with st.container(border=True):
        if group.title or group.hint:
            top = st.columns([3, 1])
            with top[0]:
                if group.title:
                    st.markdown(
                        f'<div class="mp-actionbar-title">{_esc(group.title)}</div>',
                        unsafe_allow_html=True,
                    )
                if group.hint:
                    st.caption(group.hint)

        cols = st.columns(len(group.actions))
        for col, action in zip(cols, group.actions, strict=True):
            with col:
                label = f"{action.icon} {action.label}".strip() if action.icon else action.label
                clicked = st.button(
                    label,
                    key=action.key,
                    type="primary" if action.primary else "secondary",
                    disabled=action.disabled,
                    help=action.help or None,
                    use_container_width=True,
                )
                if clicked and action.callback:
                    action.callback()


# =====================================================================
# Info callouts (smaller / softer than st.info)
# =====================================================================


_CALLOUT_ICON = {
    "info": "ⓘ",
    "tip": "💡",
    "warn": "⚠️",
    "success": "✓",
}


def info_callout(message: str, *, kind: CalloutKind = "info") -> None:
    """Soft callout — less heavy than st.info, for inline tips."""
    icon = _CALLOUT_ICON[kind]
    st.markdown(
        f'<div class="mp-callout mp-callout-{kind}">'
        f'<span class="mp-callout-icon">{icon}</span>'
        f"<span>{message}</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def empty_state(
    title: str,
    *,
    hint: str | None = None,
    icon: str = "·",
) -> None:
    parts = ['<div class="mp-empty">']
    parts.append(f'<div class="mp-empty-icon">{_esc(icon)}</div>')
    parts.append(f'<div class="mp-empty-title">{_esc(title)}</div>')
    if hint:
        parts.append(f'<div class="mp-empty-hint">{_esc(hint)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def kbd(*keys: str) -> str:
    """Inline keyboard hint, e.g. ``kbd('⌘','K')``."""
    parts = [f'<kbd class="mp-kbd">{_esc(k)}</kbd>' for k in keys]
    return '<span class="mp-kbd-group">' + "+".join(parts) + "</span>"
