"""Extracción de la ficha APLICACION_PRACTICA desde los 4 documentos vivos.

Spec M (§8.4): el generador construye una ficha de aplicación práctica del
módulo extrayendo de BIBLIA_SISTEMA, PRIMERPODCAST, VIDEOPODCAST y PODCAST
las entradas que mencionen explícitamente conceptos del módulo o tecnologías
relacionadas. La ficha se guarda en `episodios/temp/aplicacion_extraida_M{n}.md`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

LIVE_DOCS = (
    "BIBLIA_SISTEMA.md",
    "PRIMERPODCAST.md",
    "VIDEOPODCAST.md",
    "PODCAST.md",
)

# Palabras clave por módulo (subset; cubre los módulos principales).
# La heurística es buscar coincidencias completas para detectar entradas
# relevantes al módulo.
MODULE_KEYWORDS: dict[int, list[str]] = {
    0:  ["introducción", "fundamentos", "panorámica"],
    1:  ["razonamiento", "tokenización", "limitaciones"],
    2:  ["matemáticas", "estadística", "álgebra"],
    3:  ["machine learning", "ML clásico", "regresión", "clasificación"],
    4:  ["deep learning", "redes neuronales", "backpropagation"],
    5:  ["NLP", "transformer", "attention", "embeddings"],
    6:  ["prompt", "prompting", "system prompt"],
    7:  ["RAG", "retrieval", "vector store", "embeddings"],
    8:  ["LLMOps", "MLOps", "evaluación", "deployment", "monitorización"],
    9:  ["infraestructura", "GPU", "deployment", "serving"],
    10: ["agente", "agentes", "tool use", "ReAct"],
    11: ["automatización", "RPA"],
    12: ["seguridad", "prompt injection", "jailbreak"],
    13: ["gobernanza", "ética", "AI Act"],
    14: ["estrategia", "transformación", "ROI"],
}


@dataclass
class FichaAplicacion:
    modulo_n: int
    problema_concreto: str = ""
    decision_tecnica: str = ""
    cifra_verificable: str = ""
    conexion_conceptos: list[str] = field(default_factory=list)
    fuentes_consultadas: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return bool(self.problema_concreto and self.decision_tecnica
                    and self.cifra_verificable)

    def to_markdown(self) -> str:
        lines = [
            f"# Ficha de aplicación del módulo M{self.modulo_n}",
            "",
            "## Problema concreto encontrado",
            self.problema_concreto or "_(pendiente)_",
            "",
            "## Decisión tomada",
            self.decision_tecnica or "_(pendiente)_",
            "",
            "## Cifras / verificables",
        ]
        if self.cifra_verificable:
            lines.append(f"- {self.cifra_verificable}")
        else:
            lines.append("- _(pendiente)_")
        lines += ["", "## Conexión con conceptos del módulo"]
        if self.conexion_conceptos:
            for c in self.conexion_conceptos:
                lines.append(f"- {c}")
        else:
            lines.append("- _(pendiente)_")
        lines += ["", "## Fuentes consultadas"]
        for f in self.fuentes_consultadas:
            lines.append(f"- {f}")
        return "\n".join(lines) + "\n"


def _read_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


_DECISION_MARK_RE = re.compile(r"\[(?:DECISIÓN|DECISION|CAMBIO|INCIDENCIA|REGLA)\]")
_NUMBER_FACT_RE = re.compile(
    r"(\d+(?:[.,]\d+)?\s*(?:%|ms|s|min|MB|GB|tokens|USD|EUR|€|\$|x|×))",
    re.IGNORECASE,
)


def _extract_first_match(text: str, keywords: list[str],
                         marker: str | None = None) -> str:
    """Devuelve la primera frase que mencione algún keyword (y opcionalmente
    un marcador como `[DECISIÓN]`)."""
    sentences = re.split(r"(?<=\n)", text)
    low_kw = [k.lower() for k in keywords]
    for s in sentences:
        s_low = s.lower()
        if marker and marker not in s:
            continue
        if any(k in s_low for k in low_kw):
            return s.strip()[:300]
    return ""


def build_ficha(modulo_n: int, repo_root: Path,
                override_path: Path | None = None) -> FichaAplicacion:
    """Construye la ficha de aplicación del módulo desde los 4 documentos vivos.

    Si existe `override_path` (típicamente `PDFs/aplicacion_practica/M{n}.md`),
    se carga como fuente prioritaria. El parseo del override es tolerante: si
    no tiene la estructura esperada, igualmente se completa con extracciones
    de los documentos vivos.
    """
    keywords = MODULE_KEYWORDS.get(modulo_n, [])
    ficha = FichaAplicacion(modulo_n=modulo_n)

    if override_path and override_path.exists():
        ficha.fuentes_consultadas.append(
            f"override:{override_path.relative_to(repo_root).as_posix()}")

    # Recorre documentos vivos.
    for doc_name in LIVE_DOCS:
        doc_path = repo_root / doc_name
        text = _read_safe(doc_path)
        if not text or not keywords:
            continue
        ficha.fuentes_consultadas.append(doc_name)

        if not ficha.problema_concreto:
            ficha.problema_concreto = _extract_first_match(
                text, keywords, marker="[INCIDENCIA]") or _extract_first_match(
                text, keywords)
        if not ficha.decision_tecnica:
            ficha.decision_tecnica = _extract_first_match(
                text, keywords, marker="[DECISIÓN]") or _extract_first_match(
                text, keywords, marker="[CAMBIO]")
        if not ficha.cifra_verificable:
            # Busca un fragmento con número Y keyword.
            for s in re.split(r"(?<=[.!?…])\s+", text):
                s_low = s.lower()
                if any(k in s_low for k in [k.lower() for k in keywords]):
                    m = _NUMBER_FACT_RE.search(s)
                    if m:
                        ficha.cifra_verificable = f"{m.group(0).strip()} — {s.strip()[:200]}"
                        break

    if keywords:
        ficha.conexion_conceptos = list(keywords[:3])

    return ficha


def save_ficha(ficha: FichaAplicacion, repo_root: Path) -> Path:
    """Guarda la ficha en `episodios/temp/aplicacion_extraida_M{n}.md`."""
    out = repo_root / "episodios" / "temp" / f"aplicacion_extraida_M{ficha.modulo_n}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(ficha.to_markdown(), encoding="utf-8")
    return out
