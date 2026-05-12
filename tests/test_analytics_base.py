"""Tests del módulo cockpit/connectors/analytics: base + 3 conectores.

Todos los tests son sin red. Mockean clientes / requests directamente.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cockpit.connectors.analytics import (  # noqa: E402
    AnalyticsConnector,
    EpisodeMetric,
    PostMetric,
    ShowMetric,
    Unavailable,
)
from cockpit.connectors.analytics.ivoox import IvooxAnalytics, parse_rss_bytes  # noqa: E402
from cockpit.connectors.analytics.linkedin import LinkedInAnalytics  # noqa: E402
from cockpit.connectors.analytics.spotify import SpotifyAnalytics  # noqa: E402

# ---- modelos --------------------------------------------------------------


def test_episode_metric_defaults():
    e = EpisodeMetric(source="spotify", episode_id="x", title="ep")
    assert e.streams == 0
    assert e.publish_date is None


def test_post_metric_defaults():
    p = PostMetric(source="linkedin", post_id="urn:li:share:1", author_urn="urn:li:org:1")
    assert p.likes == 0


def test_show_metric_extra():
    s = ShowMetric(source="ivoox", show_id="x", as_of=date(2026, 1, 1))
    s.extra["k"] = "v"
    assert s.extra["k"] == "v"


# ---- base: caché ----------------------------------------------------------


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))

    class C(AnalyticsConnector):
        source = "dummy"
        cache_ttl_seconds = 60

    c = C()
    assert c.load_cache() is None
    c.save_cache({"hello": "world"})
    loaded = c.load_cache()
    assert loaded == {"hello": "world"}


def test_cache_expired(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))

    class C(AnalyticsConnector):
        source = "dummy"
        cache_ttl_seconds = 1

    c = C()
    c.save_cache({"x": 1})
    # Forzar expiración
    p = c._cache_path()
    payload = json.loads(p.read_text(encoding="utf-8"))
    payload["ts"] = time.time() - 999
    p.write_text(json.dumps(payload), encoding="utf-8")
    assert c.load_cache() is None


# ---- Spotify --------------------------------------------------------------


def test_spotify_missing_config():
    sp = SpotifyAnalytics(env={})
    assert not sp.is_configured()
    assert set(sp.missing_config()) == {
        "SPOTIFY_SP_DC",
        "SPOTIFY_SP_KEY",
        "SPOTIFY_PODCAST_ID",
    }


def test_spotify_configured():
    sp = SpotifyAnalytics(env={
        "SPOTIFY_SP_DC": "a", "SPOTIFY_SP_KEY": "b", "SPOTIFY_PODCAST_ID": "c",
    })
    assert sp.is_configured()
    assert sp.missing_config() == []


def test_spotify_unavailable_when_lib_missing():
    sp = SpotifyAnalytics(env={
        "SPOTIFY_SP_DC": "a", "SPOTIFY_SP_KEY": "b", "SPOTIFY_PODCAST_ID": "c",
    })
    # Simulamos que la librería no está instalada (caso entorno CI sin extras).
    with patch.dict(sys.modules, {"spotifyconnector": None}):
        with pytest.raises(Unavailable):
            sp._client()


def test_spotify_fetch_show_with_mocked_client():
    sp = SpotifyAnalytics(env={
        "SPOTIFY_SP_DC": "a", "SPOTIFY_SP_KEY": "b", "SPOTIFY_PODCAST_ID": "podX",
    })
    fake = MagicMock()
    fake.metadata.return_value = {"name": "My Pod", "totalEpisodes": 10}
    fake.followers.return_value = {"total": 1234, "new": 12}
    fake.streams.return_value = {"total": 5000}
    with patch.object(sp, "_client", return_value=fake):
        show = sp.fetch_show(window_days=30)
    assert show is not None
    assert show.followers == 1234
    assert show.new_followers == 12
    assert show.total_streams_window == 5000
    assert show.extra["name"] == "My Pod"


def test_spotify_fetch_episodes_with_mocked_client():
    sp = SpotifyAnalytics(env={
        "SPOTIFY_SP_DC": "a", "SPOTIFY_SP_KEY": "b", "SPOTIFY_PODCAST_ID": "podX",
    })
    fake = MagicMock()
    fake.episodes.return_value = [
        {"id": "ep1", "name": "Ep 1", "releaseDate": "2026-01-15", "duration": 1800},
        {"id": "ep2", "name": "Ep 2", "releaseDate": "2026-02-01", "duration": 2400},
    ]
    fake.performance.return_value = {
        "starts": 500, "listeners": 400, "completionRate": 0.85, "averageListen": 1500,
    }
    with patch.object(sp, "_client", return_value=fake):
        eps = sp.fetch_episodes(window_days=60)
    assert len(eps) == 2
    assert eps[0].title == "Ep 1"
    assert eps[0].streams == 500
    assert eps[0].completion_rate == 0.85
    assert eps[0].publish_date == date(2026, 1, 15)


# ---- iVoox ----------------------------------------------------------------


SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Test Podcast</title>
    <itunes:author>Iago</itunes:author>
    <description>Un podcast de prueba</description>
    <language>es</language>
    <item>
      <title>Episodio 1</title>
      <link>https://www.ivoox.com/ep1</link>
      <pubDate>Mon, 05 May 2025 10:00:00 +0000</pubDate>
      <guid>ep1-guid</guid>
      <itunes:duration>00:25:30</itunes:duration>
      <enclosure url="https://cdn.ivoox.com/ep1.mp3" length="0" type="audio/mpeg"/>
    </item>
    <item>
      <title>Episodio 2</title>
      <link>https://www.ivoox.com/ep2</link>
      <pubDate>Mon, 12 May 2025 10:00:00 +0000</pubDate>
      <guid>ep2-guid</guid>
      <itunes:duration>1500</itunes:duration>
      <enclosure url="https://cdn.ivoox.com/ep2.mp3" length="0" type="audio/mpeg"/>
    </item>
  </channel>
</rss>
"""


