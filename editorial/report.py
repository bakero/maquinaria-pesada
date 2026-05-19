"""Generación del reporte editorial en Markdown y JSON.

Fuente normativa: `EVALUADOR_EDITORIAL_GUIONES.md §6.3`.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from editorial.benchmark import cluster_for
from editorial.perspectives import PERSPECTIVES
from editorial.scoring import EditorialIssue, EditorialVerdict


@dataclass
class PerspectiveBlock:
    """Bloque de output de una perspectiva."""

    perspective_key: str           # "productor", "marca", ...
    score: float                   # 1-10
    rationale: str                 # 1 línea
    issues: list[EditorialIssue] = field(default_factory=list)


@dataclass
class SpecificAxisFinding:
    """Hallazgo sobre un eje específico del tipo."""

    axis: str                      # e.g. "m_aplicacion_practica_resonancia"
    note: str                      # 1-2 frases


@dataclass
class EditorialReport:
    """Reporte editorial completo de un guion."""

    filename: str
    kind: str                      # "M" | "T" | "S"
    episode_id: str
    score_global: float
    cluster_label: str             # "Top tier" / "Sólido sectorial" / ...
    cluster_phrase: str            # frase comparativa
    perspectives: list[PerspectiveBlock]
    specific_axes: list[SpecificAxisFinding]
    verdict: EditorialVerdict
    next_level_actions: list[str]  # qué cambiar para subir un nivel
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def all_issues(self) -> list[EditorialIssue]:
        out: list[EditorialIssue] = []
        for block in self.perspectives:
            out.extend(block.issues)
        return out


_VERDICT_BADGE = {
    "PUBLICAR": "PUBLICAR ✅",
    "REVISAR":  "REVISAR 🟡",
    "BLOQUEAR": "BLOQUEAR 🔴",
}


def _format_issue(issue: EditorialIssue) -> str:
    return (
        f"- [{issue.severity}] {issue.axis} · \"{issue.problem}\" "
        f"→ \"{issue.proposal}\""
    )


def render_markdown(report: EditorialReport) -> str:
    """Devuelve el reporte en formato Markdown según §6.3."""
    lines: list[str] = []
    lines.append(f"## {report.filename} · {report.kind}")
    lines.append("")
    lines.append(
        f"**Score global:** {report.score_global:.1f}/10 · "
        f"**Veredicto:** {_VERDICT_BADGE[report.verdict.verdict]}"
    )
    lines.append(
        f"**Cluster:** {report.cluster_label} — {report.cluster_phrase}"
    )
    lines.append("")

    lines.append("### Panel")
    lines.append("")
    persona_labels = {p.key: p.label for p in PERSPECTIVES}
    for block in report.perspectives:
        label = persona_labels.get(block.perspective_key, block.perspective_key)
        lines.append(
            f"**{label} — {block.score:.1f}/10.** {block.rationale}"
        )
        for issue in block.issues:
            lines.append(_format_issue(issue))
        lines.append("")

    if report.specific_axes:
        lines.append("### Ejes específicos del tipo")
        lines.append("")
        for axis in report.specific_axes:
            lines.append(f"- **{axis.axis}:** {axis.note}")
        lines.append("")

    if report.next_level_actions and report.verdict.verdict != "PUBLICAR":
        next_level = {
            "BLOQUEAR": "REVISAR",
            "REVISAR": "PUBLICAR",
        }.get(report.verdict.verdict, "PUBLICAR")
        lines.append(
            f"### Para subir de nivel (→ {next_level})"
        )
        lines.append("")
        for i, action in enumerate(report.next_level_actions, 1):
            lines.append(f"{i}. {action}")
        lines.append("")

    return "\n".join(lines)


def render_json(report: EditorialReport) -> str:
    """Devuelve el reporte serializado a JSON estable y parseable."""
    payload = {
        "filename": report.filename,
        "kind": report.kind,
        "episode_id": report.episode_id,
        "timestamp": report.timestamp,
        "score_global": report.score_global,
        "cluster": {
            "label": report.cluster_label,
            "phrase": report.cluster_phrase,
        },
        "verdict": {
            "label": report.verdict.verdict,
            "reasons": report.verdict.reasons,
        },
        "perspectives": [
            {
                "key": block.perspective_key,
                "score": block.score,
                "rationale": block.rationale,
                "issues": [issue.to_dict() for issue in block.issues],
            }
            for block in report.perspectives
        ],
        "specific_axes": [
            {"axis": a.axis, "note": a.note}
            for a in report.specific_axes
        ],
        "next_level_actions": report.next_level_actions,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def cluster_from_score(score: float) -> tuple[str, str]:
    """Devuelve (label, frase comparativa por defecto) para un score 1-10.

    La frase comparativa por defecto es genérica; el LLM normalmente la
    sobrescribe con una más concreta cuando construye el reporte.
    """
    cluster = cluster_for(score)
    references = ", ".join(cluster.references[:2])
    phrase = f"cerca de {references}. {cluster.description}"
    return cluster.label, phrase


def aggregate_corpus_summary(
    reports: Iterable[EditorialReport],
) -> dict:
    """Construye un resumen agregado para modo --corpus."""
    reports = list(reports)
    by_kind: dict[str, list[EditorialReport]] = {"M": [], "T": [], "S": []}
    for r in reports:
        if r.kind in by_kind:
            by_kind[r.kind].append(r)

    summary: dict = {
        "total_scripts": len(reports),
        "by_kind": {},
        "verdicts": {"PUBLICAR": 0, "REVISAR": 0, "BLOQUEAR": 0},
    }
    for kind, items in by_kind.items():
        items.sort(key=lambda r: r.score_global, reverse=True)
        summary["by_kind"][kind] = {
            "count": len(items),
            "top3": [(r.filename, r.score_global) for r in items[:3]],
            "bottom3": [(r.filename, r.score_global) for r in items[-3:]],
            "average_score": (
                round(sum(r.score_global for r in items) / len(items), 2)
                if items else 0.0
            ),
        }
    for r in reports:
        summary["verdicts"][r.verdict.verdict] += 1
    return summary
