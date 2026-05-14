"""Estado persistido de generación por episodio.

Cada episodio escribe un JSON en ``logs/episode_state/{ep_id}.json`` con el
progreso de la última ejecución del pipeline de audio: cuántos bloques se han
generado, cuántos han fallado, estado global y timestamps. Permite al cockpit
mostrar progreso parcial sin tener que inferirlo del filesystem, y deja un
rastro de la última corrida aunque el proceso muera a mitad.

El estado es deliberadamente plano y tolerante a fallos: si el JSON está
corrupto o ausente, ``load`` devuelve ``None`` en vez de reventar.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path

# Raíz del repo: derivada de este archivo (top-level), con override REPO_ROOT
# para tests y checkouts alternativos — misma convención que cockpit/core/paths.py.
DEFAULT_REPO_ROOT = Path(__file__).resolve().parent


def repo_root() -> Path:
    return Path(os.environ.get("REPO_ROOT", DEFAULT_REPO_ROOT)).resolve()


def state_dir() -> Path:
    return repo_root() / "logs" / "episode_state"


def state_path(ep_id: str) -> Path:
    return state_dir() / f"{ep_id}.json"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class EpisodeState:
    """Snapshot de la última ejecución del pipeline de audio de un episodio."""

    ep_id: str
    status: str = "pending"        # pending | running | ok | failed
    blocks_total: int = 0
    blocks_done: int = 0
    blocks_failed: int = 0
    duration_s: float | None = None
    started_at: str | None = None
    updated_at: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def load(ep_id: str) -> EpisodeState | None:
    """Devuelve el estado persistido del episodio, o None si no existe / está corrupto."""
    path = state_path(ep_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict) or "ep_id" not in data:
        return None
    known = {f.name for f in fields(EpisodeState)}
    return EpisodeState(**{k: v for k, v in data.items() if k in known})


def save(state: EpisodeState) -> Path:
    """Persiste el estado (refrescando updated_at) y devuelve la ruta del JSON."""
    state.updated_at = _now()
    path = state_path(state.ep_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def mark_running(ep_id: str, blocks_total: int) -> EpisodeState:
    """Marca el inicio de una corrida: status=running, started_at=ahora."""
    state = EpisodeState(
        ep_id=ep_id, status="running",
        blocks_total=blocks_total, started_at=_now(),
    )
    save(state)
    return state


def mark_finished(
    state: EpisodeState,
    *,
    blocks_done: int,
    blocks_failed: int,
    duration_s: float | None,
    ok: bool,
    error: str | None = None,
) -> EpisodeState:
    """Cierra la corrida: status=ok|failed con los contadores finales."""
    state.blocks_done = blocks_done
    state.blocks_failed = blocks_failed
    state.duration_s = duration_s
    state.status = "ok" if ok else "failed"
    state.error = error
    save(state)
    return state
