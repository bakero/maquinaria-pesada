"""Spotify analytics conector.

Dos backends:
- `spotifyconnector` (no oficial) para analytics privadas del dashboard
  de podcasters. Requiere cookies `sp_dc` + `sp_key` + `podcast_id`.
- `spotipy` (oficial) para metadatos públicos de show/episodes.

Doc: docs/integraciones/analytics.md sección Spotify.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .base import AnalyticsConnector, EpisodeMetric, ShowMetric, Unavailable, merged_env

# client_id estático del dashboard de podcasters (público, igual para todos)
SPOTIFY_PODCASTERS_CLIENT_ID = "05a1371ee5194c27860b3ff3ff3979d2"
SPOTIFY_PODCASTERS_BASE_URL = "https://generic.wg.spotify.com/podcasters/v0"


class SpotifyAnalytics(AnalyticsConnector):
    source = "spotify"
    label = "Spotify for Creators"
    icon = "🎧"
    cache_ttl_seconds = 3600

    ENV_KEYS = ("SPOTIFY_SP_DC", "SPOTIFY_SP_KEY", "SPOTIFY_PODCAST_ID")

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self._env = env if env is not None else merged_env()

    # ---- estado ----------------------------------------------------------

    def is_configured(self) -> bool:
        return all(self._env.get(k) for k in self.ENV_KEYS)

    def missing_config(self) -> list[str]:
        return [k for k in self.ENV_KEYS if not self._env.get(k)]

    # ---- cliente ---------------------------------------------------------

    def _client(self) -> Any:
        try:
            from spotifyconnector import SpotifyConnector
        except ImportError as e:
            raise Unavailable(
                "paquete 'spotifyconnector' no instalado. "
                "Ejecuta: pip install spotifyconnector"
            ) from e
        if not self.is_configured():
            raise Unavailable(f"faltan en .env: {', '.join(self.missing_config())}")
        return SpotifyConnector(
            base_url=SPOTIFY_PODCASTERS_BASE_URL,
            client_id=SPOTIFY_PODCASTERS_CLIENT_ID,
            podcast_id=self._env["SPOTIFY_PODCAST_ID"],
            sp_dc=self._env["SPOTIFY_SP_DC"],
            sp_key=self._env["SPOTIFY_SP_KEY"],
        )

    # ---- fetch -----------------------------------------------------------

    def fetch_show(self, window_days: int = 30) -> ShowMetric | None:
        client = self._client()
        end = date.today()
        start = end - timedelta(days=window_days)
        meta = client.metadata() or {}
        followers = client.followers(start=start, end=end) or {}
        streams = client.streams(start=start, end=end) or {}
        return ShowMetric(
            source=self.source,
            show_id=self._env["SPOTIFY_PODCAST_ID"],
            as_of=end,
            followers=int(_first_number(followers, ["total", "totalFollowers", "count"]) or 0),
            new_followers=int(_first_number(followers, ["new", "delta", "gained"]) or 0),
            total_streams_window=int(_first_number(streams, ["total", "totalStreams"]) or 0),
            window_days=window_days,
            extra={"name": meta.get("name", ""), "totalEpisodes": meta.get("totalEpisodes", 0)},
        )

    def fetch_episodes(self, window_days: int = 30) -> list[EpisodeMetric]:
        client = self._client()
        end = date.today()
        start = end - timedelta(days=window_days)
        out: list[EpisodeMetric] = []
        for ep in client.episodes(start=start, end=end, size=50) or []:
            ep_id = ep.get("id", "")
            perf = {}
            try:
                perf = client.performance(ep_id) or {}
            except Exception:
                perf = {}
            out.append(EpisodeMetric(
                source=self.source,
                episode_id=ep_id,
                title=ep.get("name", ""),
                publish_date=_parse_date(ep.get("releaseDate")),
                streams=int(perf.get("starts") or ep.get("starts") or 0),
                listeners=int(perf.get("listeners") or ep.get("listeners") or 0),
                completion_rate=_safe_float(perf.get("completionRate")),
                avg_listen_seconds=_safe_int(perf.get("averageListen")),
                duration_seconds=_safe_int(ep.get("duration")),
                url=ep.get("url"),
            ))
        return out


# --- helpers ---------------------------------------------------------------


def _first_number(d: dict[str, Any], keys: list[str]) -> float | None:
    for k in keys:
        v = d.get(k)
        if isinstance(v, int | float):
            return float(v)
        if isinstance(v, dict):
            for kk in ("value", "total", "count"):
                if isinstance(v.get(kk), int | float):
                    return float(v[kk])
    return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    s = str(value)
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s[: len(fmt) + 5], fmt).date()
        except ValueError:
            continue
    return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
