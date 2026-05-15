"""Parseo del formato de guion `# SECCION` + `SPEAKER: [tag] texto`.

Estructura compartida que consumen el validador base y los especialistas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

SECTION_RE = re.compile(r"^#\s+([A-Z_]+)\s*$", re.MULTILINE)
LINE_RE = re.compile(
    # Aceptamos IAGO (canónico), YAGO (variante hablada), MARIA y MARÍA.
    r"^\s*(?P<speaker>IAGO|YAGO|MARIA|MARÍA)\s*:\s*(?P<body>.*?)\s*$",
    re.MULTILINE,
)


@dataclass
class Intervention:
    speaker: str           # "IAGO" o "MARIA"
    text: str              # cuerpo completo de la intervención (con [tag] inicial)
    section: str           # nombre de la sección donde aparece


@dataclass
class ScriptParts:
    """Guion parseado: secciones, intervenciones por sección y texto completo."""

    sections: dict[str, str] = field(default_factory=dict)
    interventions_by_section: dict[str, list[Intervention]] = field(default_factory=dict)
    all_interventions: list[Intervention] = field(default_factory=list)
    full_text: str = ""
    section_order: list[str] = field(default_factory=list)

    def section_text(self, name: str) -> str:
        return self.sections.get(name, "")

    def interventions(self, section: str | None = None) -> list[Intervention]:
        if section is None:
            return self.all_interventions
        return self.interventions_by_section.get(section, [])

    def intervention_texts(self, section: str | None = None) -> list[str]:
        return [i.text for i in self.interventions(section)]

    def first_speaker_of(self, section: str) -> str | None:
        ints = self.interventions(section)
        return ints[0].speaker if ints else None


def _normalize_speaker(raw: str) -> str:
    up = raw.upper()
    if up in ("IAGO", "YAGO"):
        return "IAGO"
    return "MARIA"


def parse_script(text: str) -> ScriptParts:
    """Parsea un guion en su estructura de secciones e intervenciones.

    Reglas:
    - Las secciones empiezan con `# NOMBRE_SECCION` en una línea propia.
    - Las intervenciones tienen formato `SPEAKER: [tag] texto`, donde el [tag]
      es opcional.
    - El texto de la intervención puede continuar en líneas siguientes hasta
      la siguiente cabecera de speaker o de sección.
    """
    parts = ScriptParts(full_text=text)

    # Encuentra cabeceras de sección con sus posiciones.
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return parts

    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        parts.sections[name] = body
        parts.section_order.append(name)
        parts.interventions_by_section[name] = []

        # Parseo de intervenciones dentro del body.
        # Encontramos cada cabecera "SPEAKER:" y tomamos el cuerpo hasta la
        # siguiente cabecera de speaker.
        speaker_iter = list(LINE_RE.finditer(body))
        for j, sm in enumerate(speaker_iter):
            spk = _normalize_speaker(sm.group("speaker"))
            inter_start = sm.start("body")
            inter_end = (
                speaker_iter[j + 1].start() if j + 1 < len(speaker_iter)
                else len(body)
            )
            inter_text = body[inter_start:inter_end].strip()
            iv = Intervention(speaker=spk, text=inter_text, section=name)
            parts.interventions_by_section[name].append(iv)
            parts.all_interventions.append(iv)

    return parts


def count_words(text: str) -> int:
    """Cuenta palabras (sin tags TTS), usado por validadores de longitud."""
    no_tags = re.sub(r"^\s*\[[^\]]+\]\s*", "", text)
    return len(re.findall(r"\b[\wáéíóúñÁÉÍÓÚÑ]+\b", no_tags))


def speaker_share(interventions: list[Intervention], speaker: str) -> float:
    """Porcentaje de palabras del speaker indicado sobre el total de la lista."""
    if not interventions:
        return 0.0
    total = sum(count_words(i.text) for i in interventions)
    if total == 0:
        return 0.0
    own = sum(count_words(i.text) for i in interventions if i.speaker == speaker)
    return own / total
