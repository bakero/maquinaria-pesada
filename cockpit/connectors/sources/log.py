from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class LogSource(SourceConnector):
    id = "log"
    label = "Logs de producción"
    icon = "📜"
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

    def render_viewer(self, path: Path) -> None:
        import streamlit as st
        n_lines = st.slider("Últimas N líneas", 50, 5000, 500, step=50)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            st.error(f"No se pudo leer: {exc}")
            return
        lines = content.splitlines()
        st.caption(f"{len(lines)} líneas · {path.stat().st_size / 1024:.1f} KB")
        st.code("\n".join(lines[-n_lines:]) or "(vacío)", language="log")
