"""Modelos normalizados + interfaz común para conectores de analytics.

Los tres conectores (Spotify, iVoox, LinkedIn) implementan `AnalyticsConnector`
y devuelven datasets homogéneos. La página de Rendimiento los consume sin
saber el origen.

Cacheo en disco bajo `logs/analytics/<source>.json`, TTL configurable por
conector (Spotify 1h, iVoox 6h, LinkedIn 1h). No persistimos credenciales.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

# --- Modelos normalizados --------------------------------------------------


@dataclass
class EpisodeMetric:
    """Métricas de un episodio de podcast (Spotify / iVoox)."""
    source: str                       # "spotify" | "ivoox"
    episode_id: str
    title: str
    publish_date: date | None = None
    streams: int = 0                  # reproducciones / escuchas
    listeners: int = 0                # oyentes únicos (si la fuente lo expone)
    completion_rate: float | None = None   # 0..1
    avg_listen_seconds: int | None = None
    duration_seconds: int | None = None
    url: str | None = None


@dataclass
class ShowMetric:
    """Métricas agregadas del podcast/show en una fecha o ventana."""
    source: str
    show_id: str
    as_of: date
    followers: int = 0
    new_followers: int = 0
    total_streams_window: int = 0     # streams en la ventana [start, end]
    window_days: int = 30
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PostMetric:
    """Métricas de una publicación en una red social (LinkedIn)."""
    source: str                       # "linkedin"
    post_id: str
    author_urn: str
    published_at: datetime | None = None
    impressions: int = 0
    unique_impressions: int = 0
    clicks: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: float | None = None
    url: str | None = None
    text_preview: str = ""


# --- Excepciones -----------------------------------------------------------


class Unavailable(RuntimeError):
    """El conector no puede operar (faltan credenciales, deps o conexión)."""


# --- Interfaz común --------------------------------------------------------


class AnalyticsConnector:
    """Base class. Subclases implementan `fetch_*`."""

    source: str = ""
    label: str = ""
    icon: str = "📊"
    cache_ttl_seconds: int = 3600

    # ---- estado / credenciales --------------------------------------------

    def is_configured(self) -> bool:
        """True si hay credenciales/configuración suficiente."""
        return False

    def missing_config(self) -> list[str]:
        """Lista de variables `.env` o campos faltantes."""
        return []

    def status_detail(self) -> str:
        if self.is_configured():
            return "credenciales presentes"
        missing = self.missing_config()
        return f"faltan: {', '.join(missing)}" if missing else "no configurado"

    # ---- fetch (a sobreescribir) ------------------------------------------

    def fetch_show(self, window_days: int = 30) -> ShowMetric | None:  # pragma: no cover - default
        return None

    def fetch_episodes(self, window_days: int = 30) -> list[EpisodeMetric]:  # pragma: no cover
        return []

    def fetch_posts(self, window_days: int = 30) -> list[PostMetric]:  # pragma: no cover
        return []

    # ---- caché disco ------------------------------------------------------

    def _cache_path(self) -> Path:
        from cockpit.core import paths
        d = paths.repo_root() / "logs" / "analytics"
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{self.source}.json"

    def load_cache(self) -> dict[str, Any] | None:
        path = self._cache_path()
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - data.get("ts", 0) > self.cache_ttl_seconds:
            return None
        return data.get("payload")

    def save_cache(self, payload: dict[str, Any]) -> None:
        path = self._cache_path()
        path.write_text(
            json.dumps({"ts": time.time(), "payload": payload}, ensure_ascii=False, indent=2,
                       default=_json_default),
            encoding="utf-8",
        )


# --- helpers ---------------------------------------------------------------


def _json_default(o: Any) -> Any:
    if isinstance(o, datetime | date):
        return o.isoformat()
    if hasattr(o, "__dict__"):
        return asdict(o) if hasattr(o, "__dataclass_fields__") else o.__dict__
    raise TypeError(f"no serializable: {type(o).__name__}")


def merged_env() -> dict[str, str]:
    """Combina .env del repo + os.environ. os.environ gana."""
    from cockpit.core import paths
    env: dict[str, str] = {}
    env_path = paths.env_file() if hasattr(paths, "env_file") else paths.repo_root() / ".env"
    if env_path.exists():
        try:
            from dotenv import dotenv_values
            env.update({k: v for k, v in dotenv_values(env_path).items() if v})
        except ImportError:
            pass
    env.update({k: v for k, v in os.environ.items() if v})
    return env
