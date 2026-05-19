#!/usr/bin/env python3
"""CLI del panel editorial de MaquinarIA Pesada.

Evalúa guiones .txt como producto editorial (NO técnico). Cinco perspectivas:
Productor, Editor de marca, Oyente prototipo, Experto técnico, SEO/distribución.

Uso:
    python evaluador_editorial.py --file Guiones/M3.txt
    python evaluador_editorial.py --dir Guiones/
    python evaluador_editorial.py --dir Guiones/ --corpus
    python evaluador_editorial.py --dir Guiones/ --only-kind M
    python evaluador_editorial.py --file Guiones/M3.txt --perspective marca
    python evaluador_editorial.py --dir Guiones/ --md docs/editorial/2026-05-19.md
    python evaluador_editorial.py --dir Guiones/ --json logs/editorial.json
    python evaluador_editorial.py --dir Guiones/ --strict   # exit code segun veredicto

Exit codes en modo --strict:
    0  todos los guiones evaluados son PUBLICAR
    1  al menos uno REVISAR (sin BLOQUEAR)
    2  al menos uno BLOQUEAR

NOTA: este CLI invoca a Claude (Sonnet 4.6 por defecto) y carga el guion en
contexto. Coste estimado: ~$0.034 por guion en modo por-guion, ~$0.55 para
auditoría completa del corpus de 41 guiones.

Para la lógica detallada del panel ver `EVALUADOR_EDITORIAL_GUIONES.md`.

Este CLI orquesta la llamada al LLM, parsea su respuesta y emite el reporte.
El parsing de la respuesta del LLM se hace mediante una segunda llamada de
"structuring" si la primera no devuelve JSON limpio, para mantenerlo robusto.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from editorial.benchmark import cluster_for
from editorial.perspectives import (
    PERSPECTIVES,
)
from editorial.prompts import (
    DEFAULT_MODEL,
    build_prompt_maestro,
)
from editorial.report import (
    EditorialReport,
    PerspectiveBlock,
    SpecificAxisFinding,
    aggregate_corpus_summary,
    render_json,
    render_markdown,
)
from editorial.scoring import (
    EditorialIssue,
    EditorialVerdict,
    score_global,
    verdict_for,
)

# Reutilizamos el cliente Anthropic que ya tiene el repo.
from generadores.shared.anthropic_client import generate as _anthropic_generate

REPO_ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Detección de tipo y carga de guiones
# ---------------------------------------------------------------------------

_KIND_RE = {
    "S": re.compile(r"^S\d+(_|\.|$)"),
    "T": re.compile(r"^M\d+_T\d+(_|\.|$)"),
    "M": re.compile(r"^M\d+(?!_T)(_|\.|$)"),
}


def detect_kind(filename: str) -> str | None:
    """Detecta el tipo de guion por el nombre del fichero."""
    base = Path(filename).stem
    if _KIND_RE["S"].match(base):
        return "S"
    if _KIND_RE["T"].match(base):
        return "T"
    if _KIND_RE["M"].match(base):
        return "M"
    return None


def episode_id_from_filename(filename: str) -> str:
    """Extrae el episode_id del nombre del fichero (M3 / M1_T2 / S5_RAG)."""
    base = Path(filename).stem
    # Para M3_introduccion → "M3"
    m = re.match(r"^(M\d+(?:_T\d+)?|S\d+(?:_\w+)?)", base)
    return m.group(1) if m else base


def iter_scripts(directory: Path,
                 only_kind: str | None = None) -> Iterable[tuple[Path, str]]:
    """Itera (path, kind) de los guiones .txt del directorio."""
    for path in sorted(directory.glob("*.txt")):
        kind = detect_kind(path.name)
        if kind is None:
            continue
        if only_kind and kind != only_kind:
            continue
        yield path, kind


# ---------------------------------------------------------------------------
# Llamada al LLM + parseo del reporte
# ---------------------------------------------------------------------------

# Prompt de structuring: convierte la respuesta libre del panel a JSON estricto
# para parsing programático. Si el LLM ya devuelve JSON válido, se salta.
_STRUCTURING_INSTRUCTION = """\
A continuación tienes un informe editorial en texto libre. Convertilo a
JSON estricto con esta estructura:

