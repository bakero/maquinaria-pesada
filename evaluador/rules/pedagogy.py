"""Dimensión 5 — Pedagogía (chequeo básico)."""

from __future__ import annotations

import re

from ..parser import Script
from ..spec_data import PEDAGOGY_ANALOGY_MARKERS, PEDAGOGY_COMPLEX_TERMS
from .base import Finding, soft


def evaluate_pedagogy(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    if script.kind == "S":
        return findings  # las S se evalúan con s_anglicismo en s_specific
    findings.extend(_check_complex_concepts_landing(script))
    return findings


def _check_complex_concepts_landing(script: Script) -> list[Finding]:
    """Concepto técnico complejo sin marcador de analogía en las 6 frases siguientes."""
    findings: list[Finding] = []
    interventions = script.all_interventions
    full_text_segments: list[tuple[int, str, int]] = []  # (idx_intervention, text, line)

    for i, iv in enumerate(interventions):
        full_text_segments.append((i, iv.clean_text, iv.line_start))

    # Construir un buffer de 6 frases siguientes en intervenciones contiguas
    for i, iv in enumerate(interventions):
        if script.kind != "S" and iv.speaker is None:
            continue
        text = iv.clean_text
        for term in PEDAGOGY_COMPLEX_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE):
                # buscar marcador de analogía en este texto + siguientes 6 frases
                window = text
                for j in range(i + 1, min(i + 3, len(interventions))):
                    window += " " + interventions[j].clean_text
                if not any(
                    re.search(rf"\b{re.escape(m)}", window, re.IGNORECASE)
                    for m in PEDAGOGY_ANALOGY_MARKERS
                ):
                    findings.append(
                        soft(
                            "pedagogy_all_complex_concept_no_analogy",
                            f"Término complejo '{term}' sin marcador de analogía en ventana",
                            line=iv.line_start,
                            speaker=iv.speaker,
                        )
                    )
                break  # un finding por intervención
    return findings
