"""Dimensión 7 — Específicos T."""

from __future__ import annotations

import re

from ..parser import Script
from .base import Finding, hard, soft


def evaluate_t_specific(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_no_aplicacion(script))
    findings.extend(_check_concepts_3(script))
    findings.extend(_check_realidad_elements(script))
    findings.extend(_check_fuentes_block(script))
    findings.extend(_check_realidad_maria_intervenciones(script))
    findings.extend(_check_hook_duration(script))
    return findings


def _check_no_aplicacion(script: Script) -> list[Finding]:
    if script.section_by_name("APLICACION_PRACTICA"):
        return [
            hard(
                "t_no_aplicacion_practica",
                "T contiene APLICACION_PRACTICA (prohibido)",
            )
        ]
    return []


def _check_concepts_3(script: Script) -> list[Finding]:
    sec = script.section_by_name("CIERRE_CONCEPTOS")
    if not sec:
        return []
    text = " ".join(iv.clean_text for iv in sec.interventions)
    enumerators = set(
        e.lower()[:5]
        for e in re.findall(
            r"\b(primer[oa]|segund[oa]|tercer[oa]|cuart[oa]|quint[oa])\b",
            text,
            re.IGNORECASE,
        )
    )
    if len(enumerators) != 3:
        return [
            hard(
                "t_concepts_count_not_3",
                f"CIERRE_CONCEPTOS con {len(enumerators)} conceptos detectados (T exige exactamente 3)",
                line=sec.line_start,
                section="CIERRE_CONCEPTOS",
            )
        ]
    return []


def _check_realidad_elements(script: Script) -> list[Finding]:
    sec = script.section_by_name("BLOQUE_REALIDAD") or script.section_by_name(
        "BLOQUE_CASOS"
    )
    if not sec:
        return []
    text = " ".join(iv.clean_text for iv in sec.interventions)

    has_dato = bool(
        re.search(
            r"\b(Gartner|McKinsey|WEF|IDC|MIT|Stanford|BCG|Forrester|Deloitte|menlo)\b",
            text,
            re.IGNORECASE,
        )
    )
    has_empresa = bool(
        re.search(
            r"\b(JPMorgan|Google|Microsoft|Amazon|Meta|Apple|OpenAI|Anthropic|Tesla|Walmart|Siemens|Bosch|Salesforce|Adobe|Netflix|Uber|Airbnb|Spotify|IBM)\b",
            text,
        )
    )
    has_reto = bool(re.search(r"\b(reto|desaf[ií]o|obst[aá]culo|barrera|dificultad)", text, re.IGNORECASE))
    has_oport = bool(
        re.search(
            r"\b(oportunidad|negocio|revenue|ingreso|ahorro|valor|ROI|productividad)",
            text,
            re.IGNORECASE,
        )
    )
    present = sum([has_dato, has_empresa, has_reto, has_oport])
    if present < 2:
        return [
            hard(
                "t_realidad_min_elements",
                f"BLOQUE_REALIDAD/CASOS sin 2 de 4 elementos (dato/empresa/reto/oportunidad): {present} detectados",
                line=sec.line_start,
                section=sec.name,
            )
        ]
    return []


def _check_fuentes_block(script: Script) -> list[Finding]:
    if not script.section_by_name("BLOQUE_FUENTES"):
        return [
            hard(
                "t_fuentes_block_present",
                "Falta BLOQUE_FUENTES (obligatorio en T v6)",
            )
        ]
    return []


def _check_realidad_maria_intervenciones(script: Script) -> list[Finding]:
    sec = script.section_by_name("BLOQUE_REALIDAD") or script.section_by_name(
        "BLOQUE_CASOS"
    )
    if not sec:
        return []
    maria_devs = [
        iv for iv in sec.interventions if iv.speaker == "MARIA" and iv.word_count > 30
    ]
    if len(maria_devs) < 5:
        return [
            hard(
                "t_realidad_maria_intervenciones",
                f"Maria con {len(maria_devs)} intervenciones de desarrollo en {sec.name} (mínimo 5)",
                line=sec.line_start,
                section=sec.name,
            )
        ]
    return []


def _check_hook_duration(script: Script) -> list[Finding]:
    hook = script.section_by_name("HOOK")
    if not hook:
        return []
    wc = hook.word_count
    if wc < 75 or wc > 200:
        return [
            soft(
                "t_hook_duration_estimate",
                f"HOOK de {wc} palabras (estimado fuera de 30-45s)",
                line=hook.line_start,
                section="HOOK",
            )
        ]
    return []
