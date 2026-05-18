"""Dimensión 1 — Estructura."""

from __future__ import annotations

import re

from ..parser import Script
from ..spec_data import (
    CIERRE_CONCEPTOS_OPENER,
    CIERRE_FINAL_LITERAL,
    FORBIDDEN_LEGACY_SECTIONS,
    HOOK_CLOSING_PHRASE,
    INTRO_COMMENT_PATTERN,
    M_REQUIRED_SECTIONS,
    S_CLOSING_REGEX,
    T_FORBIDDEN_SECTIONS,
    T_REALIDAD_ALIASES,
    T_REQUIRED_SECTIONS,
)
from .base import Finding, hard, soft

# Helpers de normalización de texto

_ACCENT_MAP = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


def _norm(text: str) -> str:
    return text.translate(_ACCENT_MAP).lower()


def evaluate_structure(script: Script) -> list[Finding]:
    if script.kind == "S":
        return _evaluate_structure_s(script)
    if script.kind == "M":
        return _evaluate_structure_m(script)
    if script.kind == "T":
        return _evaluate_structure_t(script)
    return []


def _check_required_in_order(
    present: list[str], required: list[str]
) -> tuple[list[str], list[str]]:
    """Devuelve (missing, out_of_order). out_of_order es la lista de secciones
    que están presentes pero fuera del orden esperado."""
    missing = [r for r in required if r not in present]
    out_of_order: list[str] = []
    # filtra present a sólo required sections, verifica que estén en orden
    present_req = [p for p in present if p in required]
    expected_order = [r for r in required if r in present]
    if present_req != expected_order:
        # encontrar qué secciones rompen el orden
        for i, name in enumerate(present_req):
            if i < len(expected_order) and name != expected_order[i]:
                out_of_order.append(name)
    return missing, out_of_order


