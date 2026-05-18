"""A/B test de system prompts v6 vs v7.

Genera N episodios con el SYSTEM_PROMPT actual (v7) y otros N con el legacy
v6 (`SYSTEM_PROMPT_V6_LEGACY` / `_LEGACY_DETAIL` cuando existe). Compara
coste, retry-rate, pass-first rate y distribución de fallos.

Uso:
    python scripts/ab_test_prompts.py \\
        --m M0 M1 M2 M3 M4 M5 M6 \\
        --t M0_T1 M0_T2 M1_T1 M2_T1 M3_T1 M4_T1 M5_T1 \\
        --s S1 S2 S3 S4 S5 S6 \\
        --term-s RAG \\
        --salida docs/ab_test_fase3_$(date +%F).md

ATENCIÓN: gasta API real. ~20 episodios × 2 ramas = ~$0.40-1.00 según hits
de cache. Lanzar solo cuando se quiera validar el merge.
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


def _run_with_prompt(generator, episode_id: str, system_override: str,
                     *, term: str | None = None) -> dict:
    """Ejecuta el generador inyectando un system prompt concreto.

    Truco: parchea temporalmente el atributo SYSTEM_PROMPT del módulo del
    generador para forzar la rama (v6 legacy o v7 actual).
    """
    saved = generator.SYSTEM_PROMPT
    generator.SYSTEM_PROMPT = system_override
    started = time.perf_counter()
    try:
        if term is not None:
            result = generator.generate(
                episode_id, term=term, repo_root=REPO_ROOT)
        else:
            result = generator.generate(episode_id, repo_root=REPO_ROOT)
    finally:
        generator.SYSTEM_PROMPT = saved
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    gen = result.generation
    retry = result.retry_generation
    total_cost = gen.cost_usd + (retry.cost_usd if retry else 0.0)
    hard = sum(
        1 for r in result.validation_results
        if r.severity == "HARD" and not r.passed
    )
    soft = sum(
        1 for r in result.validation_results
        if r.severity == "SOFT" and not r.passed
    )
    return {
        "episode_id": episode_id,
        "cost_usd": total_cost,
        "input_tokens": gen.input_tokens,
        "output_tokens": gen.output_tokens,
        "cache_read_tokens": gen.cache_read_input_tokens,
        "latency_ms": elapsed_ms,
        "retries_done": result.retries_done,
        "patch_retries": result.patch_retries,
        "hard_failed": hard,
        "soft_failed": soft,
        "hard_rules": [
            r.rule_name for r in result.validation_results
            if r.severity == "HARD" and not r.passed
        ],
        "soft_rules": [
            r.rule_name for r in result.validation_results
            if r.severity == "SOFT" and not r.passed
        ],
        "pass_first": hard == 0 and not result.used_retry,
        "word_count": len(result.final_text.split()) if result.final_text else 0,
    }


def _v6_prompt_for(generator) -> str | None:
    """Devuelve el system prompt legacy v6 si el módulo lo expone.

    Para T existe `SYSTEM_PROMPT_V6_LEGACY`. Para M y S guardamos el v7
    como SYSTEM_PROMPT; si no hay legacy explícito devolvemos None y el
    a/b test salta esa rama (solo reporta v7).
    """
    return getattr(generator, "SYSTEM_PROMPT_V6_LEGACY", None)


def _summarize(runs: list[dict]) -> dict:
    if not runs:
        return {"n": 0}
    costs = [r["cost_usd"] for r in runs]
    retries = [r["retries_done"] for r in runs]
    wc = [r["word_count"] for r in runs if r["word_count"]]
    pf = sum(1 for r in runs if r["pass_first"])
    hard_counter: Counter = Counter()
    soft_counter: Counter = Counter()
    for r in runs:
        hard_counter.update(r["hard_rules"])
        soft_counter.update(r["soft_rules"])
    return {
        "n": len(runs),
        "cost_mean": round(statistics.fmean(costs), 6) if costs else 0,
        "cost_p95": round(_p95(costs), 6) if costs else 0,
        "retries_mean": round(statistics.fmean(retries), 2) if retries else 0,
        "pass_first_rate": round(pf / len(runs), 3),
        "word_count_mean": int(statistics.fmean(wc)) if wc else 0,
        "word_count_p50": int(statistics.median(wc)) if wc else 0,
        "top_hard": hard_counter.most_common(8),
        "top_soft": soft_counter.most_common(8),
    }


def _p95(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    return s[int(0.95 * (len(s) - 1))]


def _render_markdown(report: dict) -> str:
    out = ["# A/B test — system prompts v6 vs v7",
           f"\nFecha: {report['fecha']}\n"]
    for kind, branches in report["per_kind"].items():
        out.append(f"\n## {kind}\n")
        out.append("| Métrica | v6 (control) | v7 (refactor) | Δ |")
        out.append("|---|---|---|---|")
        v6 = branches.get("v6") or {}
        v7 = branches.get("v7") or {}
        for key in ("cost_mean", "cost_p95", "retries_mean",
                    "pass_first_rate", "word_count_mean"):
            a = v6.get(key)
            b = v7.get(key)
            if a is None and b is None:
                continue
            delta = ""
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a:
                delta = f"{(b - a) / a:+.1%}"
            out.append(f"| {key} | {a} | {b} | {delta} |")
        if v7.get("top_hard"):
            out.append("\n**Top hard fails v7**: " +
                       ", ".join(f"{n}×{r}" for r, n in v7["top_hard"]))
        if v6.get("top_hard"):
            out.append("\n**Top hard fails v6**: " +
                       ", ".join(f"{n}×{r}" for r, n in v6["top_hard"]))
    out.append("\n\n## Criterio de merge")
    out.append("- v7 ≥ v6 - 8 puntos en eval humana (rellenar manualmente)")
    out.append("- Coste medio v7 ≤ v6 con margen del 15%")
    out.append("- Pass-first rate v7 ≥ v6 - 5 pp")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m", nargs="*", default=[], help="IDs M")
    parser.add_argument("--t", nargs="*", default=[], help="IDs T (M{n}_T{x})")
    parser.add_argument("--s", nargs="*", default=[], help="IDs S")
    parser.add_argument("--term-s", default="RAG",
                         help="Término del glosario para todos los S del run.")
    parser.add_argument("--salida", default=None,
                         help="Ruta del Markdown de salida.")
    args = parser.parse_args()

    from generadores import m_generator, s_generator, t_generator
    mods = {"M": m_generator, "T": t_generator, "S": s_generator}
    eps = {"M": args.m, "T": args.t, "S": args.s}

    report: dict = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "per_kind": {},
        "raw": {"v6": [], "v7": []},
    }

    for kind, ids in eps.items():
        if not ids:
            continue
        gen = mods[kind]
        v7_prompt = gen.SYSTEM_PROMPT
        v6_prompt = _v6_prompt_for(gen)
        v6_runs: list[dict] = []
        v7_runs: list[dict] = []
        for ep in ids:
            print(f"[v7] {ep}")
            try:
                v7_runs.append(_run_with_prompt(
                    gen, ep, v7_prompt,
                    term=args.term_s if kind == "S" else None,
                ))
            except Exception as exc:  # noqa: BLE001
                print(f"  v7 ERROR: {exc}")
            if v6_prompt:
                print(f"[v6] {ep}")
                try:
                    v6_runs.append(_run_with_prompt(
                        gen, ep, v6_prompt,
                        term=args.term_s if kind == "S" else None,
                    ))
                except Exception as exc:  # noqa: BLE001
                    print(f"  v6 ERROR: {exc}")
        report["per_kind"][kind] = {
            "v6": _summarize(v6_runs),
            "v7": _summarize(v7_runs),
        }
        report["raw"]["v6"].extend(v6_runs)
        report["raw"]["v7"].extend(v7_runs)

    out_path = Path(args.salida) if args.salida else (
        REPO_ROOT / "docs" / f"ab_test_fase3_{datetime.now():%Y%m%d_%H%M%S}.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path = out_path.with_suffix(".json")
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nReporte MD: {out_path}\nRaw JSON: {json_path}")


if __name__ == "__main__":  # pragma: no cover
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="scripts/ab_test_prompts.py",
                            params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
