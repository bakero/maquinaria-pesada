"""Live process monitor for the cockpit sidebar.

Detects Python processes running pipeline scripts, the log they're writing,
and recent output files. Read-only: never launches anything.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import paths

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


# Map of script filename -> human label.
PIPELINE_SCRIPTS: dict[str, str] = {
    "generar_guion.py":            "📝 Generación de guion",
    "generar_episodio_v2.py":      "🎧 Síntesis de audio",
    "generar_episodio.py":         "🎧 Síntesis de audio (legacy)",
    "producir_episodio.py":        "🚀 Pipeline guion+audio",
    "validar_episodio.py":         "✅ Validación",
    "lanzar_produccion.py":        "🔁 Batch runner",
    "estado_proyecto.py":          "📊 Estado proyecto",
    "normalizar_guiones.py":       "🧹 Normalización guiones",
    "dual_debate.py":              "🤝 Debate dual",
    "dual_debate_maquinaria.py":   "🤝 Debate dual (maq)",
    "podcast_spec.py":             "📐 Spec validator",
    "run_pipeline.py":             "🎬 Pipeline videopodcast",
}

# Mtime windows.
_LOG_RECENT_S = 300          # log considered "active" if modified in last 5 min
_OUTPUT_RECENT_S = 600       # output file "recent" if modified in last 10 min


@dataclass
class RunningProcess:
    pid: int
    script: str          # filename detected in cmdline
    label: str
    cmdline: list[str]
    started: datetime
    elapsed_s: float
    memory_mb: float
    cwd: str
    active_log: Path | None = None
    log_tail: list[str] = field(default_factory=list)
    recent_outputs: list[Path] = field(default_factory=list)


def _match_script(cmdline: list[str]) -> str | None:
    for arg in cmdline:
        s = str(arg)
        for known in PIPELINE_SCRIPTS:
            # Accept full path or bare name; case-insensitive on Windows is fine because
            # filenames in PIPELINE_SCRIPTS already match exact case used by the repo.
            if s.endswith(known) or s.endswith("/" + known) or s.endswith("\\" + known):
                return known
            if known in s:
                return known
    return None


def find_active_log(cwd: Path | None = None) -> Path | None:
    """Most recently modified .log under episodios/, output/, repo root or cwd."""
    cutoff = time.time() - _LOG_RECENT_S
    candidates: list[Path] = []
    roots = [paths.episodios_dir(), paths.output_dir(), paths.repo_root()]
    if cwd is not None and cwd.exists() and cwd not in roots:
        roots.append(cwd)
    for d in roots:
        if not d.exists():
            continue
        try:
            for p in d.glob("*.log"):
                if p.is_file() and p.stat().st_mtime > cutoff:
                    candidates.append(p)
        except OSError:
            continue
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def tail_lines(path: Path, n: int = 5) -> list[str]:
    if path is None or not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return [ln.strip() for ln in text.splitlines()[-n:] if ln.strip()]
    except OSError:
        return []


def recent_outputs(max_age_s: int = _OUTPUT_RECENT_S, limit: int = 10) -> list[Path]:
    """Recently-created files under episodios/, output/, Videos/."""
    cutoff = time.time() - max_age_s
    items: list[Path] = []
    for d in (paths.episodios_dir(), paths.output_dir(), paths.videos_dir()):
        if not d.exists():
            continue
        try:
            for p in d.rglob("*"):
                if p.is_file():
                    try:
                        if p.stat().st_mtime > cutoff:
                            items.append(p)
                    except OSError:
                        continue
        except OSError:
            continue
    items.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return items[:limit]


def scan_running() -> list[RunningProcess]:
    """List running Python processes that match a known pipeline script."""
    if not _HAS_PSUTIL:
        return []

    out: list[RunningProcess] = []
    repo_root_resolved = paths.repo_root().resolve()

    for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time", "cwd"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            if not cmdline:
                continue
            script = _match_script(cmdline)
            if script is None:
                continue
            cwd_str = proc.info.get("cwd") or ""
            cwd_path = Path(cwd_str) if cwd_str else None

            # Limit to processes inside the repo (avoid catching python servers from elsewhere)
            try:
                if cwd_path and not str(cwd_path.resolve()).startswith(str(repo_root_resolved)):
                    # Allow if any cmdline arg is inside the repo
                    cwd_inside = False
                    for arg in cmdline:
                        try:
                            if str(Path(arg).resolve()).startswith(str(repo_root_resolved)):
                                cwd_inside = True
                                break
                        except (OSError, ValueError):
                            continue
                    if not cwd_inside:
                        continue
            except OSError:
                pass

            create_time = proc.info["create_time"]
            started = datetime.fromtimestamp(create_time)
            elapsed = time.time() - create_time
            try:
                memory_mb = proc.memory_info().rss / (1024 * 1024)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                memory_mb = 0.0

            active_log = find_active_log(cwd_path)
            tail = tail_lines(active_log, n=5) if active_log else []
            outputs = recent_outputs()

            out.append(
                RunningProcess(
                    pid=proc.info["pid"],
                    script=script,
                    label=PIPELINE_SCRIPTS[script],
                    cmdline=[str(a) for a in cmdline],
                    started=started,
                    elapsed_s=elapsed,
                    memory_mb=memory_mb,
                    cwd=cwd_str,
                    active_log=active_log,
                    log_tail=tail,
                    recent_outputs=outputs,
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    out.sort(key=lambda r: r.started)
    return out


def format_elapsed(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60:02d}s"
    return f"{s // 3600}h {(s % 3600) // 60:02d}m"


def format_age(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"
