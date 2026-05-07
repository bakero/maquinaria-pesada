"""Parse episodios/*.log into a per-category validation summary.

The log format is whatever generar_episodio_v2 / validar_episodio decide to write.
We don't control it, so the parser is heuristic and tolerant.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import paths
from . import state as state_mod

# ---- Patterns ---------------------------------------------------------

_TS = re.compile(r"\b(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\b")
_ERROR_LINE = re.compile(r"\b(ERROR|❌|FAIL(?:ED)?|TRACEBACK)\b", re.IGNORECASE)
_WARN_LINE = re.compile(r"\b(WARNING|WARN|⚠)\b", re.IGNORECASE)
_OK_LINE = re.compile(r"(✅|\bOK\b|\bPASS(?:ED)?\b|\bSUCCESS\b)", re.IGNORECASE)

# Per-category keywords used to filter relevant lines.
_KEYWORDS = {
    "pdf": ("pdf", "extract", "pdfplumber"),
    "guion": ("guion", "script", "validate_script", "bloque", "speaker", "iago", "maria"),
    "audio": ("audio", "mp3", "elevenlabs", "synthesi", "ffmpeg", "credit", "duraci", "block"),
    "video": ("video", "mp4", "luma", "subtitle", "srt", "compose", "render"),
    "log": (),  # whole file
}


@dataclass
class CategorySummary:
    module: str
    category: str
    log_path: Path | None
    log_mtime: datetime | None
    matched_lines: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ok_signals: list[str] = field(default_factory=list)
    first_ts: str | None = None
    last_ts: str | None = None
    sample: list[str] = field(default_factory=list)  # up to N representative lines

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


def latest_log_for_module(module: str) -> Path | None:
    """Return the most recent .log file for the module (mtime), or None."""
    candidates: list[Path] = []
    for d in (paths.episodios_dir(), paths.output_dir(), paths.repo_root()):
        if d.exists():
            for p in d.glob("*.log"):
                if p.is_file() and state_mod._has_module(p.name, module):
                    candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse(module: str, category: str, log_path: Path | None = None) -> CategorySummary:
    """Build a summary for a (module, category) pair from the latest log.

    If log_path is given, use it; otherwise resolve via latest_log_for_module.
    """
    if log_path is None:
        log_path = latest_log_for_module(module)
    summary = CategorySummary(module=module, category=category, log_path=log_path,
                              log_mtime=None)
    if log_path is None or not log_path.exists():
        return summary

    summary.log_mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return summary

    keywords = _KEYWORDS.get(category, ())
    lines = text.splitlines()

    # Filter lines relevant to category (or all, if log category)
    if keywords:
        relevant = [
            ln for ln in lines
            if any(kw.lower() in ln.lower() for kw in keywords)
        ]
    else:
        relevant = lines

    summary.matched_lines = len(relevant)

    for ln in relevant:
        if _ERROR_LINE.search(ln):
            summary.errors.append(ln.strip())
        elif _WARN_LINE.search(ln):
            summary.warnings.append(ln.strip())
        elif _OK_LINE.search(ln):
            summary.ok_signals.append(ln.strip())

    # Timestamps from the FULL file (not just category-filtered) so we know
    # when the run started/ended even if no keyword landed near them.
    timestamps = _TS.findall(text)
    if timestamps:
        summary.first_ts = timestamps[0]
        summary.last_ts = timestamps[-1]

    # Sample: first 3 + last 3 relevant lines (deduped)
    sample: list[str] = []
    for ln in relevant[:3]:
        sample.append(ln.strip())
    for ln in relevant[-3:]:
        s = ln.strip()
        if s and s not in sample:
            sample.append(s)
    # Cap line length for display
    summary.sample = [s[:300] for s in sample]
    summary.errors = [e[:300] for e in summary.errors[:20]]
    summary.warnings = [w[:300] for w in summary.warnings[:20]]
    summary.ok_signals = summary.ok_signals[:10]

    return summary
