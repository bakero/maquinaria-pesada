#!/usr/bin/env python3
"""Driver de entrenamiento del generador v6.

Genera 11 guiones por iteración (M0, M0_T1, M0_T2, M1, M1_T1, M1_T2, S1..S5),
guarda los outputs en Guiones/iter_<N>/ y un reporte JSON con el resumen de
validaciones para análisis.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path

from generadores import m_generator, s_generator, t_generator
from validators.result import summarize

REPO_ROOT = Path(__file__).resolve().parent

S_TERMS = [
    ("S1", "RAG"),
    ("S2", "Fine-tuning"),
    ("S3", "Hallucination"),
    ("S4", "Embedding"),
    ("S5", "Prompt"),
]

JOBS = [
    ("M", "M0", None),
    ("T", "M0_T1", None),
    ("T", "M0_T2", None),
    ("M", "M1", None),
    ("T", "M1_T1", None),
    ("T", "M1_T2", None),
] + [("S", ep, term) for ep, term in S_TERMS]


def _run_one(kind: str, ep: str, term: str | None):
    if kind == "M":
        return m_generator.generate(ep, repo_root=REPO_ROOT)
    if kind == "T":
        return t_generator.generate(ep, repo_root=REPO_ROOT)
    return s_generator.generate(ep, term=term, repo_root=REPO_ROOT)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", type=int, required=True)
    args = ap.parse_args()

    iter_dir = REPO_ROOT / "Guiones" / f"iter_{args.iter}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    report_path = REPO_ROOT / "logs" / f"entrenamiento_iter_{args.iter}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "iter": args.iter,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "jobs": [],
        "totals": {},
    }
    print(f"\n>>> ITERACIÓN {args.iter} — {len(JOBS)} guiones\n")

    hard_counter: Counter[str] = Counter()
    soft_counter: Counter[str] = Counter()

    for idx, (kind, ep, term) in enumerate(JOBS, start=1):
        t0 = datetime.now()
        print(f"[{idx:>2}/{len(JOBS)}] {kind} {ep}"
              + (f" term={term!r}" if term else ""), flush=True)
        entry: dict = {"kind": kind, "ep": ep, "term": term,
                       "started_at": t0.isoformat(timespec="seconds")}
        try:
            result = _run_one(kind, ep, term)
        except Exception as exc:  # noqa: BLE001
            print(f"   EXCEPTION: {exc}\n{traceback.format_exc()}", flush=True)
            entry["error"] = f"{type(exc).__name__}: {exc}"
            entry["elapsed_s"] = (datetime.now() - t0).total_seconds()
            report["jobs"].append(entry)
            continue

        elapsed = (datetime.now() - t0).total_seconds()
        gen = result.generation
        summary = summarize(result.validation_results)
        entry.update({
            "elapsed_s": round(elapsed, 1),
            "model": gen.model,
            "ok_gen": gen.ok,
            "used_retry": result.used_retry,
            "input_tokens": gen.input_tokens,
            "output_tokens": gen.output_tokens,
            "cost_usd": round(gen.cost_usd, 4),
            "validation": summary,
        })
        if result.used_retry and result.retry_generation:
            entry["retry_cost_usd"] = round(
                result.retry_generation.cost_usd, 4)

        # Guardar guion.
        out = iter_dir / f"{ep}_v6.md"
        out.write_text(result.final_text or "", encoding="utf-8")
        entry["script_path"] = out.relative_to(REPO_ROOT).as_posix()

        for rn in summary.get("hard_failures", []):
            hard_counter[rn] += 1
        for rn in summary.get("soft_warnings", []):
            soft_counter[rn] += 1

        print(f"   ok={gen.ok}  retry={result.used_retry}  "
              f"hard={summary['hard_failed']}  soft={summary['soft_failed']}  "
              f"out={out.name}  ({elapsed:.0f}s)", flush=True)

        report["jobs"].append(entry)

    report["finished_at"] = datetime.now().isoformat(timespec="seconds")
    report["totals"] = {
        "n_jobs": len(JOBS),
        "n_errors": sum(1 for j in report["jobs"] if "error" in j),
        "n_blocked": sum(1 for j in report["jobs"]
                        if j.get("validation", {}).get("blocking")),
        "n_with_soft": sum(1 for j in report["jobs"]
                          if j.get("validation", {}).get("soft_failed", 0) > 0),
        "hard_rule_counts": dict(hard_counter.most_common()),
        "soft_rule_counts": dict(soft_counter.most_common()),
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"\n>>> Reporte: {report_path.relative_to(REPO_ROOT).as_posix()}")
    print(f">>> Totales: {report['totals']}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="entrenar_v6.py", params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        sys.exit(main())
