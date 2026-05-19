"""Dimensión 6 — Específicos M."""

from __future__ import annotations

import re

from ..parser import Script
from .base import Finding, hard, soft


def evaluate_m_specific(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_aplicacion_in_hook(script))
    findings.extend(_check_aplicacion_material(script))
    findings.extend(_check_concepts_count(script))
    findings.extend(_check_fuentes_block(script))
    findings.extend(_check_hook_duration(script))
    return findings


def _check_aplicacion_in_hook(script: Script) -> list[Finding]:
    hook = script.section_by_name("HOOK")
    if not hook:
        return []
    text = " ".join(iv.clean_text for iv in hook.interventions)
    # heurística: si el HOOK menciona "el sistema que genera este podcast" o similar
    if re.search(r"sistema que (?:produce|genera) este podcast", text, re.IGNORECASE):
        return [
            hard(
                "m_aplicacion_in_hook",
                "APLICACION_PRACTICA mencionada en HOOK (debe ir solo en bloque APLICACION_PRACTICA)",
                line=hook.line_start,
                section="HOOK",
            )
        ]
    return []


def _check_aplicacion_material(script: Script) -> list[Finding]:
    sec = script.section_by_name("APLICACION_PRACTICA")
    if not sec:
        return []
    text = " ".join(iv.clean_text for iv in sec.interventions).lower()
    has_problem = bool(re.search(r"problem[ao]|reto|desaf[ií]o|fall[aó]", text))
    has_decision = bool(re.search(r"decidim|decisi[oó]n|elegim|optam|escog", text))
    has_number = bool(re.search(r"\b\d+|\b(cero|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|veint|treint|cuarent|cincuent|sesent|setent|ochent|novent|cien)", text))
    missing = []
    if not has_problem:
        missing.append("problema concreto")
    if not has_decision:
        missing.append("decisión técnica")
    if not has_number:
        missing.append("cifra verificable")
    if missing:
        return [
            hard(
                "m_aplicacion_insufficient_material",
                f"APLICACION_PRACTICA sin {', '.join(missing)} (heurística)",
                line=sec.line_start,
                section="APLICACION_PRACTICA",
            )
        ]
    return []


def _check_concepts_count(script: Script) -> list[Finding]:
    sec = script.section_by_name("CIERRE_CONCEPTOS")
    if not sec:
        return []
    # Contar conceptos enumerados (primero, segundo, ..., o "uno:", "dos:", o números)
    text = " ".join(iv.clean_text for iv in sec.interventions)
    enumerators = re.findall(
        r"\b(primer[oa]|segund[oa]|tercer[oa]|cuart[oa]|quint[oa]|sext[oa])\b",
        text,
        re.IGNORECASE,
    )
    count = len(set(e.lower()[:5] for e in enumerators))
    if count < 3 or count > 5:
        return [
            hard(
                "m_concepts_count_out_of_range",
                f"CIERRE_CONCEPTOS con {count} conceptos detectados (rango 3-5)",
                line=sec.line_start,
                section="CIERRE_CONCEPTOS",
            )
        ]
    return []


def _check_fuentes_block(script: Script) -> list[Finding]:
    if not script.section_by_name("BLOQUE_FUENTES"):
        return [
            hard(
                "m_fuentes_block_present",
                "Falta BLOQUE_FUENTES (obligatorio en M v6)",
            )
        ]
    return []


def _check_hook_duration(script: Script) -> list[Finding]:
    hook = script.section_by_name("HOOK")
    if not hook:
        return []
    wc = hook.word_count
    # ~3 wps a 1.32× → 3 wps * 30s = 90 palabras (mín), * 45s = 135
    if wc < 75 or wc > 200:
        return [
            soft(
                "m_hook_duration_estimate",
                f"HOOK de {wc} palabras (estimado fuera de 30-45s; rango palabras 90-160)",
                line=hook.line_start,
                section="HOOK",
            )
        ]
    return []
