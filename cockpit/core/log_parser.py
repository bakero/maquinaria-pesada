"""Per-category validation summary.

Two sources, in priority order:

1. **Structured JSONL** (`episodios/{episode}_events.jsonl`) emitted by `runlog.py`
   from the generators. Preferred — gives reliable counts, phases, and metrics.
2. **Plain-text log** (`episodios/*.log`) — heuristic regex fallback while the
   generators haven't been migrated yet.

Both sources collapse into the same `CategorySummary` so the UI doesn't change.
The JSONL parser also exposes raw `events` and `phase_counts` for richer rendering.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from . import paths
from . import state as state_mod

# ---- Regex patterns (text fallback) -----------------------------------

_TS = re.compile(r"\b(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\b")
_ERROR_LINE = re.compile(r"\b(ERROR|❌|FAIL(?:ED)?|TRACEBACK)\b", re.IGNORECASE)
_WARN_LINE = re.compile(r"\b(WARNING|WARN|⚠)\b", re.IGNORECASE)
_OK_LINE = re.compile(r"(✅|\bOK\b|\bPASS(?:ED)?\b|\bSUCCESS\b)", re.IGNORECASE)

_KEYWORDS = {
    "pdf":   ("pdf", "extract", "pdfplumber"),
    "guion": ("guion", "script", "validate_script", "bloque", "speaker", "iago", "maria"),
    "audio": ("audio", "mp3", "elevenlabs", "synthesi", "ffmpeg", "credit", "duraci", "block"),
    "video": ("video", "mp4", "luma", "subtitle", "srt", "compose", "render"),
    "log":   (),
}


@dataclass
class CategorySummary:
    module: str
    category: str
    source: str = "none"          # "jsonl" | "text" | "none"
    log_path: Path | None = None
    log_mtime: datetime | None = None
    matched_lines: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ok_signals: list[str] = field(default_factory=list)
    first_ts: str | None = None
    last_ts: str | None = None
    sample: list[str] = field(default_factory=list)
    # Structured-only extras (only populated when source == "jsonl")
    events: list[dict[str, Any]] = field(default_factory=list)
    phase_counts: dict[str, int] = field(default_factory=dict)

    @property
    def has_data(self) -> bool:
        return self.matched_lines > 0 or self.log_path is not None

    @property
    def status(self) -> str:
        if self.errors:
            return "fail"
        if self.matched_lines > 0:
            return "ok"
        return "no-data"


# ---- File discovery ---------------------------------------------------

def latest_log_for_module(module: str) -> Path | None:
    """Most recent .log file matching this module (mtime)."""
    candidates: list[Path] = []
    for d in (paths.episodios_dir(), paths.output_dir(), paths.repo_root()):
        if d.exists():
            for p in d.glob("*.log"):
                if p.is_file() and state_mod._has_module(p.name, module):
                    candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def latest_jsonl_for_module(module: str) -> Path | None:
    """Most recent *_events.jsonl matching this module (mtime)."""
    candidates: list[Path] = []
    d = paths.episodios_dir()
    if d.exists():
        for p in d.glob("*_events.jsonl"):
            if p.is_file() and state_mod._has_module(p.name, module):
                candidates.append(p)
    # Also accept events files in the repo root (uncommon but harmless)
    root = paths.repo_root()
    if root.exists():
        for p in root.glob("*_events.jsonl"):
            if p.is_file() and state_mod._has_module(p.name, module):
                candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---- JSONL parser -----------------------------------------------------

def _parse_jsonl(jsonl_path: Path, module: str, category: str) -> CategorySummary:
    summary = CategorySummary(
        module=module,
        category=category,
        source="jsonl",
        log_path=jsonl_path,
        log_mtime=datetime.fromtimestamp(jsonl_path.stat().st_mtime),
    )
    try:
        raw = jsonl_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return summary

    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not events:
        return summary

    # Filter by category (system events are always relevant)
    if category == "log":
        relevant = events
    else:
        relevant = [e for e in events if e.get("category") in (category, "system")]

    summary.matched_lines = len(relevant)
    summary.events = relevant

    # Timestamps span the full run
    ts_all = [e.get("ts") for e in events if e.get("ts")]
    if ts_all:
        summary.first_ts = ts_all[0]
        summary.last_ts = ts_all[-1]

    # Phase counts (handy for rendering metrics like "synth_block: 78")
    for e in relevant:
        ph = str(e.get("phase", ""))
        if ph:
            summary.phase_counts[ph] = summary.phase_counts.get(ph, 0) + 1

    # Errors / warnings / ok-signals
    for e in relevant:
        level = e.get("level", "info")
        rendered = _format_event(e)
        if level == "error":
            summary.errors.append(rendered)
        elif level == "warn":
            summary.warnings.append(rendered)
        elif e.get("phase") == "end" and e.get("status") == "ok":
            summary.ok_signals.append(rendered)

    # Sample: first 2 + last 4 relevant events
    sample_events = relevant[:2] + relevant[-4:]
    seen: set[str] = set()
    for e in sample_events:
        s = _format_event(e)
        if s not in seen:
            seen.add(s)
            summary.sample.append(s)

    # Caps for UI safety
    summary.errors = [s[:400] for s in summary.errors[:30]]
    summary.warnings = [s[:400] for s in summary.warnings[:30]]
    summary.ok_signals = summary.ok_signals[:10]
    summary.sample = [s[:400] for s in summary.sample[:8]]
    return summary


def _format_event(e: dict[str, Any]) -> str:
    """Render an event dict as a single human-readable line."""
    ts = e.get("ts", "—")
    level = e.get("level", "info")
    phase = e.get("phase", "?")
    extras = {
        k: v for k, v in e.items()
        if k not in ("ts", "level", "phase", "category", "episode", "module", "script", "pid")
    }
    if extras:
        # short k=v pairs
        kv = " ".join(f"{k}={v}" for k, v in list(extras.items())[:6])
        return f"[{ts}] {level.upper()} {phase} · {kv}"
    return f"[{ts}] {level.upper()} {phase}"


# ---- Text fallback parser --------------------------------------------

def _parse_text(log_path: Path, module: str, category: str) -> CategorySummary:
    summary = CategorySummary(
        module=module,
        category=category,
        source="text",
        log_path=log_path,
        log_mtime=datetime.fromtimestamp(log_path.stat().st_mtime),
    )
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return summary

    keywords = _KEYWORDS.get(category, ())
    lines = text.splitlines()
    relevant = (
        [ln for ln in lines if any(kw.lower() in ln.lower() for kw in keywords)]
        if keywords else lines
    )
    summary.matched_lines = len(relevant)

    for ln in relevant:
        if _ERROR_LINE.search(ln):
            summary.errors.append(ln.strip())
        elif _WARN_LINE.search(ln):
            summary.warnings.append(ln.strip())
        elif _OK_LINE.search(ln):
            summary.ok_signals.append(ln.strip())

    timestamps = _TS.findall(text)
    if timestamps:
        summary.first_ts = timestamps[0]
        summary.last_ts = timestamps[-1]

    sample: list[str] = []
    for ln in relevant[:3]:
        sample.append(ln.strip())
    for ln in relevant[-3:]:
        s = ln.strip()
        if s and s not in sample:
            sample.append(s)
    summary.sample = [s[:300] for s in sample]
    summary.errors = [e[:300] for e in summary.errors[:20]]
    summary.warnings = [w[:300] for w in summary.warnings[:20]]
    summary.ok_signals = summary.ok_signals[:10]
    return summary


# ---- Public entry point ----------------------------------------------

def parse(module: str, category: str, log_path: Path | None = None) -> CategorySummary:
    """Resolve the best source available and produce a CategorySummary.

    Priority: JSONL (richer) > text log (heuristic regex). If `log_path` is
    given, it's used directly as a text log (escape hatch).
    """
    if log_path is not None:
        if log_path.suffix == ".jsonl":
            return _parse_jsonl(log_path, module, category)
        return _parse_text(log_path, module, category)

    jsonl = latest_jsonl_for_module(module)
    if jsonl is not None:
        return _parse_jsonl(jsonl, module, category)

    text_log = latest_log_for_module(module)
    if text_log is not None:
        return _parse_text(text_log, module, category)

    return CategorySummary(module=module, category=category, source="none")
