"""Planner loader, state mutator, and alert calculator.

Loads `planner/tareas.json` (immutable derived from source MD) and
`planner/_state.json` (mutable status per task). Merges them into `Task`
dataclasses for the UI to consume.

State mutations (`set_status`, `set_notes`) write back to `_state.json`
atomically (write to temp + os.replace) to avoid corruption on crash.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from . import paths


VALID_STATUSES = ("pending", "in_progress", "done", "blocked")


def _planner_dir() -> Path:
    """Locate the planner data directory.

    Priority: env PLANNER_DIR > <repo containing cockpit/>/planner > REPO_ROOT/planner.
    """
    env = os.environ.get("PLANNER_DIR")
    if env:
        return Path(env)
    # Repo that ships the cockpit package (parent of `cockpit/`)
    pkg_repo = Path(__file__).resolve().parents[2]
    candidate = pkg_repo / "planner"
    if (candidate / "tareas.json").exists():
        return candidate
    # Fallback: REPO_ROOT (useful once planner/ is merged into master)
    return paths.repo_root() / "planner"


def _tareas_path() -> Path:
    return _planner_dir() / "tareas.json"


def _state_path() -> Path:
    return _planner_dir() / "_state.json"


# ---- Dataclass --------------------------------------------------------

@dataclass
class Task:
    id: str
    title: str
    owner: str
    block: str
    subsection: str
    lista_date: str | None       # ISO yyyy-mm-dd or None
    lista_time: str | None       # "HH:MM" or None
    lista_raw: str
    sale_date: str | None
    sale_time: str | None
    sale_raw: str
    deps: list[str] = field(default_factory=list)
    critical: bool = False
    is_check: bool = False
    recurring: bool = False
    # From state file
    status: str = "pending"
    completed_at: str | None = None
    notes: str = ""

    @property
    def lista_dt(self) -> datetime | None:
        return _combine_dt(self.lista_date, self.lista_time)

    @property
    def sale_dt(self) -> datetime | None:
        return _combine_dt(self.sale_date, self.sale_time)

    @property
    def is_done(self) -> bool:
        return self.status == "done"


def _combine_dt(d: str | None, t: str | None) -> datetime | None:
    if not d:
        return None
    if t:
        try:
            return datetime.fromisoformat(f"{d}T{t}:00")
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(f"{d}T23:59:59")
    except ValueError:
        return None


# ---- IO ---------------------------------------------------------------

def load_state() -> dict[str, dict]:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, dict]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: temp file + os.replace
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False,
        dir=path.parent, prefix="._state.", suffix=".tmp"
    ) as tmp:
        json.dump(state, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, path)


def load_tasks() -> list[Task]:
    tpath = _tareas_path()
    if not tpath.exists():
        return []
    raw = json.loads(tpath.read_text(encoding="utf-8"))
    state = load_state()
    tasks: list[Task] = []
    for entry in raw.get("tasks", []):
        s = state.get(entry["id"], {})
        tasks.append(Task(
            id=entry["id"],
            title=entry.get("title", ""),
            owner=entry.get("owner", ""),
            block=entry.get("block", ""),
            subsection=entry.get("subsection", ""),
            lista_date=entry.get("lista_date"),
            lista_time=entry.get("lista_time"),
            lista_raw=entry.get("lista_raw", ""),
            sale_date=entry.get("sale_date"),
            sale_time=entry.get("sale_time"),
            sale_raw=entry.get("sale_raw", ""),
            deps=list(entry.get("deps", [])),
            critical=bool(entry.get("critical", False)),
            is_check=bool(entry.get("is_check", False)),
            recurring=bool(entry.get("recurring", False)),
            status=s.get("status", "pending"),
            completed_at=s.get("completed_at"),
            notes=s.get("notes", ""),
        ))
    return tasks


# ---- Mutations --------------------------------------------------------

def set_status(task_id: str, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}")
    state = load_state()
    entry = state.get(task_id, {})
    entry["status"] = status
    if status == "done":
        entry["completed_at"] = datetime.now().isoformat(timespec="seconds")
    else:
        entry.pop("completed_at", None)
    state[task_id] = entry
    save_state(state)


def set_notes(task_id: str, notes: str) -> None:
    state = load_state()
    entry = state.get(task_id, {})
    entry["notes"] = notes
    state[task_id] = entry
    save_state(state)


# ---- Queries / alerts -------------------------------------------------

def overdue(tasks: list[Task], today: date | None = None) -> list[Task]:
    today = today or date.today()
    today_iso = today.isoformat()
    return [
        t for t in tasks
        if not t.recurring and not t.is_done
        and t.lista_date and t.lista_date < today_iso
    ]


def due_today(tasks: list[Task], today: date | None = None) -> list[Task]:
    today = today or date.today()
    today_iso = today.isoformat()
    return [
        t for t in tasks
        if not t.recurring and not t.is_done
        and t.lista_date == today_iso
    ]


def upcoming(tasks: list[Task], days: int = 7,
             today: date | None = None) -> list[Task]:
    today = today or date.today()
    horizon = (today + timedelta(days=days)).isoformat()
    today_iso = today.isoformat()
    return [
        t for t in tasks
        if not t.recurring and not t.is_done
        and t.lista_date and today_iso < t.lista_date <= horizon
    ]


def upcoming_critical(tasks: list[Task], days: int = 14,
                      today: date | None = None) -> list[Task]:
    today = today or date.today()
    horizon = (today + timedelta(days=days)).isoformat()
    today_iso = today.isoformat()
    return [
        t for t in tasks
        if t.critical and not t.is_done
        and t.lista_date and today_iso <= t.lista_date <= horizon
    ]


def publishing_today(tasks: list[Task], today: date | None = None) -> list[Task]:
    """Tasks scheduled to be PUBLISHED (SALE) today."""
    today = today or date.today()
    today_iso = today.isoformat()
    return [
        t for t in tasks
        if t.sale_date == today_iso and not t.is_done
    ]


def by_status(tasks: list[Task]) -> dict[str, list[Task]]:
    out: dict[str, list[Task]] = {s: [] for s in VALID_STATUSES}
    for t in tasks:
        out.setdefault(t.status, []).append(t)
    return out


def progress(tasks: list[Task]) -> tuple[int, int, float]:
    total = len(tasks)
    done = sum(1 for t in tasks if t.is_done)
    pct = (done / total * 100) if total else 0.0
    return done, total, pct


@dataclass
class AlertSummary:
    overdue: int = 0
    due_today: int = 0
    publishing_today: int = 0
    upcoming_critical: int = 0
    total: int = 0
    done: int = 0


def alert_summary(tasks: list[Task], today: date | None = None) -> AlertSummary:
    return AlertSummary(
        overdue=len(overdue(tasks, today)),
        due_today=len(due_today(tasks, today)),
        publishing_today=len(publishing_today(tasks, today)),
        upcoming_critical=len(upcoming_critical(tasks, today=today)),
        total=len(tasks),
        done=sum(1 for t in tasks if t.is_done),
    )
