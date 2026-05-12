"""Conectores de analytics externas (Spotify, iVoox, LinkedIn).

Cada submódulo expone un cliente que devuelve `EpisodeMetric` / `PostMetric`
normalizados (ver `base.py`). Las llamadas reales requieren credenciales en
`.env`; los conectores degradan a "no configurado" si faltan.

Tests sin red: mockear `requests.get`/`requests.post` o las clases cliente.
"""
from __future__ import annotations

from .base import (
    AnalyticsConnector,
    EpisodeMetric,
    PostMetric,
    ShowMetric,
    Unavailable,
)

__all__ = [
    "AnalyticsConnector",
    "EpisodeMetric",
    "PostMetric",
    "ShowMetric",
    "Unavailable",
]
