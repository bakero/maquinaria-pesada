"""Extracción de la pre-escritura obligatoria desde el texto del PDF fuente.

Spec M (§7.1) y T (§7.1): antes de generar el guion, el generador rellena
internamente una tabla con datos numéricos, casos con nombre propio,
frase-fuerza y contraintuitivos del PDF.

Este módulo aplica heurísticas estables sobre el texto del PDF para extraerlos
y devolverlos en una estructura que el generador inyecta en el prompt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_NUMERIC_RE = re.compile(
    r"(?:\d{1,3}(?:[.,]\d+)?\s*%"      # 3.7%, 80%
    r"|\$\s*\d+(?:[.,]\d+)?\s*(?:[KMB]|millones|millardos)?\b"  # $3M, $250
    r"|\b\d{4}\b"                      # 2017
    r"|\b\d+(?:[.,]\d{3})+\b"          # 1.234, 12.000
    r"|\b\d+(?:[.,]\d+)?\s+(?:millones|empresas|usuarios|paises|paises|veces|horas|minutos)\b"
    r")",
    re.IGNORECASE,
)

# Nombres propios reconocibles del corpus tech.
_NAMED_ORGS = (
    "OpenAI", "Anthropic", "Google", "Meta", "Microsoft", "IBM", "Amazon",
    "Apple", "DeepMind", "Hugging Face", "Stability AI", "Cohere", "Mistral",
    "Stanford", "MIT", "Gartner", "McKinsey", "Forrester", "IDC",
    "Spotify", "Netflix", "Airbnb", "Uber", "Tesla", "Salesforce",
    "Oracle", "SAP", "Adobe", "BBVA", "Santander", "Telefonica", "Telefónica",
    "Repsol", "Iberdrola", "Mercadona", "Inditex",
)

_CONTRAINTUITIVE_MARKERS = (
    "sorprendentemente", "contrariamente", "a pesar de", "sin embargo",
    "paradójicamente", "lo curioso", "lo contraintuitivo",
    "no es lo que parece", "se suele creer", "el mito",
)


@dataclass
class PreWriting:
    datos_numericos: list[str] = field(default_factory=list)
    casos_nombre_propio: list[str] = field(default_factory=list)
    frase_fuerza: str = ""
    contraintuitivos: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "datos_numericos_count": len(self.datos_numericos),
            "casos_nombre_propio_count": len(self.casos_nombre_propio),
            "has_frase_fuerza": bool(self.frase_fuerza),
            "contraintuitivos_count": len(self.contraintuitivos),
        }

    def meets_minimum(self, *, datos_min: int, casos_min: int,
                      contraintuitivos_min: int) -> bool:
        return (
            len(self.datos_numericos) >= datos_min
            and len(self.casos_nombre_propio) >= casos_min
            and bool(self.frase_fuerza)
            and len(self.contraintuitivos) >= contraintuitivos_min
        )


def _extract_first_sentence_with(text: str, markers: list[str]) -> str:
    """Devuelve la primera frase del texto que contenga alguno de los markers."""
    sentences = re.split(r"(?<=[.!?…])\s+", text)
    low_markers = [m.lower() for m in markers]
    for s in sentences:
        s_low = s.lower()
        if any(m in s_low for m in low_markers):
            return s.strip()
    return ""


def _extract_frase_fuerza(text: str) -> str:
    """Heurística para la frase-fuerza del resumen ejecutivo: la primera frase
    de >12 palabras que aparezca en los primeros 1500 caracteres."""
    chunk = text[:1500]
    for s in re.split(r"(?<=[.!?…])\s+", chunk):
        words = re.findall(r"\b[\wáéíóúñÁÉÍÓÚÑ]+\b", s)
        if 12 <= len(words) <= 35:
            return s.strip()
    return ""


def extract_pre_writing(pdf_text: str) -> PreWriting:
    """Extrae la tabla de pre-escritura desde el texto del PDF.

    Las heurísticas son tolerantes: si el PDF no aporta material para alguna
    categoría, el generador hace fallback hard-fail (responsabilidad del
    generador, no de este módulo).
    """
    pw = PreWriting()

    # Datos numéricos: hasta 10 distintos.
    seen = set()
    for m in _NUMERIC_RE.finditer(pdf_text):
        v = re.sub(r"\s+", " ", m.group(0).strip())
        key = v.lower()
        if key in seen:
            continue
        seen.add(key)
        pw.datos_numericos.append(v)
        if len(pw.datos_numericos) >= 10:
            break

    # Casos con nombre propio reconocibles.
    for org in _NAMED_ORGS:
        if re.search(rf"\b{re.escape(org)}\b", pdf_text):
            if org not in pw.casos_nombre_propio:
                pw.casos_nombre_propio.append(org)

    # Frase-fuerza del primer tramo del PDF.
    pw.frase_fuerza = _extract_frase_fuerza(pdf_text)

    # Contraintuitivos: frases con marcadores.
    contras: list[str] = []
    for marker in _CONTRAINTUITIVE_MARKERS:
        s = _extract_first_sentence_with(pdf_text, [marker])
        if s and s not in contras:
            contras.append(s[:200])
        if len(contras) >= 5:
            break
    pw.contraintuitivos = contras

    return pw
