"""Structured event logger for the MaquinarIA Pesada pipeline.

Generators (generar_guion.py, generar_episodio_v2.py, validar_episodio.py, etc.)
import this and emit JSONL events. The cockpit reads those files; the pipeline
itself never imports the cockpit.

Format: one JSON object per line. File path: `episodios/{episode}_events.jsonl`.

Required fields auto-added: ts, episode, module, script, pid, phase, level, category.
Free-form fields go via kwargs.

Quick start
-----------

    from runlog import RunLogger

    with RunLogger(episode="M3_E_ML_Clasico", module="M3", script="generar_episodio_v2.py") as log:
        log.event("extract_pdf", category="pdf", path="PDFs/M3_T1.pdf", pages=42)
        log.event("synth_block", category="audio", block=12, speaker="IAGO", ms=312, credits=1024)
        log.warn("retry", category="audio", block=15, attempt=2, reason="503 Service Unavailable")
        try:
            ...
        except Exception as e:
            log.error("synth_block", category="audio", block=15, exc=str(e))
            raise

Design notes
------------

- Append-only. Each event is flushed to disk so the cockpit can tail in real time.
- Logging errors never crash the generator. Failures are silently swallowed
  (still printed to stderr for debugging).
- No dependencies. Pure stdlib. Works on Python 3.9+.
- Thread-safe enough for a single-threaded pipeline (don't share an instance
  across threads without locking).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


VALID_LEVELS = ("info", "warn", "error")
VALID_CATEGORIES = ("pdf", "guion", "audio", "video", "log", "system")


def _events_dir() -> Path:
    """Resolve where event files live.

    Priority: env EVENTS_DIR > env REPO_ROOT/episodios > cwd/episodios.
    """
    custom = os.environ.get("EVENTS_DIR")
    if custom:
        return Path(custom)
    repo_root = os.environ.get("REPO_ROOT")
    if repo_root:
        return Path(repo_root) / "episodios"
    return Path.cwd() / "episodios"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class RunLogger:
    """Append-only JSONL event logger for a single episode/run.

    Usable as a context manager (recommended) or directly. The context manager
    emits a `start` event on enter and an `end` event on exit (with status=ok or
    status=error if an exception escaped).

    Multiple processes can write to the same file; entries are interleaved per
    line, which is fine for JSONL.
    """

    def __init__(
        self,
        episode: str,
        module: str,
        script: str = "",
        events_dir: Optional[Path] = None,
    ):
        self.episode = episode
        self.module = module
        self.script = script or (Path(sys.argv[0]).name if sys.argv else "")
        self.pid = os.getpid()
        self.start_time = time.time()
        self._dir = Path(events_dir) if events_dir else _events_dir()
        self._path = self._dir / f"{episode}_events.jsonl"
        self._file = None
        self._lock = threading.Lock()

    @property
    def path(self) -> Path:
        return self._path

    # ---- Context manager -------------------------------------------------

    def __enter__(self) -> "RunLogger":
        self.event("start", category="system", elapsed_s=0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                self.error(
                    "end",
                    category="system",
                    exc=str(exc_val)[:1000],
                    exc_type=exc_type.__name__,
                    traceback=traceback.format_exc()[:2000],
                    elapsed_s=round(time.time() - self.start_time, 2),
                )
            else:
                self.event(
                    "end",
                    category="system",
                    status="ok",
                    elapsed_s=round(time.time() - self.start_time, 2),
                )
        finally:
            self.close()

    # ---- Public API ------------------------------------------------------

    def event(
        self,
        phase: str,
        level: str = "info",
        category: str = "log",
        **fields: Any,
    ) -> None:
        """Emit a structured event."""
        if level not in VALID_LEVELS:
            level = "info"
        if category not in VALID_CATEGORIES:
            category = "log"
        record = {
            "ts": _now_iso(),
            "episode": self.episode,
            "module": self.module,
            "script": self.script,
            "pid": self.pid,
            "phase": phase,
            "level": level,
            "category": category,
        }
        # Guard against accidentally clobbering required fields with kwargs.
        for k, v in fields.items():
            if k not in record:
                record[k] = v
        self._write(record)

    def warn(self, phase: str, category: str = "log", **fields: Any) -> None:
        self.event(phase, level="warn", category=category, **fields)

    def error(self, phase: str, category: str = "log", **fields: Any) -> None:
        self.event(phase, level="error", category=category, **fields)

    def close(self) -> None:
        with self._lock:
            if self._file is not None:
                try:
                    self._file.close()
                except OSError:
                    pass
                self._file = None

    # ---- Internals -------------------------------------------------------

    def _ensure_open(self) -> None:
        if self._file is None:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._file = self._path.open("a", encoding="utf-8")

    def _write(self, record: dict) -> None:
        try:
            with self._lock:
                self._ensure_open()
                line = json.dumps(record, ensure_ascii=False, default=str)
                self._file.write(line + "\n")
                self._file.flush()
        except Exception as exc:
            # Never let logging failures break the pipeline.
            try:
                sys.stderr.write(f"[runlog] write failed: {exc!r}\n")
            except Exception:
                pass


# ---- Convenience helpers ---------------------------------------------

_GLOBAL: Optional[RunLogger] = None


def init(episode: str, module: str, script: str = "") -> RunLogger:
    """Create + register a global logger (for scripts that don't want a context manager).

    Call once near the top of the script; then use `event()`, `warn()`, `error()`.
    The caller must ensure `close_global()` runs at script end (or atexit).
    """
    global _GLOBAL
    _GLOBAL = RunLogger(episode=episode, module=module, script=script)
    _GLOBAL.event("start", category="system", elapsed_s=0)
    return _GLOBAL


def event(phase: str, **fields: Any) -> None:
    if _GLOBAL is not None:
        _GLOBAL.event(phase, **fields)


def warn(phase: str, **fields: Any) -> None:
    if _GLOBAL is not None:
        _GLOBAL.warn(phase, **fields)


def error(phase: str, **fields: Any) -> None:
    if _GLOBAL is not None:
        _GLOBAL.error(phase, **fields)


def close_global() -> None:
    global _GLOBAL
    if _GLOBAL is not None:
        _GLOBAL.event("end", category="system", status="ok",
                      elapsed_s=round(time.time() - _GLOBAL.start_time, 2))
        _GLOBAL.close()
        _GLOBAL = None