def _evaluate_structure_m(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    present = script.section_names()

    # forbidden legacy
    for sec in script.sections:
        if sec.name in FORBIDDEN_LEGACY_SECTIONS:
            findings.append(
                hard(
                    "struct_t_forbidden_section_legacy",
                    f"Sección legacy '{sec.name}' presente (estructura no-v6)",
                    line=sec.line_start,
                    section=sec.name,
                )
            )

    missing, ooo = _check_required_in_order(present, M_REQUIRED_SECTIONS)
    for m in missing:
        findings.append(
            hard(
                "struct_all_missing_section",
                f"Falta sección obligatoria '{m}'",
                section=m,
            )
        )
    for s in ooo:
        sec = script.section_by_name(s)
        findings.append(
            hard(
                "struct_all_section_out_of_order",
                f"Sección '{s}' fuera de orden",
                line=sec.line_start if sec else None,
                section=s,
            )
        )

    findings.extend(_check_canonical_phrases(script))
    findings.extend(_check_saludo_three_blocks(script))
    findings.extend(_check_m_cierre_cta(script))
    return findings


def _evaluate_structure_t(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    present = script.section_names()

    for sec in script.sections:
        if sec.name in FORBIDDEN_LEGACY_SECTIONS:
            findings.append(
                hard(
                    "struct_t_forbidden_section_legacy",
                    f"Sección legacy '{sec.name}' presente (estructura no-v6)",
                    line=sec.line_start,
                    section=sec.name,
                )
            )
        if sec.name in T_FORBIDDEN_SECTIONS:
            findings.append(
                hard(
                    "struct_t_forbidden_section_aplicacion",
                    f"T contiene '{sec.name}' (exclusivo de M)",
                    line=sec.line_start,
                    section=sec.name,
                )
            )

    # Normalizar BLOQUE_CASOS → BLOQUE_REALIDAD para la verificación de orden
    present_norm = [
        "BLOQUE_REALIDAD" if p in T_REALIDAD_ALIASES else p for p in present
    ]
    missing, ooo = _check_required_in_order(present_norm, T_REQUIRED_SECTIONS)
    for m in missing:
        findings.append(
            hard(
                "struct_all_missing_section",
                f"Falta sección obligatoria '{m}'"
                + (" (acepta también BLOQUE_CASOS)" if m == "BLOQUE_REALIDAD" else ""),
                section=m,
            )
        )
    for s in ooo:
        sec = script.section_by_name(s) or script.section_by_name(
            "BLOQUE_CASOS" if s == "BLOQUE_REALIDAD" else s
        )
        findings.append(
            hard(
                "struct_all_section_out_of_order",
                f"Sección '{s}' fuera de orden",
                line=sec.line_start if sec else None,
                section=s,
            )
        )

    findings.extend(_check_canonical_phrases(script))
    findings.extend(_check_saludo_three_blocks(script))
    return findings


def _evaluate_structure_s(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    n_blocks = len(script.sections)
    if n_blocks != 4:
        findings.append(
            hard(
                "struct_s_block_count",
                f"S tiene {n_blocks} párrafos-bloque, debe tener exactamente 4",
            )
        )
        return findings  # sin 4 bloques no podemos evaluar el resto

    # cierre literal del último párrafo
    last = script.sections[-1].interventions[0].text.strip()
    last_line = last.splitlines()[-1] if last else ""
    if not S_CLOSING_REGEX.search(last_line):
        findings.append(
            hard(
                "struct_s_closing_literal",
                "Última frase no encaja con plantilla 'Más sobre [tema] en el episodio T de MaquinarIA Pesada.'",
                line=script.sections[-1].line_end,
            )
        )
    return findings


def _check_canonical_phrases(script: Script) -> list[Finding]:
    """HOOK closing, INTRO_SONIDO marker, CIERRE_CONCEPTOS opener, CIERRE_FINAL literal."""
    findings: list[Finding] = []

    hook = script.section_by_name("HOOK")
    if hook:
        # cierre del HOOK
        hook_text = " ".join(iv.clean_text for iv in hook.interventions)
        if _norm(HOOK_CLOSING_PHRASE) not in _norm(hook_text):
            findings.append(
                hard(
                    "struct_all_hook_closing",
                    f"HOOK no cierra con '{HOOK_CLOSING_PHRASE}'",
                    line=hook.line_start,
                    section="HOOK",
                )
            )

    intro = script.section_by_name("INTRO_SONIDO")
    if intro:
        if not INTRO_COMMENT_PATTERN.search(intro.interventions[0].text if intro.interventions else ""):
            # buscar también en el bloque completo (puede estar tras un speaker)
            raw_block = "\n".join(iv.text for iv in intro.interventions)
            if not INTRO_COMMENT_PATTERN.search(raw_block):
                findings.append(
                    hard(
                        "struct_all_intro_sonido_marker",
                        "INTRO_SONIDO sin comentario '[INTRO - SONIDO ...]'",
                        line=intro.line_start,
                        section="INTRO_SONIDO",
                    )
                )

    cierre_c = script.section_by_name("CIERRE_CONCEPTOS")
    if cierre_c:
        text = " ".join(iv.clean_text for iv in cierre_c.interventions)
        if _norm(CIERRE_CONCEPTOS_OPENER) not in _norm(text):
            findings.append(
                hard(
                    "struct_all_cierre_conceptos_open",
                    f"CIERRE_CONCEPTOS no abre con '{CIERRE_CONCEPTOS_OPENER}'",
                    line=cierre_c.line_start,
                    section="CIERRE_CONCEPTOS",
                )
            )

    cierre_f = script.section_by_name("CIERRE_FINAL")
    if cierre_f:
        text = " ".join(iv.clean_text for iv in cierre_f.interventions)
        if _norm(CIERRE_FINAL_LITERAL) not in _norm(text):
            findings.append(
                hard(
                    "struct_all_cierre_final_literal",
                    "CIERRE_FINAL no contiene la cita canónica completa",
                    line=cierre_f.line_start,
                    section="CIERRE_FINAL",
                )
            )

    return findings


def _check_saludo_three_blocks(script: Script) -> list[Finding]:
    """SALUDO_Y_PRESENTACION debe tener ≥3 intervenciones (no colapsado en 1-2)."""
    saludo = script.section_by_name("SALUDO_Y_PRESENTACION")
    if not saludo:
        return []
    speaker_interventions = [iv for iv in saludo.interventions if iv.speaker]
    if len(speaker_interventions) < 3:
        return [
            hard(
                "struct_saludo_three_blocks",
                f"SALUDO_Y_PRESENTACION con {len(speaker_interventions)} intervenciones (mínimo 3)",
                line=saludo.line_start,
                section="SALUDO_Y_PRESENTACION",
            )
        ]
    return []


def _check_m_cierre_cta(script: Script) -> list[Finding]:
    """M sin CTA detectada en CIERRE_FINAL (soft)."""
    cierre = script.section_by_name("CIERRE_FINAL")
    if not cierre:
        return []
    text = " ".join(iv.clean_text for iv in cierre.interventions)
    cta_regex = re.compile(
        r"episodios?[^\n]{0,80}(módulo|modulo|disponible|plataforma|escucha|sigu|próxim|proxim)",
        re.IGNORECASE,
    )
    if not cta_regex.search(text):
        return [
            soft(
                "struct_m_cierre_final_cta",
                "M sin CTA detectada en CIERRE_FINAL",
                line=cierre.line_start,
                section="CIERRE_FINAL",
            )
        ]
    return []
