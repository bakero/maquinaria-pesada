"""Renderer de terminal con colores ANSI."""

from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import datetime

from ..rules.base import Finding, Severity

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") != "1"


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def red(t: str) -> str:
    return _c("31", t)


def yellow(t: str) -> str:
    return _c("33", t)


def green(t: str) -> str:
    return _c("32", t)


def gray(t: str) -> str:
    return _c("90", t)


def bold(t: str) -> str:
    return _c("1", t)


def render_terminal(results: list[dict], directory: str, mode: str) -> str:
    out: list[str] = []
    sep = "=" * 72
    line_sep = "-" * 72
    out.append(sep)
    out.append(
        bold("EVALUADOR DE GUIONES")
        + " · MaquinarIA Pesada · "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    out.append(sep)
    out.append(f"Directorio: {directory}")
    counts = Counter(r["kind"] for r in results if r.get("kind"))
    parts = ", ".join(f"{n} {k}" for k, n in sorted(counts.items()))
    out.append(f"Ficheros encontrados: {len(results)} ({parts})")
    out.append(f"Modo: {mode}")
    out.append("")

    total_hard = 0
    total_soft = 0
    n_pass = 0
    for r in results:
        out.append(line_sep)
        title = f"{r['filename']} · {r.get('kind', '?')}"
        meta = r.get("metadata", {})
        meta_bits = []
        if meta.get("opener"):
            meta_bits.append(f"opener {meta['opener']}")
        if meta.get("module_number") is not None:
            meta_bits.append(f"M{meta['module_number']}")
        if meta.get("tema_number") is not None:
            meta_bits.append(f"T{meta['tema_number']}")
        if meta.get("s_number") is not None:
            meta_bits.append(f"S{meta['s_number']}")
        if meta.get("word_count") is not None:
            meta_bits.append(f"{meta['word_count']} palabras")
        if meta_bits:
            title += " · " + " · ".join(meta_bits)
        out.append(title)
        out.append(line_sep)

        findings = r.get("findings", [])
        if r.get("error"):
            out.append(red(f"  ERROR  {r['error']}"))
            out.append("")
            continue

        if not findings:
            out.append(green("  ✓ Sin findings"))
            n_pass += 1
        else:
            hard = sum(1 for f in findings if f["severity"] == "hard")
            soft = sum(1 for f in findings if f["severity"] == "soft")
            total_hard += hard
            total_soft += soft
            if hard == 0:
                n_pass += 1
            for f in findings:
                tag = red("HARD") if f["severity"] == "hard" else yellow("SOFT")
                line_info = f"L{f['line']}" if f.get("line") else "—"
                speaker = f"{f.get('speaker', '')}" if f.get("speaker") else ""
                sec = f"[{f.get('section', '')}]" if f.get("section") else ""
                out.append(
                    f"  {tag}  {gray(f['code'])}  {line_info} {speaker} {sec}".rstrip()
                )
                out.append(f"         {f['message']}")
                if f.get("snippet"):
                    out.append(gray(f"         └─ {f['snippet'][:80]}"))
            out.append("")
            sev_summary = []
            if hard:
                sev_summary.append(red(f"{hard} hard-fail"))
            if soft:
                sev_summary.append(yellow(f"{soft} soft-warn"))
            out.append(f"  RESUMEN: {' · '.join(sev_summary)}")
        out.append("")

    out.append(sep)
    out.append(
        f"TOTAL: {len(results)} ficheros · "
        + red(f"{total_hard} hard-fail")
        + " · "
        + yellow(f"{total_soft} soft-warn")
    )
    pass_pct = (n_pass / len(results) * 100) if results else 0
    out.append(green(f"PASS:  {n_pass} ({pass_pct:.0f}%) sin hard-fail"))
    out.append(sep)
    return "\n".join(out)
