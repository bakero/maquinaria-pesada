from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class GuionSource(SourceConnector):
    id = "guion"
    label = "Guiones"
    description = "Guiones .txt con etiquetas TTS y bloques IAGO/MARIA."
    suffixes = (".txt",)

    def list_items(self) -> list[Path]:
        d = paths.guiones_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() == ".txt")
