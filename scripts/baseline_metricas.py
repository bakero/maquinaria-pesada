"""Baseline de métricas de generación (coste, latencia, retry-rate, fallos).

Ejecuta una batería de generaciones REALES sobre los episodios indicados y
emite un reporte JSON con coste medio/mediana/p95, retry-rate, latencias y
los top fallos por regla. Se compara contra reportes posteriores para
validar las optimizaciones (Fase 1+).

Uso:
    python scripts/baseline_metricas.py \\
        --episodios M0 M1 M0_T1 M0_T2 S1 \\
        --repeticiones 3 \\
        --salida logs/baseline_$(date +%F).json

Requiere ANTHROPIC_API_KEY. NO usar sobre el repo en CI.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _detect_kind(episode_id: str) -> str:
    if episode_id.startswith("S"):
        return "S"
    if "_T" in episode_id:
        return "T"
    return "M"


def _run_one(episode_id: str, *, term: str | None) -> dict:
    """Genera un episodio y devuelve métricas de esa corrida."""
    from generadores import m_generator, s_generator, t_generator

    kind = _detect_kind(episode_id)
    started = time.perf_counter()
    if kind == "M":
        result = m_generator.generate(episode_id, repo_root=REPO_ROOT)
    elif kind == "T":
        result = t_generator.generate(episode_id, repo_root=REPO_ROOT)
    else:
        if not term:
            raise SystemExit(
                f"--term requerido para episodios S ({episode_id})"
            )
        result = s_generator.generate(
            episode_id, term=term, repo_root=REPO_ROOT)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    gen = result.generation
    last_retry = result.retry_generation
    total_cost = gen.cost_usd + (last_retry.cost_usd if last_retry else 0.0)
    total_input = gen.input_tokens + (last_retry.input_tokens if last_retry else 0)
    total_output = gen.output_tokens + (last_retry.output_tokens if last_retry else 0)
    total_cache_read = gen.cache_read_input_tokens + (
        last_retry.cache_read_input_tokens if last_retry else 0
    )

    hard = sum(
        1 for r in result.validation_results
        if r.severity == "HARD" and not r.passed
    )
    soft = sum(
        1 for r in result.validation_results
        if r.severity == "SOFT" and not r.passed
    )
    hard_rules = [
        r.rule_name for r in result.validation_results
        if r.severity == "HARD" and not r.passed
    ]
    soft_rules = [
        r.rule_name for r in result.validation_results
        if r.severity == "SOFT" and not r.passed
    ]
    return {
        "episode_id": episode_id,
        "kind": kind,
        "cost_usd": total_cost,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cache_read_tokens": total_cache_read,
        "latency_ms": elapsed_ms,
        "retries_done": result.retries_done,
        "patch_retries": result.patch_retries,
        "hard_failed": hard,
        "soft_failed": soft,
        "hard_rules": hard_rules,
        "soft_rules": soft_rules,
        "pass_first": hard == 0 and not result.used_retry,
    }


def _aggregate(runs: list[dict]) -> dict:
    """Agrega métricas por kind (M/T/S)."""
    by_kind: dict[str, list[dict]] = {}
    for r in runs:
        by_kind.setdefault(r["kind"], []).append(r)

    summary: dict = {}
    hard_counter: Counter = Counter()
    soft_counter: Counter = Counter()

    for kind, items in by_kind.items():
        costs = [r["cost_usd"] for r in items]
        lats = [r["latency_ms"] for r in items]
        retries = [r["retries_done"] for r in items]
        pass_first = sum(1 for r in items if r["pass_first"])
        for r in items:
            hard_counter.update(r["hard_rules"])
            soft_counter.update(r["soft_rules"])
        summary[kind] = {
            "n": len(items),
            "cost_usd": {
                "mean": round(statistics.fmean(costs), 6) if costs else 0,
                "median": round(statistics.median(costs), 6) if costs else 0,
                "p95": round(_p95(costs), 6) if costs else 0,
            },
            "latency_ms": {
                "p50": int(statistics.median(lats)) if lats else 0,
                "p95": int(_p95(lats)) if lats else 0,
            },
            "retries": {
                "mean": round(statistics.fmean(retries), 2) if retries else 0,
                "any_retry_rate": round(
                    sum(1 for r in retries if r > 0) / len(retries), 3
                ) if retries else 0,
            },
            "pass_first_rate": round(pass_first / len(items), 3) if items else 0,
        }

    return {
        "by_kind": summary,
        "top_hard_fails": hard_counter.most_common(10),
        "top_soft_fails": soft_counter.most_common(10),
    }


def _p95(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = int(0.95 * (len(s) - 1))
    return s[idx]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--episodios", nargs="+", required=True,
        help="IDs: M0 M1 M0_T1 S1_RAG ...",
    )
    parser.add_argument(
        "--repeticiones", type=int, default=1,
        help="Veces que se repite cada episodio (default 1).",
    )
    parser.add_argument(
        "--term", default=None,
        help="Término del glosario para episodios S (si aplica).",
    )
    parser.add_argument(
        "--salida", default=None,
        help="Ruta del JSON de salida (default: logs/baseline_<fecha>.json).",
    )
    parser.add_argument(
        "--etiqueta", default="baseline",
        help="Etiqueta de versión incluida en el reporte.",
    )
    args = parser.parse_args()

    runs: list[dict] = []
    for ep in args.episodios:
        for i in range(args.repeticiones):
            print(f"→ {ep} (rep {i + 1}/{args.repeticiones})")
            try:
                runs.append(_run_one(ep, term=args.term))
            except Exception as exc:  # noqa: BLE001
                print(f"  ERROR: {exc}")
                runs.append({
                    "episode_id": ep, "kind": _detect_kind(ep),
                    "error": str(exc),
                })

    report = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "etiqueta": args.etiqueta,
        "n_total": len(runs),
        "runs": runs,
        "summary": _aggregate([r for r in runs if "error" not in r]),
    }

    out_path = Path(args.salida) if args.salida else (
        REPO_ROOT / "logs" / f"baseline_{datetime.now():%Y%m%d_%H%M%S}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"\nReporte: {out_path}")


if __name__ == "__main__":  # pragma: no cover
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="scripts/baseline_metricas.py",
                            params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
