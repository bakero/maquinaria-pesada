"""Dimensión 4 — Audio/TTS."""

from __future__ import annotations

import re

from ..parser import Script, split_sentences
from ..spec_data import TTS_TAGS_ALLOWED, normalize_tag
from .base import Finding, hard, soft

# Dígitos en texto hablado (ignorar dentro de [...] y <break/>, ya viene limpio en clean_text)
DIGITS_REGEX = re.compile(r"\b\d+(?:[\.,]\d+)?\b")

# Excepciones: años en nombres propios o modelos (GPT-4, T5, BERT-2024-style)
PROPER_NAME_BEFORE = re.compile(
    r"(GPT-?|Claude(?:\s+Sonnet|\s+Opus|\s+Haiku)?-?|Sonnet|Opus|Haiku|Llama-?|T5|BERT|Gemini|Sora-?|Flux-?|paper|informe|según|segun|estudio|McKinsey|Gartner|BCG|MIT|WEF|IDC|OpenAI|Anthropic|Stanford|versi[oó]n|v\.?)\s*$",
    re.IGNORECASE,
)

# Líneas de metadata legacy: `PALABRAS TOTALES : 3184 (objetivo: ...)` y similares
METADATA_LINE_REGEX = re.compile(
    r"^\s*(PALABRAS\s+TOTALES|DURACI[OÓ]N\s+ESTIMADA|TIEMPO\s+ESTIMADO|VERIFICAR|OBJETIVO|TOTAL)\b",
    re.IGNORECASE,
)


def evaluate_audio(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_digits_in_dialogue(script))
    findings.extend(_check_intervention_length(script))
    findings.extend(_check_sentence_length(script))
    findings.extend(_check_tts_tags(script))
    findings.extend(_check_ssml_breaks(script))
    return findings


