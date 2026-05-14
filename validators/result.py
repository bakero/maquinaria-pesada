"""Resultado estructurado de validación.

Cada regla de validación devuelve uno o más `ValidationResult`. La separación
hard/soft es la misma del modelo de validación del proyecto: un `HARD` que no
pasa aborta la generación; un `SOFT` que no pasa solo advierte.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["HARD", "SOFT"]


@dataclass
class ValidationResult:
    """Resultado de aplicar una regla de validación a un guion o a un audio."""

    rule_name: str
    severity: Severity
    passed: bool
    message: str = ""
    context: dict = field(default_factory=dict)

    @property
    def is_blocking(self) -> bool:
        """True si este resultado debe abortar la generación (HARD no superado)."""
        return self.severity == "HARD" and not self.passed

    def to_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity,
            "passed": self.passed,
            "message": self.message,
            "context": self.context,
        }


def ok(rule_name: str, severity: Severity = "HARD", message: str = "",
       **context) -> ValidationResult:
    """Atajo: resultado superado."""
    return ValidationResult(rule_name, severity, True, message, context)


def fail(rule_name: str, severity: Severity, message: str,
         **context) -> ValidationResult:
    """Atajo: resultado no superado."""
    return ValidationResult(rule_name, severity, False, message, context)


def summarize(results: list[ValidationResult]) -> dict:
    """Resume una lista de resultados: contadores y si hay bloqueos."""
    hard_failed = [r for r in results if r.severity == "HARD" and not r.passed]
    soft_failed = [r for r in results if r.severity == "SOFT" and not r.passed]
    return {
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "hard_failed": len(hard_failed),
        "soft_failed": len(soft_failed),
        "blocking": len(hard_failed) > 0,
        "hard_failures": [r.rule_name for r in hard_failed],
        "soft_warnings": [r.rule_name for r in soft_failed],
    }
