from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class AudioSource(SourceConnector):
    id = "audio"
    label = "Audio (episodios)"
    description = "MP3 finales y temporales en episodios/."
    suffixes = (".mp3",)

    def list_items(self) -> list[Path]:
        d = paths.episodios_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() == ".mp3")
