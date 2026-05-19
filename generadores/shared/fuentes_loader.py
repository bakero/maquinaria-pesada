"""Lectura del glosario y de las fuentes auxiliares.

`PDFs/auxiliares/glosario_unificado.md` tiene un formato estructurado:
- Entradas como `## Término (sigla opcional)`
- Línea `**Fuentes:** M3_T1, M3_T2, ...`
- Línea opcional `**S:** N` (orden de publicación del Short)
- Definición libre

Este módulo lo parsea a un diccionario consumible por el generador S y por la
validación de cobertura del generador M/T.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_DEFAULT_GLOSARIO = (
    Path(__file__).resolve().parents[2] / "PDFs" / "auxiliares" / "glosario_unificado.md"
)

HEADING_RE = re.compile(r"^##\s+(?P<name>[^\n]+?)\s*$", re.MULTILINE)
FUENTES_LINE_RE = re.compile(r"^\*\*Fuentes:\*\*\s+(?P<src>[^\n]+)$", re.MULTILINE)
S_LINE_RE = re.compile(r"^\*\*S:\*\*\s+(?P<n>\d+)\s*$", re.MULTILINE)
# v6.1 — Expansión castellana del término (siglas/anglicismos).
ES_LINE_RE = re.compile(r"^\*\*ES:\*\*\s+(?P<es>[^\n]+)$", re.MULTILINE)


@dataclass
class GlosarioFuente:
    modulo: str          # "M3"
    tema: str | None     # "T1" o None si es _RESUMEN
    raw: str             # "M3_T1" / "M3_RESUMEN" / "base"

    @property
    def es_resumen(self) -> bool:
        return self.raw.endswith("_RESUMEN")


@dataclass
class GlosarioEntry:
    name: str                          # nombre canónico (sin paréntesis)
    sigla: str | None = None           # "RAG", "LLM"... si lo lleva entre paréntesis
    fuentes: list[GlosarioFuente] = field(default_factory=list)
    s_number: int | None = None        # número de orden de publicación del Short
    definicion: str = ""
    expansion_es: str | None = None    # v6.1 — expansión castellana al primer uso

    @property
    def modulos_distintos(self) -> set[str]:
        return {f.modulo for f in self.fuentes}

    @property
    def aparece_en_resumen(self) -> bool:
        return any(f.es_resumen for f in self.fuentes)

    @property
    def bilingual_split(self) -> str | None:
        """Si el heading tiene formato 'X / Y' devuelve Y (la traducción).

        Permite usar el segundo segmento del heading bilingüe como expansión
        castellana implícita cuando no hay campo `**ES:**` explícito.
        Ej: 'Hallucination / Alucinación' → 'Alucinación'.
        """
        parts = [p.strip() for p in self.name.split("/")]
        if len(parts) == 2 and parts[1]:
            return parts[1]
        return None

    @property
    def expansion_castellana(self) -> str | None:
        """Expansión castellana efectiva: campo `**ES:**` si existe, si no,
        segundo segmento del heading bilingüe. None si nada disponible.
        """
        if self.expansion_es:
            return self.expansion_es
        return self.bilingual_split

    @property
    def needs_first_use_expansion(self) -> bool:
        """¿Esta entrada debe expandirse al primer uso en un guion?

        Sí cuando hay sigla canónica entre paréntesis o cuando el nombre es
        un anglicismo evidente. En la práctica: hay expansión castellana
        disponible (campo `**ES:**` o heading bilingüe) Y el término tiene
        sigla o lleva paréntesis con la versión extendida.
        """
        return (self.expansion_castellana is not None) and (
            self.sigla is not None or "/" in self.name
        )


def _parse_fuentes_line(src: str) -> list[GlosarioFuente]:
    out: list[GlosarioFuente] = []
    for raw in re.split(r"[,\s]+", src.strip()):
        raw = raw.strip().strip(",")
        if not raw:
            continue
        if raw.lower() == "base":
            continue
        m = re.match(r"^M(\d+)(?:_(T\d+|RESUMEN))?$", raw)
        if not m:
            continue
        modulo = f"M{m.group(1)}"
        tema = m.group(2) if m.group(2) else None
        out.append(GlosarioFuente(modulo=modulo, tema=tema, raw=raw))
    return out


def _split_heading(name: str) -> tuple[str, str | None]:
    """`RAG (Retrieval-Augmented Generation)` → (`RAG (...)`, `Retrieval-Augmented Generation`).

    Devolvemos el nombre canónico TAL CUAL aparece en el heading (sin alterar) y
    la sigla/etiqueta entre paréntesis si hay una.
    """
    m = re.match(r"^(.+?)\s+\((.+)\)\s*$", name)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return name.strip(), None


def parse_glosario(text: str) -> list[GlosarioEntry]:
    """Parsea el glosario en una lista de entradas estructuradas."""
    entries: list[GlosarioEntry] = []
    headings = list(HEADING_RE.finditer(text))
    for i, m in enumerate(headings):
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]
        name_full = m.group("name")
        name, sigla = _split_heading(name_full)

        entry = GlosarioEntry(name=name, sigla=sigla)
        fm = FUENTES_LINE_RE.search(body)
        if fm:
            entry.fuentes = _parse_fuentes_line(fm.group("src"))
        sm = S_LINE_RE.search(body)
        if sm:
            entry.s_number = int(sm.group("n"))
        em = ES_LINE_RE.search(body)
        if em:
            entry.expansion_es = em.group("es").strip()
        # Definición = todo el body sin las líneas estructuradas.
        def_text = FUENTES_LINE_RE.sub("", body)
        def_text = S_LINE_RE.sub("", def_text)
        def_text = ES_LINE_RE.sub("", def_text)
        entry.definicion = def_text.strip()
        entries.append(entry)
    return entries


def load_glosario(path: Path | None = None) -> list[GlosarioEntry]:
    """Carga y parsea el glosario_unificado.md."""
    path = path or _DEFAULT_GLOSARIO
    if not path.exists():
        return []
    return parse_glosario(path.read_text(encoding="utf-8"))


def find_entry(entries: list[GlosarioEntry], term: str) -> GlosarioEntry | None:
    """Busca una entrada por nombre canónico (case-insensitive).

    Acepta también coincidencia con el primer segmento separado por " / "
    (p. ej. "Hallucination" matchea "Hallucination / Alucinación").
    """
    needle = term.strip().lower()
    for e in entries:
        if e.name.lower() == needle:
            return e
        if e.sigla and e.sigla.lower() == needle:
            return e
        # Match con primer segmento separado por "/" (alias bilingüe canónico).
        first_part = e.name.split("/")[0].strip().lower()
        if first_part == needle:
            return e
    return None


def entries_for_module(entries: list[GlosarioEntry], modulo: str) -> list[GlosarioEntry]:
    """Devuelve las entradas que aparecen en algún tema/resumen del módulo dado."""
    return [e for e in entries if modulo in e.modulos_distintos]


def write_s_number(path: Path, entry_name: str, s_number: int) -> bool:
    """Inserta o actualiza la línea `**S:** N` justo debajo de `**Fuentes:**`
    para la entrada con el nombre indicado. Devuelve True si modificó el fichero.
    """
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    headings = list(HEADING_RE.finditer(text))
    for i, m in enumerate(headings):
        name, _sigla = _split_heading(m.group("name"))
        if name != entry_name:
            continue
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]
        new_s_line = f"\n**S:** {s_number}"
        if S_LINE_RE.search(body):
            new_body = S_LINE_RE.sub(f"**S:** {s_number}", body)
        elif FUENTES_LINE_RE.search(body):
            new_body = FUENTES_LINE_RE.sub(
                lambda fm, sline=new_s_line: fm.group(0) + sline,
                body, count=1)
        else:
            new_body = f"\n**S:** {s_number}\n" + body
        text = text[:start] + new_body + text[end:]
        path.write_text(text, encoding="utf-8")
        return True
    return False
