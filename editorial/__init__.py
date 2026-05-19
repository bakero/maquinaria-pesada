"""Panel editorial de MaquinarIA Pesada.

Evalúa guiones como producto editorial (NO técnico). Cinco perspectivas:
Productor, Editor de marca, Oyente prototipo, Experto técnico, SEO/distribución.

Ver `EVALUADOR_EDITORIAL_GUIONES.md` (raíz del repo) para la documentación
normativa del panel.
"""
from __future__ import annotations

from editorial.benchmark import REFERENCE_CLUSTERS, ReferenceCluster
from editorial.perspectives import (
    PERSPECTIVE_WEIGHTS,
    PERSPECTIVES,
    Perspective,
    weights_for,
)
from editorial.report import EditorialReport, render_json, render_markdown
from editorial.scoring import EditorialIssue, EditorialVerdict, score_global, verdict_for

__all__ = [
    "PERSPECTIVES",
    "PERSPECTIVE_WEIGHTS",
    "Perspective",
    "weights_for",
    "REFERENCE_CLUSTERS",
    "ReferenceCluster",
    "EditorialReport",
    "EditorialIssue",
    "EditorialVerdict",
    "render_markdown",
    "render_json",
    "score_global",
    "verdict_for",
]
