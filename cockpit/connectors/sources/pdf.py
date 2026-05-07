from __future__ import annotations

from pathlib import Path

from cockpit.connectors.base import SourceConnector, register
from cockpit.core import paths


@register
class PdfSource(SourceConnector):
    id = "pdf"
    label = "PDFs (fuentes)"
    icon = "📄"
    description = "Resúmenes RESUMEN_M{N}_*.pdf de los módulos."
    suffixes = (".pdf",)

    def list_items(self) -> list[Path]:
        d = paths.pdfs_dir()
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.suffix.lower() == ".pdf")

    def render_viewer(self, path: Path) -> None:
        import streamlit as st
        st.write(f"**{path.name}** — {path.stat().st_size / 1024:.1f} KB")
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                pages = pdf.pages
                st.caption(f"{len(pages)} páginas")
                page_n = st.number_input("Página", 1, len(pages), 1)
                text = pages[page_n - 1].extract_text() or "(página vacía)"
                st.text_area("Texto", text, height=400)
        except Exception as exc:
            st.error(f"No se pudo abrir el PDF: {exc}")
        with open(path, "rb") as f:
            st.download_button("Descargar PDF", f, file_name=path.name)
