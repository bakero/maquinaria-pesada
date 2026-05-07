from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class VideoSource(SourceConnector):
    id = "video"
    label = "Vídeo (episodios)"
    icon = "🎬"
    description = "Videopodcast final en Videos/."
    suffixes = (".mp4", ".mov", ".mkv")

    def list_items(self) -> list[Path]:
        d = paths.videos_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() in self.suffixes)

    def render_viewer(self, path: Path) -> None:
        import streamlit as st
        size_mb = path.stat().st_size / (1024 * 1024)
        st.write(f"**{path.name}** — {size_mb:.1f} MB")
        try:
            with open(path, "rb") as f:
                st.video(f.read())
        except Exception as exc:
            st.warning(f"No se pudo previsualizar: {exc}")
            st.caption(str(path))
