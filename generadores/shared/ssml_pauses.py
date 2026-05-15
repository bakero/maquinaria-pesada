"""Inserción de pausas SSML en el guion antes de enviar a TTS.

Audio-Regla 6 v6: entre bloques 800-1200ms, intra-bloque 400-600ms, fin de
HOOK 600ms, antes/después del aviso de IA 400ms, cambio de speaker 400-600ms.
"""
from __future__ import annotations

import re

DEFAULT_PAUSES_MS = {
    "between_blocks": 1000,
    "between_subtopics": 500,
    "after_hook": 600,
    "around_ia_warning": 400,
    "speaker_change": 500,
}


def _ssml(ms: int) -> str:
    return f'<break time="{ms}ms"/>'


def insert_block_pauses(script_text: str,
                        pauses_ms: dict | None = None) -> str:
    """Inserta una etiqueta SSML al final de cada sección y al final del HOOK.

    El TTS de ElevenLabs respeta `<break time="Xms"/>` tags si el modelo lo
    soporta; en caso contrario, son ignorados sin error.
    """
    p = dict(DEFAULT_PAUSES_MS)
    if pauses_ms:
        p.update(pauses_ms)

    pattern = re.compile(r"^#\s+([A-Z_]+)\s*$", re.MULTILINE)
    headings = list(pattern.finditer(script_text))
    if not headings:
        return script_text

    out_parts: list[str] = []
    last_end = 0
    for i, m in enumerate(headings):
        name = m.group(1)
        end_of_section = headings[i + 1].start() if i + 1 < len(headings) else len(script_text)
        # Texto antes de esta sección.
        out_parts.append(script_text[last_end:end_of_section])
        # Añade pausa al final de la sección.
        if name == "HOOK":
            pause = _ssml(p["after_hook"])
        elif i + 1 < len(headings):
            pause = _ssml(p["between_blocks"])
        else:
            pause = ""
        if pause:
            out_parts.append(f"\n{pause}\n")
        last_end = end_of_section
    out_parts.append(script_text[last_end:])
    return "".join(out_parts)


def insert_speaker_change_pauses(script_text: str,
                                  pause_ms: int = 500) -> str:
    """Inserta una pausa antes de cada cambio de speaker dentro de un bloque."""
    lines = script_text.split("\n")
    out: list[str] = []
    prev_speaker: str | None = None
    speaker_re = re.compile(r"^\s*(IAGO|MARIA|MARÍA)\s*:")
    for line in lines:
        m = speaker_re.match(line)
        if m:
            current = "MARIA" if m.group(1).upper() in ("MARIA", "MARÍA") else "IAGO"
            if prev_speaker and current != prev_speaker:
                out.append(_ssml(pause_ms))
            prev_speaker = current
        else:
            # Cabeceras de sección resetean el estado.
            if line.startswith("# "):
                prev_speaker = None
        out.append(line)
    return "\n".join(out)


def insert_all(script_text: str, pauses_ms: dict | None = None) -> str:
    """Aplica todas las inserciones de pausas SSML en orden seguro."""
    p = dict(DEFAULT_PAUSES_MS)
    if pauses_ms:
        p.update(pauses_ms)
    text = insert_block_pauses(script_text, p)
    text = insert_speaker_change_pauses(text, p["speaker_change"])
    return text
