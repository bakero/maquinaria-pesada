"""Form values -> CLI command string ready to paste into Codex."""
from __future__ import annotations

import datetime as _dt
import shlex
from typing import Any, Iterable

from . import paths


def _quote(value: Any) -> str:
    s = str(value)
    # shlex.quote uses POSIX rules, which Codex/bash on Windows handles fine.
    return shlex.quote(s)


def build(
    *,
    script: str,
    flags: Iterable[tuple[str, Any]],
    cwd: str | None = None,
    header: str | None = None,
) -> str:
    parts: list[str] = []
    if header:
        parts.append(f"# {header}")
    parts.append(f"# Generated {_dt.date.today().isoformat()}")
    if cwd:
        parts.append(f'cd {_quote(cwd)}')
    cmd = ["python", script]
    for flag, value in flags:
        if value is None or value == "" or value is False:
            continue
        if value is True:
            cmd.append(flag)
        else:
            cmd.extend([flag, _quote(value)])
    parts.append(" ".join(cmd))
    return "\n".join(parts)


def default_cwd() -> str:
    return str(paths.repo_root())
