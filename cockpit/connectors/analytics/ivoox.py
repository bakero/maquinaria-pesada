"""iVoox analytics conector.

No hay API oficial. Vías soportadas:
- RSS público del podcast (canal soportado por ToS, vía recomendada).
- CSV exportado manualmente desde la Zona de Creadores (planes Essential+).

NO hace scraping de páginas internas ni descarga MP3 de terceros (contra ToS).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .base import AnalyticsConnector, EpisodeMetric, ShowMetric, Unavailable, merged_env

USER_AGENT = "MaquinarIaPesadaCockpit/1.0 (+contact: bkasero@gmail.com)"
HTTP_TIMEOUT = 20


@dataclass
class IvooxFeedInfo:
    title: str
    author: str
    description: str
    language: str
    image: str | None


class IvooxAnalytics(AnalyticsConnector):
    source = "ivoox"
    label = "iVoox (RSS público)"
    icon = "🟧"
    cache_ttl_seconds = 6 * 3600

    ENV_KEYS = ("IVOOX_RSS_URL",)

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self._env = env if env is not None else merged_env()

    # ---- estado ----------------------------------------------------------

    def is_configured(self) -> bool:
        return bool(self._env.get("IVOOX_RSS_URL"))

    def missing_config(self) -> list[str]:
        return [] if self.is_configured() else ["IVOOX_RSS_URL"]

    # ---- HTTP ------------------------------------------------------------

    def _fetch_rss(self, url: str) -> bytes:
        try:
            import requests
        except ImportError as e:
            raise Unavailable("paquete 'requests' no instalado") from e
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return r.content

    # ---- fetch -----------------------------------------------------------

    def fetch_feed_info(self, raw: bytes | None = None) -> IvooxFeedInfo:
        try:
            import feedparser
        except ImportError as e:
            raise Unavailable("paquete 'feedparser' no instalado") from e
        if raw is None:
            if not self.is_configured():
                raise Unavailable("IVOOX_RSS_URL no definido en .env")
            raw = self._fetch_rss(self._env["IVOOX_RSS_URL"])
        fp = feedparser.parse(raw)
        ch = fp.feed
        image = None
        img = ch.get("image")
        if isinstance(img, dict):
            image = img.get("href")
        return IvooxFeedInfo(
            title=ch.get("title", ""),
            author=ch.get("author") or ch.get("itunes_author", ""),
            description=ch.get("summary", ""),
            language=ch.get("language", "es"),
            image=image,
        )

    def fetch_episodes(self, window_days: int = 365, raw: bytes | None = None) -> list[EpisodeMetric]:
        try:
            import feedparser
        except ImportError as e:
            raise Unavailable("paquete 'feedparser' no instalado") from e
        if raw is None:
            if not self.is_configured():
                raise Unavailable("IVOOX_RSS_URL no definido en .env")
            raw = self._fetch_rss(self._env["IVOOX_RSS_URL"])
        fp = feedparser.parse(raw)
        cutoff = date.today() - timedelta(days=window_days)
        out: list[EpisodeMetric] = []
        for it in fp.entries:
            pub = _parse_pub(it.get("published"))
            if pub and pub < cutoff:
                continue
            out.append(EpisodeMetric(
                source=self.source,
                episode_id=str(it.get("id") or it.get("link") or it.get("title", "")),
                title=it.get("title", ""),
                publish_date=pub,
                streams=0,           # RSS no expone escuchas
                listeners=0,
                duration_seconds=_parse_duration(it.get("itunes_duration")),
                url=it.get("link"),
            ))
        return out

    def fetch_show(self, window_days: int = 30) -> ShowMetric | None:
        if not self.is_configured():
            return None
        info = self.fetch_feed_info()
        return ShowMetric(
            source=self.source,
            show_id=self._env["IVOOX_RSS_URL"],
            as_of=date.today(),
            window_days=window_days,
            extra={
                "title": info.title,
                "author": info.author,
                "language": info.language,
                "image": info.image or "",
            },
        )

    # ---- CSV manual ------------------------------------------------------

    @staticmethod
    def load_stats_csv(path: Path | str) -> Any:
        """Carga el CSV que iVoox Podcasters exporta desde la UI.

        Retorna un `pandas.DataFrame` con columnas normalizadas (lowercase,
        underscores) y `fecha` parseada como datetime si existe.
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise Unavailable("paquete 'pandas' no instalado") from e
        df = pd.read_csv(str(path), sep=";", encoding="utf-8-sig")
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
        return df


# --- helpers ---------------------------------------------------------------


def _parse_pub(value: Any) -> date | None:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(str(value))
        return dt.date() if dt else None
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _parse_duration(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip()
    if s.isdigit():
        return int(s)
    parts = s.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    return None


def parse_rss_bytes(raw: bytes) -> tuple[IvooxFeedInfo, list[EpisodeMetric]]:
    """Helper standalone para parsear RSS sin instanciar conector (útil en tests)."""
    conn = IvooxAnalytics(env={"IVOOX_RSS_URL": "test://fixture"})
    return conn.fetch_feed_info(raw=raw), conn.fetch_episodes(raw=raw, window_days=10_000)