def _check_digits_in_dialogue(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    for sec in script.sections:
        for iv in sec.interventions:
            # Para M/T saltar intervenciones sin speaker (metadata)
            if script.kind != "S" and iv.speaker is None:
                continue
            text = iv.clean_text
            # Saltar líneas de metadata legacy
            if METADATA_LINE_REGEX.match(text):
                continue
            for m in DIGITS_REGEX.finditer(text):
                # excepción: año precedido de nombre propio/contexto
                preceding = text[max(0, m.start() - 40) : m.start()]
                if PROPER_NAME_BEFORE.search(preceding):
                    continue
                # excepción: número pegado a un nombre con guion (T5, GPT-4)
                if m.start() > 0 and text[m.start() - 1] in "-.":
                    continue
                findings.append(
                    hard(
                        "audio_all_digits_in_dialogue",
                        f"Dígito '{m.group(0)}' en texto hablado (debe ir en palabras)",
                        line=iv.line_start,
                        speaker=iv.speaker,
                        section=sec.name,
                        snippet=text[max(0, m.start() - 20) : m.end() + 20],
                        autofixable=True,
                    )
                )
                break  # un finding por intervención
    return findings


def _check_intervention_length(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    if script.kind == "S":
        # S es prosa, se evalúa por bloque más adelante
        for sec in script.sections:
            for iv in sec.interventions:
                if iv.word_count > 60:
                    findings.append(
                        soft(
                            "s_intervention_over_60_words",
                            f"Párrafo-bloque {sec.name} con {iv.word_count} palabras (>60)",
                            line=iv.line_start,
                            section=sec.name,
                        )
                    )
        return findings

    # Secciones donde las intervenciones cortas son introducciones, no reacciones
    NON_REACTION_SECTIONS = {"SALUDO_Y_PRESENTACION", "INTRO_SONIDO", "CIERRE_FINAL"}

    for sec in script.sections:
        for iv in sec.interventions:
            if iv.speaker is None:
                continue  # metadata / comentarios no son intervenciones
            wc = iv.word_count
            sentences = iv.sentence_count
            if wc == 0:
                continue
            text = iv.clean_text.strip()
            if METADATA_LINE_REGEX.match(text):
                continue
            # Reacción real: 1 frase (≤2 frases si la 2ª es muy corta) Y suele ser
            # pregunta o reacción corta. Excluimos saludo/cierre.
            is_reaction = (
                sentences <= 2
                and wc <= 30
                and sec.name not in NON_REACTION_SECTIONS
                and (text.endswith("?") or sentences == 1)
            )
            if is_reaction and wc > 22:
                findings.append(
                    hard(
                        "audio_all_reaction_too_long",
                        f"Reacción/pregunta con {wc} palabras (>22)",
                        line=iv.line_start,
                        speaker=iv.speaker,
                        section=sec.name,
                    )
                )
            if not is_reaction:
                # APLICACION_PRACTICA momento 2 permite hasta 250
                limit_hard = 250 if sec.name == "APLICACION_PRACTICA" else 200
                if wc > limit_hard:
                    findings.append(
                        hard(
                            "audio_all_dev_over_200_words",
                            f"Intervención con {wc} palabras (>{limit_hard})",
                            line=iv.line_start,
                            speaker=iv.speaker,
                            section=sec.name,
                        )
                    )
                elif wc > 200 and sec.name != "APLICACION_PRACTICA":
                    findings.append(
                        soft(
                            "audio_all_dev_over_200_words",
                            f"Intervención con {wc} palabras (>200, soft)",
                            line=iv.line_start,
                            speaker=iv.speaker,
                            section=sec.name,
                        )
                    )
    return findings


def _check_sentence_length(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    limit = 28 if script.kind == "S" else 32
    code = (
        "audio_s_sentence_over_28_words"
        if script.kind == "S"
        else "audio_all_sentence_over_32_words"
    )
    sev = hard if script.kind == "S" else soft
    word_re = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+")
    for sec in script.sections:
        flagged_in_sec = 0
        for iv in sec.interventions:
            if script.kind != "S" and iv.speaker is None:
                continue
            if METADATA_LINE_REGEX.match(iv.clean_text):
                continue
            for sentence in split_sentences(iv.clean_text):
                wc = len(word_re.findall(sentence))
                if wc > limit:
                    findings.append(
                        sev(
                            code,
                            f"Frase de {wc} palabras (límite {limit})",
                            line=iv.line_start,
                            speaker=iv.speaker,
                            section=sec.name,
                            snippet=sentence[:80],
                        )
                    )
                    flagged_in_sec += 1
                    if flagged_in_sec >= 3:
                        break
            if flagged_in_sec >= 3:
                break
    return findings


def _check_tts_tags(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    if script.kind == "S":
        # S no admite etiquetas
        if re.search(r"[\[<](didactico|natural|conversacional)[\]>]", script.raw_text, re.IGNORECASE):
            findings.append(
                hard(
                    "audio_s_tts_tags_forbidden",
                    "S contiene etiquetas TTS (no permitidas)",
                )
            )
        return findings

    for sec in script.sections:
        for iv in sec.interventions:
            if iv.tag is None:
                continue
            tag_norm = normalize_tag(iv.tag)
            if tag_norm not in TTS_TAGS_ALLOWED:
                findings.append(
                    hard(
                        "audio_all_tag_not_allowed",
                        f"Etiqueta TTS '{iv.tag}' no está en el catálogo permitido",
                        line=iv.line_start,
                        speaker=iv.speaker,
                        section=sec.name,
                    )
                )

    # múltiples etiquetas al inicio: detectar 2+ corchetes/angulares antes del primer espacio relevante
    multi_tag_regex = re.compile(
        r"^(?:(?:IAGO|YAGO|MARIA|MAR[ÍI]A)\s*:\s*)?[\[<][^\]>]+[\]>]\s*[\[<][^\]>]+[\]>]",
        re.IGNORECASE | re.MULTILINE,
    )
    for m in multi_tag_regex.finditer(script.raw_text):
        line_no = script.raw_text.count("\n", 0, m.start()) + 1
        findings.append(
            hard(
                "audio_all_multiple_tags_per_intervention",
                "Más de una etiqueta TTS al inicio de la intervención",
                line=line_no,
            )
        )
    return findings


def _check_ssml_breaks(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    break_regex = re.compile(r'<break\s+time\s*=\s*"(\d+)(ms|s)"\s*/?>')
    for m in break_regex.finditer(script.raw_text):
        value = int(m.group(1))
        unit = m.group(2)
        ms = value * 1000 if unit == "s" else value
        if ms < 100 or ms > 2000:
            line_no = script.raw_text.count("\n", 0, m.start()) + 1
            findings.append(
                soft(
                    "audio_all_break_malformed",
                    f"<break time='{value}{unit}'/> fuera de [100ms, 2000ms]",
                    line=line_no,
                )
            )
    return findings
