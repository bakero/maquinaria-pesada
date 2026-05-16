from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class LogSource(SourceConnector):
    id = "log"
    label = "Logs de producción"
    description = "episodios/*.log generados por las ejecuciones."
    suffixes = (".log",)

    def list_items(self) -> list[Path]:
        roots = [paths.episodios_dir(), paths.output_dir(), paths.repo_root()]
        seen: set[Path] = set()
        items: list[Path] = []
        for d in roots:
            if not d.exists():
                continue
            for p in d.glob("*.log"):
                if p.is_file() and p not in seen:
                    seen.add(p)
                    items.append(p)
        return sorted(items)
