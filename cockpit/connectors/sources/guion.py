from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class GuionSource(SourceConnector):
    id = "guion"
    label = "Guiones"
    icon = "📜"
    description = "Guiones .txt con etiquetas TTS y bloques IAGO/MARIA."
    suffixes = (".txt",)

    def list_items(self) -> list[Path]:
        d = paths.guiones_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() == ".txt")

    def render_viewer(self, path: Path) -> None:
        import streamlit as st
        text = path.read_text(encoding="utf-8", errors="replace")
        words = len(text.split())
        st.write(f"**{path.name}** — {words} palabras · {path.stat().st_size} bytes")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_area("Contenido", text, height=500)
        with col2:
            st.metric("Palabras", words)
            target_min, target_max = 1900, 2100
            in_range = target_min <= words <= target_max
            st.write(f"Rango objetivo: {target_min}-{target_max}")
            st.write("✅ dentro" if in_range else "⚠️ fuera de rango")
            iago_blocks = text.count("[IAGO]") or text.upper().count("IAGO:")
            maria_blocks = text.count("[MARIA]") or text.upper().count("MARIA:")
            st.write(f"Bloques IAGO: {iago_blocks}")
            st.write(f"Bloques MARIA: {maria_blocks}")
