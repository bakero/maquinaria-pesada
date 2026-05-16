from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class PdfSource(SourceConnector):
    id = "pdf"
    label = "PDFs (fuentes)"
    description = "Resúmenes RESUMEN_M{N}_*.pdf de los módulos."
    suffixes = (".pdf",)

    def list_items(self) -> list[Path]:
        d = paths.pdfs_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() == ".pdf")
