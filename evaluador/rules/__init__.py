"""Reglas del evaluador organizadas por dimensión.

Las funciones públicas `evaluate_*` reciben un Script y devuelven list[Finding].
"""

from __future__ import annotations

from ..parser import Script
from .audio import evaluate_audio
from .base import Finding
from .cast import evaluate_cast
from .content import evaluate_content
from .m_specific import evaluate_m_specific
from .pedagogy import evaluate_pedagogy
from .s_specific import evaluate_s_specific
from .structure import evaluate_structure
from .t_specific import evaluate_t_specific


def evaluate_all(script: Script) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(evaluate_structure(script))
    findings.extend(evaluate_cast(script))
    findings.extend(evaluate_content(script))
    findings.extend(evaluate_audio(script))
    findings.extend(evaluate_pedagogy(script))
    if script.kind == "M":
        findings.extend(evaluate_m_specific(script))
    elif script.kind == "T":
        findings.extend(evaluate_t_specific(script))
    elif script.kind == "S":
        findings.extend(evaluate_s_specific(script))
    return findings
