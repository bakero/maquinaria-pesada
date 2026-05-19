"""Dimensión 3 — Contenido (word count y referencias temporales)."""

from __future__ import annotations

import re

from ..parser import Script
from ..spec_data import WORD_COUNT_RANGES
from .base import Finding, hard, soft


def evaluate_content(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_word_count(script))
    findings.extend(_check_temporal_references(script))
    return findings


def _check_word_count(script: Script) -> list[Finding]:
    minw, maxw = WORD_COUNT_RANGES.get(script.kind, (0, 10**9))
    total = script.total_word_count
    if total < minw or total > maxw:
        return [
            hard(
                "content_all_word_count_out_of_range",
                f"Word count {total} fuera de [{minw}, {maxw}] para tipo {script.kind}",
            )
        ]
    return []


def _check_temporal_references(script: Script) -> list[Finding]:
    """Año 2024/2025 sin contexto de publicación previo."""
    findings: list[Finding] = []
    year_regex = re.compile(r"\b(20\d{2})\b")
    context_markers = re.compile(
        r"(paper|informe|según|segun|estudio|reporte|publicad[oa]|estadística|estadisticas|McKinsey|Gartner|BCG|MIT|WEF|IDC|Stanford|OpenAI|menlo|investigaci[oó]n)",
        re.IGNORECASE,
    )
    for sec in script.sections:
        for iv in sec.interventions:
            if script.kind != "S" and iv.speaker is None:
                continue
            text = iv.clean_text
            for m in year_regex.finditer(text):
                window = text[max(0, m.start() - 80) : m.start()]
                if not context_markers.search(window):
                    findings.append(
                        soft(
                            "content_all_temporal_reference_no_context",
                            f"Año '{m.group(1)}' sin contexto de publicación previo",
                            line=iv.line_start,
                            speaker=iv.speaker,
                            section=sec.name,
                            snippet=text[max(0, m.start() - 30) : m.end() + 30],
                        )
                    )
                    break  # un finding por intervención basta
            else:
                continue
            break
    return findings
