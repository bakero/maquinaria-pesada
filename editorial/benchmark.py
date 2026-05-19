"""Mapa de referentes del panel editorial.

Fuente normativa: `EVALUADOR_EDITORIAL_GUIONES.md §5.1`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceCluster:
    """Un cluster de referentes editoriales."""

    label: str                     # "Top tier" / "Sólido sectorial" / ...
    score_min: float               # umbral inferior (inclusive)
    score_max: float               # umbral superior (inclusive)
    references: tuple[str, ...]    # referentes externos
    description: str               # rasgos clave del cluster


REFERENCE_CLUSTERS: tuple[ReferenceCluster, ...] = (
    ReferenceCluster(
        label="Top tier",
        score_min=9.0,
        score_max=10.0,
        references=("Lex Fridman AI", "Latent Space", "Dwarkesh Patel"),
        description=(
            "Profundidad técnica real, criterio editorial fuerte, voz humana, "
            "fuentes primarias."
        ),
    ),
    ReferenceCluster(
        label="Sólido sectorial",
        score_min=7.0,
        score_max=8.999,
        references=("Practical AI", "Hard Fork", "El Robot de Platón", "Nate Gentile"),
        description=(
            "Buena producción, ángulo claro, criterio, accesible sin ser "
            "superficial."
        ),
    ),
    ReferenceCluster(
        label="Estándar IA",
        score_min=5.0,
        score_max=6.999,
        references=("Mayoría de podcasts IA en español", "AI in Business"),
        description=(
            "Útil pero genérico, sin diferenciación clara, tono divulgativo "
            "amable."
        ),
    ),
    ReferenceCluster(
        label="Bajo",
        score_min=3.0,
        score_max=4.999,
        references=("Dot CSV", "Divulgación tipo YouTube IA en español promedio"),
        description="Clickbait visual, superficial, AI-bro mood.",
    ),
    ReferenceCluster(
        label="Crítico",
        score_min=1.0,
        score_max=2.999,
        references=("Podcasts coach-mode", "Contenido auto-generado sin criterio"),
        description="NotebookLM puro, sin postura, sin voz.",
    ),
)


def cluster_for(score: float) -> ReferenceCluster:
    """Devuelve el cluster que corresponde a un score 1-10 (1 decimal)."""
    for cluster in REFERENCE_CLUSTERS:
        if cluster.score_min <= score <= cluster.score_max:
            return cluster
    # Fallback defensivo: score <1 (no debería pasar).
    return REFERENCE_CLUSTERS[-1]