{
  "score_global": <float 1-10>,
  "cluster_label": "<Top tier|Sólido sectorial|Estándar IA|Bajo|Crítico>",
  "cluster_phrase": "<frase comparativa con referente>",
  "verdict": "<PUBLICAR|REVISAR|BLOQUEAR>",
  "verdict_reasons": ["<razón 1>", ...],
  "perspectives": [
    {
      "key": "productor|marca|oyente|experto|seo",
      "score": <float 1-10>,
      "rationale": "<1 línea>",
      "issues": [
        {
          "severity": "critico|relevante|menor",
          "axis": "<nombre del eje>",
          "problem": "<frase del problema>",
          "proposal": "<acción concreta de cambio>"
        }
      ]
    }
  ],
  "specific_axes": [
    {"axis": "<nombre>", "note": "<1-2 frases>"}
  ],
  "next_level_actions": ["<acción 1>", ...]
}

Devuelve SOLO el JSON, sin markdown, sin explicaciones, sin ```json```.
"""


def _extract_json(text: str) -> dict | None:
    """Intenta extraer un objeto JSON de la respuesta del LLM."""
    # Caso simple: el output es JSON directo.
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Buscar el primer objeto JSON dentro del texto.
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _structure_response(raw_text: str, *, model: str) -> dict | None:
    """Si raw_text no es JSON parseable, hace una llamada extra para estructurar."""
    parsed = _extract_json(raw_text)
    if parsed is not None:
        return parsed
    result = _anthropic_generate(
        system=_STRUCTURING_INSTRUCTION,
        user=raw_text,
        model=model,
        max_output_tokens=4000,
        temperature=0.0,
    )
    if not result.ok:
        return None
    return _extract_json(result.text)


def _evaluate_one(
    *, path: Path, kind: str, model: str, dry_run: bool,
) -> EditorialReport | None:
    """Lanza la evaluación de un guion. Devuelve el reporte o None en error."""
    script_text = path.read_text(encoding="utf-8")
    episode_id = episode_id_from_filename(path.name)
    prompt = build_prompt_maestro(kind=kind, episode_id=episode_id,
                                   script_text=script_text)
    if dry_run:
        print(f"[DRY-RUN] {path.name} ({kind}) — prompt {len(prompt)} chars")
        return None
    result = _anthropic_generate(
        system="Devuelve la evaluación editorial en JSON estricto (formato "
               "indicado dentro del prompt) sin markdown ni preámbulo.",
        user=prompt,
        model=model,
        max_output_tokens=6000,
        temperature=0.3,
    )
    if not result.ok:
        print(f"[ERROR] {path.name}: {result.error}", file=sys.stderr)
        return None
    parsed = _structure_response(result.text, model=model)
    if parsed is None:
        print(f"[ERROR] {path.name}: no se pudo parsear la respuesta del LLM",
              file=sys.stderr)
        return None
    return _build_report(parsed, path=path, kind=kind, episode_id=episode_id)


def _build_report(parsed: dict, *, path: Path, kind: str,
                   episode_id: str) -> EditorialReport:
    """Construye `EditorialReport` desde el dict parseado."""
    perspective_scores: dict[str, float] = {}
    blocks: list[PerspectiveBlock] = []
    all_issues: list[EditorialIssue] = []

    for raw_persp in parsed.get("perspectives", []):
        key = raw_persp.get("key")
        if not key:
            continue
        score = float(raw_persp.get("score", 0.0))
        rationale = str(raw_persp.get("rationale", "")).strip()
        issues = []
        for raw_issue in raw_persp.get("issues", []):
            issue = EditorialIssue(
                severity=raw_issue.get("severity", "menor"),
                perspective=key,
                axis=str(raw_issue.get("axis", "")),
                problem=str(raw_issue.get("problem", "")),
                proposal=str(raw_issue.get("proposal", "")),
            )
            issues.append(issue)
            all_issues.append(issue)
        perspective_scores[key] = score
        blocks.append(PerspectiveBlock(
            perspective_key=key,
            score=score,
            rationale=rationale,
            issues=issues,
        ))

    # Score global: prioriza el del LLM si está; si no, lo recalcula.
    score = float(parsed.get("score_global") or score_global(perspective_scores, kind))

    cluster_label = parsed.get("cluster_label") or cluster_for(score).label
    cluster_phrase = parsed.get("cluster_phrase") or cluster_for(score).description

    verdict_label = parsed.get("verdict")
    verdict_reasons = parsed.get("verdict_reasons") or []
    if verdict_label:
        verdict = EditorialVerdict(
            verdict=verdict_label,
            score_global=score,
            reasons=verdict_reasons,
        )
    else:
        verdict = verdict_for(score, all_issues)

    specific_axes = [
        SpecificAxisFinding(axis=str(a.get("axis", "")),
                             note=str(a.get("note", "")))
        for a in parsed.get("specific_axes", [])
    ]

    return EditorialReport(
        filename=path.name,
        kind=kind,
        episode_id=episode_id,
        score_global=score,
        cluster_label=cluster_label,
        cluster_phrase=cluster_phrase,
        perspectives=blocks,
        specific_axes=specific_axes,
        verdict=verdict,
        next_level_actions=parsed.get("next_level_actions", []),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Panel editorial de guiones de MaquinarIA Pesada",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", type=Path, help="Evalúa un único guion .txt")
    src.add_argument("--dir", type=Path, help="Evalúa todos los .txt de un directorio")
    parser.add_argument("--corpus", action="store_true",
                        help="Modo corpus: 1 prompt sobre todo el directorio "
                             "+ auditoría global")
    parser.add_argument("--only-kind", choices=["M", "T", "S"],
                        help="Filtrar por tipo de guion")
    parser.add_argument("--perspective",
                        choices=[p.key for p in PERSPECTIVES],
                        help="Filtrar el output a una sola perspectiva")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"Modelo Claude (default: {DEFAULT_MODEL})")
    parser.add_argument("--md", type=Path,
                        help="Escribe el reporte agregado en este Markdown")
    parser.add_argument("--json", type=Path, dest="json_path",
                        help="Escribe el reporte agregado en este JSON")
    parser.add_argument("--strict", action="store_true",
                        help="Salir con código != 0 si hay REVISAR / BLOQUEAR")
    parser.add_argument("--dry-run", action="store_true",
                        help="No llama al LLM, solo prepara los prompts")
    return parser.parse_args(argv)


def _exit_code(reports: list[EditorialReport]) -> int:
    """0 si todo PUBLICAR · 1 si REVISAR · 2 si algún BLOQUEAR."""
    if not reports:
        return 0
    has_block = any(r.verdict.verdict == "BLOQUEAR" for r in reports)
    has_review = any(r.verdict.verdict == "REVISAR" for r in reports)
    if has_block:
        return 2
    if has_review:
        return 1
    return 0


def _maybe_filter_perspective(report: EditorialReport,
                              perspective: str | None) -> EditorialReport:
    if perspective is None:
        return report
    report.perspectives = [
        b for b in report.perspectives if b.perspective_key == perspective
    ]
    return report


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # Recolectar guiones a evaluar.
    targets: list[tuple[Path, str]]
    if args.file:
        kind = detect_kind(args.file.name)
        if kind is None:
            print(f"[ERROR] No puedo deducir el tipo (M/T/S) de {args.file.name}",
                  file=sys.stderr)
            return 2
        targets = [(args.file, kind)]
    else:
        if not args.dir.exists():
            print(f"[ERROR] Directorio no existe: {args.dir}", file=sys.stderr)
            return 2
        targets = list(iter_scripts(args.dir, only_kind=args.only_kind))

    if not targets:
        print("[INFO] No hay guiones .txt que evaluar.", file=sys.stderr)
        return 0

    # Verificar API key salvo en dry-run.
    if not args.dry_run and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY no definida (usá --dry-run para "
              "preparar prompts sin llamar al LLM).", file=sys.stderr)
        return 2

    reports: list[EditorialReport] = []
    for path, kind in targets:
        print(f"[INFO] Evaluando {path.name} ({kind})...", file=sys.stderr)
        report = _evaluate_one(
            path=path, kind=kind, model=args.model, dry_run=args.dry_run,
        )
        if report is None:
            continue
        report = _maybe_filter_perspective(report, args.perspective)
        reports.append(report)

    if args.dry_run:
        return 0

    # Render por consola.
    for report in reports:
        print()
        print(render_markdown(report))

    # Modo --corpus añade auditoría global al final.
    if args.corpus and len(reports) > 1:
        summary = aggregate_corpus_summary(reports)
        print()
        print("## AUDITORÍA DE CORPUS")
        print()
        print(f"Guiones evaluados: {summary['total_scripts']}")
        print(f"Veredictos: {summary['verdicts']}")
        for kind, info in summary["by_kind"].items():
            if info["count"] == 0:
                continue
            print(f"\n### {kind} ({info['count']} guiones, media {info['average_score']})")
            print(f"Top 3: {info['top3']}")
            print(f"Bottom 3: {info['bottom3']}")

    # Exportes.
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        with args.md.open("w", encoding="utf-8") as fh:
            fh.write(f"# Auditoría editorial — {datetime.utcnow().isoformat()}\n\n")
            for report in reports:
                fh.write(render_markdown(report))
                fh.write("\n\n---\n\n")

    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "reports": [json.loads(render_json(r)) for r in reports],
        }
        if args.corpus and len(reports) > 1:
            payload["corpus_summary"] = aggregate_corpus_summary(reports)
        with args.json_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    return _exit_code(reports) if args.strict else 0


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el CLI
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="evaluador_editorial.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        sys.exit(main())
