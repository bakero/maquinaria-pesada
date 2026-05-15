"""Reusable UI primitives for the cockpit.

Helpers that render polished blocks (page headers, stat grids, status pills,
section labels, empty states) using the CSS classes injected by
``cockpit.theme``. Pages should prefer these over hand-rolling HTML so the
look stays consistent.

Every helper is a thin wrapper around ``st.markdown(..., unsafe_allow_html=
True)``. No state, no side-effects beyond rendering.
"""
from __future__ import annotations

import html
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

import streamlit as st

PillKind = Literal["ok", "warn", "fail", "info", "primary", "neutral"]
StatColor = Literal["default", "ok", "warn", "alert", "primary"]


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page_header(
    title: str,
    *,
    eyebrow: str | None = None,
    subtitle: str | None = None,
) -> None:
    """Editorial page header: eyebrow + title + subtitle.

    Use once at the top of each page in place of ``st.title()`` so all pages
    get the same visual rhythm and a separator line below.
    """
    parts = ['<div class="mp-page-header">']
    if eyebrow:
        parts.append(f'<div class="mp-eyebrow">{_esc(eyebrow)}</div>')
    parts.append(f"<h1>{_esc(title)}</h1>")
    if subtitle:
        parts.append(f'<p class="mp-subtitle">{_esc(subtitle)}</p>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def section(title: str, *, subtitle: str | None = None) -> None:
    """Small section heading (uppercase, tracked) — for grouping inside a page."""
    parts = ['<div class="mp-section">']
    parts.append(f'<div class="mp-section-title">{_esc(title)}</div>')
    if subtitle:
        parts.append(f'<div class="mp-section-subtitle">{_esc(subtitle)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


@dataclass(frozen=True)
class Stat:
    """One stat tile. ``value`` is rendered as-is (already formatted)."""

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
    """Render a row of stat cards. Defaults to one column per stat."""
    stats_list = list(stats)
    if not stats_list:
        return
    n = columns if columns is not None else len(stats_list)
    cols = st.columns(n)
    for idx, stat in enumerate(stats_list):
        with cols[idx % n]:
            st.markdown(_stat_card_html(stat), unsafe_allow_html=True)


def status_pill(label: str, *, kind: PillKind = "neutral") -> str:
    """Return inline HTML for a status pill. Embed it inside other markdown."""
    return f'<span class="mp-pill {kind}">{_esc(label)}</span>'


def render_pill(label: str, *, kind: PillKind = "neutral") -> None:
    """Render a status pill on its own."""
    st.markdown(status_pill(label, kind=kind), unsafe_allow_html=True)


def empty_state(
    title: str,
    *,
    hint: str | None = None,
    icon: str = "·",
) -> None:
    """Friendly empty-state placeholder — for pages with no data yet."""
    parts = ['<div class="mp-empty">']
    parts.append(f'<div class="mp-empty-icon">{_esc(icon)}</div>')
    parts.append(f'<div class="mp-empty-title">{_esc(title)}</div>')
    if hint:
        parts.append(f'<div class="mp-empty-hint">{_esc(hint)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
