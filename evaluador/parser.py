"""Parser de guiones a estructura intermedia.

Acepta dos sintaxis de etiqueta TTS por compatibilidad con corpus mixto:
- `[didactico]` (spec v6 canónico)
- `<didactico>` (corpus legacy `.txt`)

Acepta también `YAGO:` además de `IAGO:` como tag de speaker (el corpus
real usa ambos, normalizamos a `IAGO`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Conteo de palabras compatible con podcast_spec.py
WORD_REGEX = re.compile(
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:[-'][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)?"
)

SECTION_HEADER_REGEX = re.compile(r"^#\s+([A-Z][A-Z0-9_]*)\s*$")

SPEAKER_REGEX = re.compile(
    r"^(IAGO|YAGO|MARIA|MAR[ÍI]A)\s*:\s*(.*)$",
    re.IGNORECASE,
)

# Etiqueta TTS al inicio de intervención: [foo] o <foo>
TTS_TAG_REGEX = re.compile(
    r"^\s*(?:\[([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)\]|<([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)>)\s*"
)

# Comentarios narrativos: [INTRO - ...], [NOTA: ...], [pausa breve]
INLINE_COMMENT_REGEX = re.compile(r"\[[^\]]+\]")
# SSML breaks: <break time="500ms"/>
SSML_BREAK_REGEX = re.compile(r"<break\s+time\s*=\s*\"[^\"]+\"\s*/?>")

# Detector de oraciones (heurística simple; suficiente para conteo)
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[\.\!\?])\s+(?=[A-ZÁÉÍÓÚÜÑ¿¡])")


def normalize_speaker(name: str) -> str:
    n = name.upper().replace("Í", "I")
    if n == "YAGO":
        return "IAGO"  # interno
    return n  # MARIA, IAGO


def count_words(text: str) -> int:
    return len(WORD_REGEX.findall(text))


def strip_inline_artifacts(text: str) -> str:
    """Elimina comentarios `[...]` y `<break ... />` para conteo y análisis."""
    text = SSML_BREAK_REGEX.sub(" ", text)
    text = INLINE_COMMENT_REGEX.sub(" ", text)
    return text


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT_REGEX.split(text)
    return [p.strip() for p in parts if p.strip()]


@dataclass
class Intervention:
    speaker: str | None  # "IAGO" | "MARIA" | None (S)
    tag: str | None  # contenido del primer [...]/<...> de TTS
    text: str  # texto hablado tal cual (incluye <break/> y comentarios inline)
    line_start: int  # 1-indexed
    line_end: int

    @property
    def clean_text(self) -> str:
        """Texto hablado sin etiquetas SSML ni comentarios."""
        return strip_inline_artifacts(self.text).strip()

    @property
    def word_count(self) -> int:
        return count_words(self.clean_text)

    @property
    def sentence_count(self) -> int:
        return len(split_sentences(self.clean_text))


@dataclass
class Section:
    name: str
    line_start: int
    line_end: int
    interventions: list[Intervention] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return sum(i.word_count for i in self.interventions)

    def speaker_share(self) -> dict[str, int]:
        """Palabras por speaker en este bloque."""
        shares: dict[str, int] = {}
        for iv in self.interventions:
            if iv.speaker:
                shares[iv.speaker] = shares.get(iv.speaker, 0) + iv.word_count
        return shares


@dataclass
class Script:
    filename: str
    kind: str  # "M" | "T" | "S"
    raw_text: str
    sections: list[Section] = field(default_factory=list)
    # Para S: párrafos como pseudo-secciones (HOOK, DEFINICION, EJEMPLO, APLICACION_GANCHO)
    metadata: dict = field(default_factory=dict)

    def section_by_name(self, name: str) -> Section | None:
        for s in self.sections:
            if s.name == name:
                return s
        return None

    def section_names(self) -> list[str]:
        return [s.name for s in self.sections]

    @property
    def total_word_count(self) -> int:
        return sum(s.word_count for s in self.sections)

    @property
    def all_interventions(self) -> list[Intervention]:
        out: list[Intervention] = []
        for s in self.sections:
            out.extend(s.interventions)
        return out


def _extract_tts_tag(text: str) -> tuple[str | None, str]:
    """Extrae la etiqueta TTS inicial y devuelve (tag, resto_texto).

    Si no hay etiqueta inicial, devuelve (None, text_original).
    """
    m = TTS_TAG_REGEX.match(text)
    if not m:
        return None, text
    tag = m.group(1) or m.group(2)
    rest = text[m.end() :]
    return tag, rest


def _parse_interventions_block(lines: list[tuple[int, str]]) -> list[Intervention]:
    """Convierte un bloque de líneas (line_no, line) en lista de Intervention.

    Una intervención puede ocupar varias líneas hasta que aparece otro speaker
    o un bloque vacío con cambio.
    """
    interventions: list[Intervention] = []
    current_speaker: str | None = None
    current_tag: str | None = None
    current_text_lines: list[str] = []
    current_start = 0
    current_end = 0

    def flush():
        nonlocal current_speaker, current_tag, current_text_lines, current_start, current_end
        if current_speaker is None and not current_text_lines:
            return
        text = "\n".join(current_text_lines).strip()
        if not text and current_speaker is None:
            return
        interventions.append(
            Intervention(
                speaker=current_speaker,
                tag=current_tag,
                text=text,
                line_start=current_start,
                line_end=current_end,
            )
        )
        current_speaker = None
        current_tag = None
        current_text_lines = []

    for line_no, line in lines:
        stripped = line.strip()
        # Línea vacía: la incluimos como continuación silenciosa (no rompe la intervención)
        m = SPEAKER_REGEX.match(stripped)
        if m:
            # Nueva intervención
            flush()
            current_speaker = normalize_speaker(m.group(1))
            remainder = m.group(2)
            tag, body = _extract_tts_tag(remainder)
            current_tag = tag
            current_text_lines = [body] if body else []
            current_start = line_no
            current_end = line_no
        else:
            if current_speaker is None and not stripped:
                continue
            # continuación de la intervención actual (o línea solitaria sin speaker)
            if stripped:
                if current_start == 0:
                    current_start = line_no
                current_text_lines.append(line)
                current_end = line_no
            # líneas vacías dentro de una intervención: las ignoramos (continúa)
    flush()
    return interventions


def parse_script(filename: str | Path, kind: str) -> Script:
    """Parsea un guion .txt/.md a Script."""
    path = Path(filename)
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    if kind == "S":
        return _parse_s_script(path, raw, lines)

    # M / T: bloques delimitados por "# NAME"
    sections: list[Section] = []
    current_name: str | None = None
    current_start_line = 0
    current_lines: list[tuple[int, str]] = []

    for idx, line in enumerate(lines, start=1):
        m = SECTION_HEADER_REGEX.match(line)
        if m:
            # cerrar la sección anterior
            if current_name is not None:
                interventions = _parse_interventions_block(current_lines)
                sections.append(
                    Section(
                        name=current_name,
                        line_start=current_start_line,
                        line_end=idx - 1,
                        interventions=interventions,
                    )
                )
            current_name = m.group(1)
            current_start_line = idx
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append((idx, line))
            # líneas antes de cualquier sección se ignoran

    # cerrar última sección
    if current_name is not None:
        interventions = _parse_interventions_block(current_lines)
        sections.append(
            Section(
                name=current_name,
                line_start=current_start_line,
                line_end=len(lines),
                interventions=interventions,
            )
        )

    script = Script(filename=str(path), kind=kind, raw_text=raw, sections=sections)
    _populate_metadata(script)
    return script


def _parse_s_script(path: Path, raw: str, lines: list[str]) -> Script:
    """Parser de S: párrafos separados por línea en blanco.

    Cada párrafo se trata como una pseudo-sección con una sola Intervention
    sin speaker. Los nombres de bloque interno son: HOOK, DEFINICION,
    EJEMPLO, APLICACION_GANCHO (orden fijo si hay exactamente 4 párrafos).
    """
    paragraphs: list[tuple[int, int, str]] = []  # (line_start, line_end, text)
    buf: list[str] = []
    p_start = 0
    for idx, line in enumerate(lines, start=1):
        if line.strip() == "":
            if buf:
                paragraphs.append((p_start, idx - 1, "\n".join(buf).strip()))
                buf = []
                p_start = 0
        else:
            if not buf:
                p_start = idx
            buf.append(line)
    if buf:
        paragraphs.append((p_start, len(lines), "\n".join(buf).strip()))

    s_block_names = ["HOOK", "DEFINICION", "EJEMPLO", "APLICACION_GANCHO"]
    sections: list[Section] = []
    for i, (ls, le, ptext) in enumerate(paragraphs):
        name = s_block_names[i] if i < len(s_block_names) else f"PARRAFO_{i + 1}"
        intervention = Intervention(
            speaker=None,
            tag=None,
            text=ptext,
            line_start=ls,
            line_end=le,
        )
        sections.append(
            Section(
                name=name,
                line_start=ls,
                line_end=le,
                interventions=[intervention],
            )
        )

    script = Script(filename=str(path), kind="S", raw_text=raw, sections=sections)
    _populate_metadata(script)
    return script


def _populate_metadata(script: Script) -> None:
    """Extrae opener, números de módulo/tema/s, etc."""
    name = Path(script.filename).name
    md: dict = {}

    if script.kind == "M":
        m = re.match(r"^M(\d{1,2})", name)
        if m:
            md["module_number"] = int(m.group(1))
    elif script.kind == "T":
        m = re.match(r"^M(\d{1,2})_T(\d{1,2})", name)
        if m:
            md["module_number"] = int(m.group(1))
            md["tema_number"] = int(m.group(2))
    elif script.kind == "S":
        m = re.match(r"^S(\d{1,3})", name)
        if m:
            md["s_number"] = int(m.group(1))

    # opener = primer speaker en la primera sección con intervenciones
    for sec in script.sections:
        for iv in sec.interventions:
            if iv.speaker:
                md["opener"] = iv.speaker
                break
        if "opener" in md:
            break

    md["word_count"] = script.total_word_count
    md["section_count"] = len(script.sections)
    script.metadata = md
