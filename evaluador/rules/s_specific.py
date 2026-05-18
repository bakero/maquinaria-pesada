"""Dimensión 8 — Específicos S."""

from __future__ import annotations

import re

from ..parser import Script
from ..spec_data import S_CLOSING_REGEX
from .base import Finding, hard, soft

# Word targets por bloque interno
S_BLOCK_TARGETS = {
    "HOOK": (12, 18),
    "DEFINICION": (45, 55),
    "EJEMPLO": (70, 85),
    "APLICACION_GANCHO": (30, 40),
}


def evaluate_s_specific(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    if len(script.sections) != 4:
        return []  # ya reportado por struct_s_block_count
    findings.extend(_check_block_word_targets(script))
    findings.extend(_check_hook_template(script))
    findings.extend(_check_closing(script))
    findings.extend(_check_brand_outside_closing(script))
    findings.extend(_check_url_in_speech(script))
    findings.extend(_check_paper_citation(script))
    findings.extend(_check_dialogue_forbidden(script))
    return findings


def _check_block_word_targets(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    for sec, (mn, mx) in zip(script.sections, S_BLOCK_TARGETS.values(), strict=False):
        wc = sec.word_count
        if wc < mn or wc > mx:
            findings.append(
                hard(
                    "s_block_word_targets",
                    f"Bloque {sec.name}: {wc} palabras (rango {mn}-{mx})",
                    line=sec.line_start,
                    section=sec.name,
                )
            )
    return findings


def _check_hook_template(script: Script) -> list[Finding]:
    hook = script.sections[0]
    text = hook.interventions[0].clean_text.strip() if hook.interventions else ""
    # H3: pregunta (acaba en ?)
    # H2: número (dígitos o palabra-número en los primeros caracteres)
    # H1: contradicción (resto)
    ok = False
    if text.endswith("?"):
        ok = True  # H3
    if re.search(r"\b\d+", text[:80]) or re.search(
        r"\b(uno|dos|tres|cuatro|cinco|cien|mil|veinte|treinta|cuarenta|cincuenta|ochenta|noventa)\b",
        text[:80],
        re.IGNORECASE,
    ):
        ok = True  # H2
    if "pero" in text.lower() or "sin embargo" in text.lower() or "aunque" in text.lower():
        ok = True  # H1 (heurística)
    if not ok:
        return [
            hard(
                "s_hook_template_missing",
                "HOOK no encaja en plantilla H1 (contradicción) / H2 (número) / H3 (pregunta)",
                line=hook.line_start,
                section="HOOK",
            )
        ]
    return []


def _check_closing(script: Script) -> list[Finding]:
    last = script.sections[-1].interventions[0].text.strip()
    last_line = last.splitlines()[-1] if last else ""
    if not S_CLOSING_REGEX.search(last_line):
        return [
            hard(
                "s_closing_phrase_literal",
                "Última frase ≠ 'Más sobre [tema] en el episodio T de MaquinarIA Pesada.'",
                line=script.sections[-1].line_end,
            )
        ]
    return []


def _check_brand_outside_closing(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    for idx, sec in enumerate(script.sections):
        for iv in sec.interventions:
            text = iv.clean_text
            if "MaquinarIA Pesada" in text or "maquinaria pesada" in text.lower():
                # último párrafo permitido si es el cierre
                if idx == len(script.sections) - 1:
                    continue
                findings.append(
                    soft(
                        "s_brand_outside_closing",
                        "'MaquinarIA Pesada' aparece fuera del cierre",
                        line=iv.line_start,
                        section=sec.name,
                    )
                )
                break
    return findings


def _check_url_in_speech(script: Script) -> list[Finding]:
    if re.search(r"https?://|www\.", script.raw_text):
        return [hard("s_url_in_speech", "URL en texto del guion (prohibido en S)")]
    return []


def _check_paper_citation(script: Script) -> list[Finding]:
    # heurística simple: "et al" o nombre + año entre paréntesis
    if re.search(r"\bet al\.?", script.raw_text, re.IGNORECASE) or re.search(
        r"\b[A-Z][a-z]+\s*\(\s*20\d{2}\s*\)", script.raw_text
    ):
        return [
            hard(
                "s_paper_citation_in_speech",
                "Cita académica explícita detectada (autor/año/et al)",
            )
        ]
    return []


def _check_dialogue_forbidden(script: Script) -> list[Finding]:
    # detectar atribuciones tipo —X dijo—, "preguntó", "respondió", etc. (heurística suave)
    if re.search(
        r"^(IAGO|YAGO|MARIA|MAR[ÍI]A)\s*:", script.raw_text, re.MULTILINE | re.IGNORECASE
    ):
        return [
            hard(
                "s_dialogue_forbidden",
                "S contiene atribución de speaker (diálogo prohibido)",
            )
        ]
    return []
