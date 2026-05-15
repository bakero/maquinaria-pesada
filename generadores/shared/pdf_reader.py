"""Lectura de PDFs del corpus del máster, con tracking de tokens.

Wrapper fino sobre `pdfplumber` para que los generadores reciban texto +
contador de tokens estimados sin tener que importar la librería directamente.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PdfReadResult:
    path: Path
    text: str
    page_count: int
    estimated_tokens: int

    @property
    def empty(self) -> bool:
        return self.estimated_tokens <= 0


def _estimate_tokens(text: str) -> int:
    """Estimación robusta de tokens (1 token ≈ 0.75 palabras en español)."""
    words = len(re.findall(r"\b[\wáéíóúñÁÉÍÓÚÑ]+\b", text))
    return int(words / 0.75) if words else 0


def read_pdf(path: str | Path) -> PdfReadResult:
    """Lee un PDF y devuelve texto + tokens estimados. Si pdfplumber no está
    disponible o el fichero no existe, devuelve un resultado vacío en lugar de
    reventar."""
    pth = Path(path)
    if not pth.exists():
        return PdfReadResult(pth, "", 0, 0)
    try:
        import pdfplumber
    except ImportError:  # pragma: no cover
        return PdfReadResult(pth, "", 0, 0)
    try:
        parts: list[str] = []
        with pdfplumber.open(str(pth)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                t = page.extract_text() or ""
                parts.append(t)
        text = "\n".join(parts).strip()
        return PdfReadResult(pth, text, page_count, _estimate_tokens(text))
    except Exception:  # noqa: BLE001
        return PdfReadResult(pth, "", 0, 0)


def find_resumen(repo_root: Path, modulo_n: int) -> Path | None:
    """Localiza `PDFs/resumenes/RESUMEN_M{n}_*.pdf` por módulo."""
    pattern = f"RESUMEN_M{modulo_n}_*.pdf"
    matches = sorted((repo_root / "PDFs" / "resumenes").glob(pattern))
    return matches[0] if matches else None


def find_tema(repo_root: Path, modulo_n: int, tema_n: int) -> Path | None:
    """Localiza `PDFs/temas/M{n}_T{x}_*.pdf` por módulo y tema."""
    pattern = f"M{modulo_n}_T{tema_n}_*.pdf"
    matches = sorted((repo_root / "PDFs" / "temas").glob(pattern))
    return matches[0] if matches else None


def coverage_percent(script_text: str, concepts: list[str]) -> float:
    """Porcentaje de los conceptos clave que aparecen en el guion (case-insensitive)."""
    if not concepts:
        return 100.0
    needle_text = script_text.lower()
    hits = sum(1 for c in concepts if c.strip().lower() in needle_text)
    return 100.0 * hits / len(concepts)