def test_ivoox_missing_config():
    iv = IvooxAnalytics(env={})
    assert not iv.is_configured()
    assert iv.missing_config() == ["IVOOX_RSS_URL"]


def test_ivoox_parse_rss_feed_info():
    pytest.importorskip("feedparser")
    info, eps = parse_rss_bytes(SAMPLE_RSS)
    assert info.title == "Test Podcast"
    assert info.author == "Iago"
    assert info.language == "es"
    assert len(eps) == 2
    assert eps[0].title == "Episodio 1"
    assert eps[0].duration_seconds == 25 * 60 + 30
    assert eps[1].duration_seconds == 1500


def test_ivoox_csv_normalization(tmp_path):
    pytest.importorskip("pandas")
    csv_path = tmp_path / "stats.csv"
    csv_path.write_text(
        "Fecha;Episodio;Escuchas\n01/05/2025;Ep 1;100\n02/05/2025;Ep 2;250\n",
        encoding="utf-8-sig",
    )
    df = IvooxAnalytics.load_stats_csv(csv_path)
    assert list(df.columns) == ["fecha", "episodio", "escuchas"]
    assert df["escuchas"].sum() == 350


# ---- LinkedIn -------------------------------------------------------------


def test_linkedin_missing_config():
    li = LinkedInAnalytics(env={})
    assert not li.is_configured()
    assert "LINKEDIN_CLIENT_ID" in li.missing_config()


def test_linkedin_authorization_url():
    li = LinkedInAnalytics(env={
        "LINKEDIN_CLIENT_ID": "abc",
        "LINKEDIN_CLIENT_SECRET": "secret",
        "LINKEDIN_ORG_URN": "urn:li:organization:1",
    })
    url = li.authorization_url(
        "http://localhost:8501/cb", ["r_organization_social"], state="xyz"
    )
    assert url.startswith("https://www.linkedin.com/oauth/v2/authorization?")
    assert "client_id=abc" in url
    assert "state=xyz" in url
    assert "r_organization_social" in url


def test_linkedin_token_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    li = LinkedInAnalytics(env={
        "LINKEDIN_CLIENT_ID": "abc",
        "LINKEDIN_CLIENT_SECRET": "secret",
        "LINKEDIN_ORG_URN": "urn:li:organization:1",
    })
    li.save_tokens({"access_token": "AT", "expires_in": 3600, "refresh_token": "RT"})
    loaded = li._load_tokens()
    assert loaded["access_token"] == "AT"
    assert loaded["expires_at"] > int(time.time())


def test_linkedin_share_stats_with_mocked_http(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    li = LinkedInAnalytics(env={
        "LINKEDIN_CLIENT_ID": "abc",
        "LINKEDIN_CLIENT_SECRET": "secret",
        "LINKEDIN_ORG_URN": "urn:li:organization:1",
    })
    li.save_tokens({"access_token": "AT", "expires_in": 3600})

    fake_resp = MagicMock()
    fake_resp.raise_for_status.return_value = None
    fake_resp.json.return_value = {
        "elements": [{
            "totalShareStatistics": {
                "impressionCount": 100, "clickCount": 10, "likeCount": 5,
                "commentCount": 2, "shareCount": 1, "engagement": 0.18,
                "uniqueImpressionsCount": 90,
            }
        }]
    }
    with patch("requests.get", return_value=fake_resp) as mock_get:
        stats = li.fetch_share_statistics()
    assert stats["impressionCount"] == 100
    assert stats["engagement"] == 0.18
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["headers"]["LinkedIn-Version"] == "202604"
    assert kwargs["headers"]["Authorization"] == "Bearer AT"


def test_linkedin_fetch_posts_chunks_and_merges(tmp_path, monkeypatch):
    monkeypatch.setenv("REPO_ROOT", str(tmp_path))
    li = LinkedInAnalytics(env={
        "LINKEDIN_CLIENT_ID": "abc",
        "LINKEDIN_CLIENT_SECRET": "secret",
        "LINKEDIN_ORG_URN": "urn:li:organization:1",
    })
    li.save_tokens({"access_token": "AT", "expires_in": 3600})

    now_ms = int(datetime.now().timestamp() * 1000)
    posts_resp = {
        "elements": [
            {"id": "urn:li:ugcPost:111", "publishedAt": now_ms, "commentary": "Hola"},
            {"id": "urn:li:ugcPost:222", "publishedAt": now_ms, "commentary": "Mundo"},
        ]
    }
    stats_resp = {
        "elements": [
            {"ugcPost": "urn:li:ugcPost:111",
             "totalShareStatistics": {"impressionCount": 10, "likeCount": 1}},
            {"ugcPost": "urn:li:ugcPost:222",
             "totalShareStatistics": {"impressionCount": 20, "likeCount": 3}},
        ]
    }
    responses = [posts_resp, stats_resp]

    def fake_get(url, headers=None, params=None, timeout=None):
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = responses.pop(0)
        return m

    with patch("requests.get", side_effect=fake_get):
        posts = li.fetch_posts(window_days=30)

    assert len(posts) == 2
    by_id = {p.post_id: p for p in posts}
    assert by_id["urn:li:ugcPost:111"].impressions == 10
    assert by_id["urn:li:ugcPost:222"].likes == 3
    assert posts[0].text_preview in ("Hola", "Mundo")
