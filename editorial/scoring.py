"""Score editorial ponderado y veredicto en 3 niveles.

Fuente normativa: `EVALUADOR_EDITORIAL_GUIONES.md §4`.

Veredicto:
    PUBLICAR  ✅  score ≥ 7.5  Y  0 críticos  EN NINGUNA perspectiva
    REVISAR   🟡  6.0 ≤ score < 7.5  O  1-2 críticos (sin asimetría de marca)
    BLOQUEAR  🔴  score < 6.0  O  ≥3 críticos  O  ≥1 crítico en MARCA

Asimetría intencional confirmada (desempate 2026-05-19): un issue crítico
en la perspectiva *Editor de marca* basta para bloquear, aunque el resto
puntúe ≥9.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from editorial.perspectives import PERSPECTIVE_WEIGHTS

Severity = Literal["critico", "relevante", "menor"]
Verdict = Literal["PUBLICAR", "REVISAR", "BLOQUEAR"]


@dataclass
class EditorialIssue:
    severity: Severity
    perspective: str       # "productor" | "marca" | "oyente" | "experto" | "seo"
    axis: str              # eje afectado
    problem: str           # frase del problema en el guion
    proposal: str          # acción concreta de cambio

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "perspective": self.perspective,
            "axis": self.axis,
            "problem": self.problem,
            "proposal": self.proposal,
        }


@dataclass
class PerspectiveScore:
    """Score y rationale de una perspectiva."""

    perspective_key: str
    score: float            # 1-10
    rationale: str
    issues: list[EditorialIssue] = field(default_factory=list)


@dataclass
class EditorialVerdict:
    verdict: Verdict
    score_global: float     # 1-10 con 1 decimal
    reasons: list[str] = field(default_factory=list)


def score_global(perspective_scores: dict[str, float], kind: str) -> float:
    """Calcula el score global ponderado para un tipo de guion.

    `perspective_scores`: mapa {perspective_key: score 1-10}.
    `kind`: "M" | "T" | "S".
    Devuelve el score 1-10 con un decimal.
    """
    weights = PERSPECTIVE_WEIGHTS[kind]
    total = 0.0
    weight_sum = 0.0
    for key, weight in weights.items():
        if weight <= 0.0:
            continue
        if key not in perspective_scores:
            continue
        total += perspective_scores[key] * weight
        weight_sum += weight
    if weight_sum == 0:
        return 0.0
    return round(total / weight_sum, 1)


def has_brand_critical(issues: list[EditorialIssue]) -> bool:
    """¿Hay al menos un issue crítico en la perspectiva *Editor de marca*?"""
    return any(
        i.severity == "critico" and i.perspective == "marca"
        for i in issues
    )


def count_critical(issues: list[EditorialIssue]) -> int:
    return sum(1 for i in issues if i.severity == "critico")


def verdict_for(score: float, issues: list[EditorialIssue]) -> EditorialVerdict:
    """Aplica los criterios del §4.3 + asimetría de marca."""
    reasons: list[str] = []

    n_critical = count_critical(issues)
    brand_crit = has_brand_critical(issues)

    if brand_crit:
        reasons.append(
            "Issue crítico en perspectiva 'Editor de marca' → BLOQUEAR "
            "(asimetría editorial)"
        )
        return EditorialVerdict(verdict="BLOQUEAR", score_global=score,
                                reasons=reasons)

    if score < 6.0 or n_critical >= 3:
        reasons.append(
            f"score {score} < 6.0" if score < 6.0
            else f"{n_critical} issues críticos (≥3)"
        )
        return EditorialVerdict(verdict="BLOQUEAR", score_global=score,
                                reasons=reasons)

    if score < 7.5 or n_critical >= 1:
        reasons.append(
            f"score {score} en banda REVISAR" if score < 7.5
            else f"{n_critical} issues críticos (1-2)"
        )
        return EditorialVerdict(verdict="REVISAR", score_global=score,
                                reasons=reasons)

    return EditorialVerdict(verdict="PUBLICAR", score_global=score,
                            reasons=["score ≥ 7.5 y sin issues críticos"])
