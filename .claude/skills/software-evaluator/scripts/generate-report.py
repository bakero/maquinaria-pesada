#!/usr/bin/env python3
"""
generate-report.py
Genera el índice de evaluaciones y calcula deltas respecto a la anterior.
Uso: python3 generate-report.py <repo_path> <eval_id>
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

def load_evaluation(eval_dir):
    """Carga evaluation-data.json de un directorio de evaluación."""
    data_file = Path(eval_dir) / "evaluation-data.json"
    if data_file.exists():
        with open(data_file) as f:
            return json.load(f)
    return None

def semaphore_emoji(score):
    if score >= 7: return "🟢"
    if score >= 4: return "🟡"
    return "🔴"

def trend_arrow(current, previous):
    if previous is None: return "—"
    diff = current - previous
    if diff > 0.5: return f"↑ +{diff:.1f}"
    if diff < -0.5: return f"↓ {diff:.1f}"
    return "→"

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 generate-report.py <repo_path> <eval_id>")
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    eval_id = sys.argv[2]
    evals_dir = repo_path / "docs" / "evaluations"

    # Cargar evaluación actual
    current_eval = load_evaluation(evals_dir / eval_id)
    if not current_eval:
        print(f"No se encontró evaluation-data.json en {evals_dir / eval_id}")
        sys.exit(1)

    # Buscar evaluación anterior
    all_evals = sorted([d for d in evals_dir.iterdir() if d.is_dir() and d.name != eval_id])
    previous_eval = None
    if all_evals:
        previous_eval = load_evaluation(all_evals[-1])

    # Generar índice
    index_path = evals_dir / "INDEX.md"
    all_eval_dirs = sorted([d for d in evals_dir.iterdir() if d.is_dir()])
    all_evals_data = [(d.name, load_evaluation(d)) for d in all_eval_dirs]
    all_evals_data = [(name, data) for name, data in all_evals_data if data]

    index_lines = [
        "# Historial de Evaluaciones Técnicas\n",
        "| Fecha | Global | Código | Tests | Seguridad | CI/CD | BD | Observabilidad |",
        "|-------|--------|--------|-------|-----------|-------|-----|----------------|",
    ]

    for eval_name, eval_data in all_evals_data:
        scores = eval_data.get("scores", {})
        g = scores.get("global", 0)
        index_lines.append(
            f"| {eval_name} "
            f"| {semaphore_emoji(g)} {g:.1f} "
            f"| {scores.get('code_quality', 0):.1f} "
            f"| {scores.get('tests', 0):.1f} "
            f"| {scores.get('security', 0):.1f} "
            f"| {scores.get('cicd', 0):.1f} "
            f"| {scores.get('database', 0):.1f} "
            f"| {scores.get('observability', 0):.1f} |"
        )

    with open(index_path, "w") as f:
        f.write("\n".join(index_lines))
    print(f"Índice actualizado: {index_path}")

    # Generar comparativa
    if previous_eval:
        curr_scores = current_eval.get("scores", {})
        prev_scores = previous_eval.get("scores", {})

        print("\n═══ COMPARATIVA CON EVALUACIÓN ANTERIOR ═══")
        areas = [
            ("code_quality", "Calidad de código"),
            ("patterns", "Patrones"),
            ("tests", "Tests"),
            ("frontend", "Frontend"),
            ("database", "Base de datos"),
            ("security", "Seguridad"),
            ("cicd", "CI/CD"),
            ("documentation", "Documentación"),
            ("dependencies", "Dependencias"),
            ("observability", "Observabilidad"),
        ]
        for key, name in areas:
            curr = curr_scores.get(key, 0)
            prev = prev_scores.get(key, 0)
            trend = trend_arrow(curr, prev)
            emoji = semaphore_emoji(curr)
            print(f"  {name:<25} {emoji} {curr:.1f}  {trend}")

        global_curr = curr_scores.get("global", 0)
        global_prev = prev_scores.get("global", 0)
        print(f"\n  {'GLOBAL':<25} {semaphore_emoji(global_curr)} {global_curr:.1f}  {trend_arrow(global_curr, global_prev)}")

        # Alertar si algo empeoró
        deteriorated = [
            name for key, name in areas
            if curr_scores.get(key, 0) < prev_scores.get(key, 0) - 0.5
        ]
        if deteriorated:
            print(f"\n  🚨 ÁREAS QUE HAN EMPEORADO: {', '.join(deteriorated)}")
    else:
        print("\n  ℹ️  Primera evaluación — sin datos anteriores para comparar.")

if __name__ == "__main__":
    main()
