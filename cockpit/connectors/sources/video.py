from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class VideoSource(SourceConnector):
    id = "video"
    label = "Vídeo (episodios)"
    description = "Videopodcast final en Videos/."
    suffixes = (".mp4", ".mov", ".mkv")

    def list_items(self) -> list[Path]:
        d = paths.videos_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() in self.suffixes)
