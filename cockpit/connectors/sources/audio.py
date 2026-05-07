from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class AudioSource(SourceConnector):
    id = "audio"
    label = "Audio (episodios)"
    icon = "🎵"
    description = "MP3 finales y temporales en episodios/."
    suffixes = (".mp3",)

    def list_items(self) -> list[Path]:
        d = paths.episodios_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() == ".mp3")

    def render_viewer(self, path: Path) -> None:
        import streamlit as st
        size_mb = path.stat().st_size / (1024 * 1024)
        st.write(f"**{path.name}** — {size_mb:.2f} MB")
        with open(path, "rb") as f:
            data = f.read()
        st.audio(data, format="audio/mp3")
        st.download_button("Descargar MP3", data, file_name=path.name)
