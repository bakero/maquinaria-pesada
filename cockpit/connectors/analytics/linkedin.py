"""LinkedIn analytics conector (Community Management API).

Auth: OAuth 2.0 3-legged. El usuario debe haber completado el flujo y obtenido
un `access_token` (60d) + opcionalmente `refresh_token` (365d). Guardamos
tokens en `logs/analytics/linkedin_tokens.json` (no commitear).

Endpoints usados (versión LinkedIn-Version: 202604):
- /rest/organizationalEntityShareStatistics (agregados de posts de página)
- /rest/organizationPageStatistics            (vistas/clicks de página)
- /rest/organizationalEntityFollowerStatistics (seguidores)
- /rest/posts (listado de posts del autor)

NO usamos `linkedin-api` (scraper que viola ToS).
"""
from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .base import AnalyticsConnector, PostMetric, Unavailable, merged_env

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_API_BASE = "https://api.linkedin.com/rest"
LINKEDIN_API_VERSION = "202604"
HTTP_TIMEOUT = 30


class LinkedInAnalytics(AnalyticsConnector):
    source = "linkedin"
    label = "LinkedIn"
    icon = "💼"
    cache_ttl_seconds = 3600

    ENV_KEYS = ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ORG_URN")

    def __init__(self, env: dict[str, str] | None = None) -> None:
        self._env = env if env is not None else merged_env()

    # ---- estado ----------------------------------------------------------

    def is_configured(self) -> bool:
        if not all(self._env.get(k) for k in self.ENV_KEYS):
            return False
        return self._load_tokens() is not None

    def missing_config(self) -> list[str]:
        missing = [k for k in self.ENV_KEYS if not self._env.get(k)]
        if self._load_tokens() is None:
            missing.append("oauth_tokens")
        return missing

    # ---- token store -----------------------------------------------------

    def _tokens_path(self) -> Path:
        from cockpit.core import paths
        d = paths.repo_root() / "logs" / "analytics"
        d.mkdir(parents=True, exist_ok=True)
        return d / "linkedin_tokens.json"

    def _load_tokens(self) -> dict[str, Any] | None:
        path = self._tokens_path()
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def save_tokens(self, payload: dict[str, Any]) -> None:
        payload = dict(payload)
        if "expires_in" in payload and "expires_at" not in payload:
            payload["expires_at"] = int(time.time()) + int(payload["expires_in"])
        self._tokens_path().write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---- OAuth -----------------------------------------------------------

    def authorization_url(self, redirect_uri: str, scopes: list[str], state: str) -> str:
        from urllib.parse import urlencode
        params = {
            "response_type": "code",
            "client_id": self._env.get("LINKEDIN_CLIENT_ID", ""),
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": " ".join(scopes),
        }
        return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        try:
            import requests
        except ImportError as e:
            raise Unavailable("paquete 'requests' no instalado") from e
        r = requests.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self._env.get("LINKEDIN_CLIENT_ID", ""),
                "client_secret": self._env.get("LINKEDIN_CLIENT_SECRET", ""),
            },
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        payload = r.json()
        self.save_tokens(payload)
        return payload

    def refresh_access_token(self) -> dict[str, Any]:
        tokens = self._load_tokens() or {}
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise Unavailable("no hay refresh_token guardado")
        try:
            import requests
        except ImportError as e:
            raise Unavailable("paquete 'requests' no instalado") from e
        r = requests.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._env.get("LINKEDIN_CLIENT_ID", ""),
                "client_secret": self._env.get("LINKEDIN_CLIENT_SECRET", ""),
            },
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        payload = r.json()
        # Preserva refresh_token si LinkedIn no lo devuelve (no rota).
        payload.setdefault("refresh_token", refresh_token)
        self.save_tokens(payload)
        return payload

    def _bearer(self) -> str:
        tokens = self._load_tokens()
        if not tokens or not tokens.get("access_token"):
            raise Unavailable("sin access_token. Completa el flujo OAuth desde la página de LinkedIn.")
        expires_at = tokens.get("expires_at", 0)
        # Margen 7 días → refrescar si tenemos refresh_token.
        if expires_at and expires_at - time.time() < 7 * 86400 and tokens.get("refresh_token"):
            try:
                tokens = self.refresh_access_token()
            except Exception:
                pass  # uso el access caducando, fallará con 401 y se gestiona arriba
        return tokens["access_token"]

    # ---- HTTP helpers ----------------------------------------------------

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            import requests
        except ImportError as e:
            raise Unavailable("paquete 'requests' no instalado") from e
        headers = {
            "Authorization": f"Bearer {self._bearer()}",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
        r = requests.get(
            f"{LINKEDIN_API_BASE}{path}", headers=headers, params=params, timeout=HTTP_TIMEOUT
        )
        r.raise_for_status()
        return r.json()

    # ---- fetch -----------------------------------------------------------

    def fetch_share_statistics(self) -> dict[str, Any]:
        """Lifetime share statistics de la página completa."""
        org_urn = self._env.get("LINKEDIN_ORG_URN", "")
        if not org_urn:
            raise Unavailable("LINKEDIN_ORG_URN no definido")
        data = self._get(
            "/organizationalEntityShareStatistics",
            params={"q": "organizationalEntity", "organizationalEntity": org_urn},
        )
        elements = data.get("elements", [])
        return elements[0].get("totalShareStatistics", {}) if elements else {}

    def fetch_page_statistics(self) -> dict[str, Any]:
        org_urn = self._env.get("LINKEDIN_ORG_URN", "")
        if not org_urn:
            raise Unavailable("LINKEDIN_ORG_URN no definido")
        data = self._get(
            "/organizationPageStatistics",
            params={"q": "organization", "organization": org_urn},
        )
        elements = data.get("elements", [])
        return elements[0] if elements else {}

    def fetch_follower_statistics(self) -> dict[str, Any]:
        org_urn = self._env.get("LINKEDIN_ORG_URN", "")
        if not org_urn:
            raise Unavailable("LINKEDIN_ORG_URN no definido")
        data = self._get(
            "/organizationalEntityFollowerStatistics",
            params={"q": "organizationalEntity", "organizationalEntity": org_urn},
        )
        elements = data.get("elements", [])
        return elements[0] if elements else {}

    def fetch_posts(self, window_days: int = 30) -> list[PostMetric]:
        org_urn = self._env.get("LINKEDIN_ORG_URN", "")
        if not org_urn:
            raise Unavailable("LINKEDIN_ORG_URN no definido")
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        # 1) lista de posts del autor
        posts_data = self._get(
            "/posts", params={"q": "author", "author": org_urn, "count": 50}
        )
        elements = posts_data.get("elements", [])
        if not elements:
            return []
        # 2) stats agregadas por post via finder ugcPosts[]
        post_ids = [e.get("id") for e in elements if e.get("id")]
        # LinkedIn permite hasta ~20 por llamada; troceamos en bloques de 20.
        stats_by_id: dict[str, dict[str, Any]] = {}
        for i in range(0, len(post_ids), 20):
            chunk = post_ids[i : i + 20]
            params = {"q": "organizationalEntity", "organizationalEntity": org_urn}
            for idx, pid in enumerate(chunk):
                params[f"ugcPosts[{idx}]"] = pid
            try:
                data = self._get("/organizationalEntityShareStatistics", params=params)
                for el in data.get("elements", []):
                    pid = el.get("share") or el.get("ugcPost")
                    if pid:
                        stats_by_id[str(pid)] = el.get("totalShareStatistics", {})
            except Exception:
                continue

        out: list[PostMetric] = []
        for e in elements:
            pid = e.get("id", "")
            published_ms = (e.get("publishedAt") or 0) // 1000
            published_at = (
                datetime.fromtimestamp(published_ms, tz=UTC) if published_ms else None
            )
            if published_at and published_at < cutoff:
                continue
            s = stats_by_id.get(str(pid), {})
            impressions = int(s.get("impressionCount", 0))
            engagement = float(s.get("engagement") or 0.0)
            out.append(PostMetric(
                source=self.source,
                post_id=str(pid),
                author_urn=org_urn,
                published_at=published_at,
                impressions=impressions,
                unique_impressions=int(s.get("uniqueImpressionsCount", 0)),
                clicks=int(s.get("clickCount", 0)),
                likes=int(s.get("likeCount", 0)),
                comments=int(s.get("commentCount", 0)),
                shares=int(s.get("shareCount", 0)),
                engagement_rate=engagement or None,
                url=f"https://www.linkedin.com/feed/update/{pid}/" if pid else None,
                text_preview=(e.get("commentary") or "")[:280],
            ))
        return out
