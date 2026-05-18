"""Runner del pipeline v7 con dos planes: smoke y produccion.

Guarda los guiones generados en `Output_v6/<kind>/<episode_id>[_iterN].txt`
y produce un reporte MD + JSON con coste, cache hit rate, retries y
fallos por iteración. Aborta automáticamente si excede `--budget-usd`.

Planes:
- smoke: 2 M + 4 T + 5 S (~$0.50 por iteración cold; -50% por iter warm).
  Diseñado para correr en 3 iteraciones y medir el ahorro real del caching.
- produccion: 6 M + 11 T + 8 S = 25 episodios (~$1.85 cold cache).

Uso típico (presupuesto €14 ≈ $15):
    # 0) Pre-flight (sin gasto) para validar entorno + PDFs + estimación.
    python scripts/smoke_test_v7.py --check --plan smoke --iteraciones 3

    # 1) Smoke test x3 iteraciones (valida v7 + mide caching, ~$1.0)
    python scripts/smoke_test_v7.py --run --plan smoke --iteraciones 3 --budget-usd 14

    # 2) Producción (genera los 25 episodios del plan, ~$1.85)
    python scripts/smoke_test_v7.py --run --plan produccion --budget-usd 14

Flags útiles:
    --solo M | T | S        # limita a un solo tipo
    --con-prewriting-llm    # activa MP_PREWRITING_LLM=1 (Haiku tool call)
    --baseline X.json       # compara contra reporte previo

Guiones generados en: Output_v6/M/, Output_v6/T/, Output_v6/S/.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Asegura que `generadores/` y `validators/` son importables.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Carga .env de la raiz del repo o del padre antes de comprobar la key
# (load_dotenv busca hacia arriba). Sin esto, _check_env reporta "Falta
# ANTHROPIC_API_KEY" aunque exista en .env, porque corre antes de importar
# generadores.shared.anthropic_client (que es donde se llama load_dotenv()).
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass


# Plan SMOKE (3 iteraciones para medir caching + estabilidad).
PLAN_M: list[str] = ["M0", "M3"]
PLAN_T: list[str] = ["M0_T1", "M0_T2", "M10_T1", "M10_T5"]
PLAN_S: list[tuple[str, str]] = [
    ("S1_RAG", "RAG"),
    ("S2_Fine_tuning", "Fine-tuning"),
    ("S3_Agentic_AI", "Agentic AI"),
    ("S4_Hallucination", "Hallucination"),
    ("S5_Golden_dataset", "Golden dataset"),
]

# Plan PRODUCCION (6 M + 11 T + 8 S = 25 episodios, ~$2.50).
PROD_M: list[str] = ["M0", "M1", "M2", "M3", "M4", "M5"]
PROD_T: list[str] = [
    "M0_T1", "M0_T2", "M0_T3",
    "M1_T1", "M1_T2", "M1_T3",
    "M2_T1", "M2_T2",
    "M3_T1",
    "M4_T1",
    "M5_T1",
]
PROD_S: list[tuple[str, str]] = [
    ("S1_RAG", "RAG"),
    ("S2_Fine_tuning", "Fine-tuning"),
    ("S3_Embedding", "Embedding"),
    ("S4_Agentic_AI", "Agentic AI"),
    ("S5_Chain_of_Thought", "Chain-of-Thought"),
    ("S6_Hallucination", "Hallucination"),
    ("S7_RLHF", "RLHF"),
    ("S8_Golden_dataset", "Golden dataset"),
]

# Coste estimado por tipo (USD por episodio, cold cache).
_COST_ESTIMATE_USD = {"M": 0.13, "T": 0.15, "S": 0.0015}


def _check_env(plan_m: list[str], plan_t: list[str],
                plan_s: list[tuple[str, str]]) -> list[str]:
    """Devuelve lista de problemas encontrados (vacía si OK)."""
    issues: list[str] = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        issues.append("Falta ANTHROPIC_API_KEY (define en .env o exporta).")
    if plan_m or plan_t:
        master_ok = any(
            (REPO_ROOT / "PDFs" / "auxiliares" / n).exists()
            for n in ("master IA.pdf", "master_IA.pdf", "MasterIA.pdf")
        )
        if not master_ok:
            issues.append("Falta PDFs/auxiliares/master IA.pdf (BLOQUE_FUENTES se resentirá).")
    for ep in plan_m:
        n = int(ep.removeprefix("M"))
        resumenes = list((REPO_ROOT / "PDFs" / "resumenes").glob(
            f"RESUMEN_M{n}_*.pdf"))
        if not resumenes:
            issues.append(f"Falta PDF resumen para {ep}: PDFs/resumenes/RESUMEN_M{n}_*.pdf")
    for ep in plan_t:
        parts = ep.split("_T")
        modulo_n = int(parts[0].removeprefix("M"))
        tema_n = int(parts[1])
        temas = list((REPO_ROOT / "PDFs" / "temas").glob(
            f"M{modulo_n}_T{tema_n}_*.pdf"))
        if not temas:
            issues.append(f"Falta PDF de tema para {ep}: PDFs/temas/M{modulo_n}_T{tema_n}_*.pdf")
    if plan_s:
        glosario_path = REPO_ROOT / "PDFs" / "auxiliares" / "glosario_unificado.md"
        if not glosario_path.exists():
            issues.append("Falta PDFs/auxiliares/glosario_unificado.md (S no podrá generar).")
        else:
            glos_text = glosario_path.read_text(encoding="utf-8")
            for _ep, term in plan_s:
                if term.lower() not in glos_text.lower():
                    issues.append(f"Glosario no contiene término '{term}'.")
    return issues


def _summarize(runs: list[dict]) -> dict:
    if not runs:
        return {"n": 0}
    costs = [r["cost_usd"] for r in runs]
    lat = [r["latency_ms"] for r in runs]
    retries = [r["retries_done"] for r in runs]
    patches = [r["patch_retries"] for r in runs]
    pass_first = sum(1 for r in runs if r["pass_first"])
    cache_total = sum(r["cache_read_tokens"] for r in runs)
    input_total = sum(r["input_tokens"] for r in runs)
    grand_in = input_total + cache_total
    hard_counter: Counter = Counter()
    soft_counter: Counter = Counter()
    for r in runs:
        hard_counter.update(r["hard_rules"])
        soft_counter.update(r["soft_rules"])
    return {
        "n": len(runs),
        "cost_total_usd": round(sum(costs), 4),
        "cost_mean": round(statistics.fmean(costs), 6),
        "cost_p95": round(_p95(costs), 6),
        "latency_p50_ms": int(statistics.median(lat)),
        "latency_p95_ms": int(_p95(lat)),
        "retries_mean": round(statistics.fmean(retries), 2),
        "any_retry_rate": round(sum(1 for r in retries if r > 0) / len(retries), 3),
        "patch_retries_total": sum(patches),
        "pass_first_rate": round(pass_first / len(runs), 3),
        "cache_hit_rate_global": (
            round(cache_total / grand_in, 3) if grand_in > 0 else 0.0
        ),
        "top_hard": hard_counter.most_common(8),
        "top_soft": soft_counter.most_common(8),
    }


def _p95(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    return s[int(0.95 * (len(s) - 1))]


OUTPUT_DIR_NAME = "Output_v6"


def _save_guion(episode_id: str, kind: str, final_text: str,
                iteration: int = 1) -> Path | None:
    """Guarda el guion final en Output_v6/<kind>/<episode_id>[_iterN].txt.

    Si `iteration > 1` añade sufijo `_iter{N}` para no pisar runs anteriores
    (útil en el smoke test multi-iteración para comparar consistencia).
    """
    if not final_text:
        return None
    out_dir = REPO_ROOT / OUTPUT_DIR_NAME / kind
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if iteration == 1 else f"_iter{iteration}"
    out_path = out_dir / f"{episode_id}{suffix}.txt"
    out_path.write_text(final_text, encoding="utf-8")
    return out_path


def _run_one(episode_id: str, kind: str, term: str | None = None,
             iteration: int = 1) -> dict:
    from generadores import m_generator, s_generator, t_generator
    started = time.perf_counter()
    if kind == "M":
        result = m_generator.generate(episode_id, repo_root=REPO_ROOT)
    elif kind == "T":
        result = t_generator.generate(episode_id, repo_root=REPO_ROOT)
    else:
        result = s_generator.generate(
            episode_id, term=term or "", repo_root=REPO_ROOT)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    saved_path = _save_guion(
        episode_id, kind, result.final_text, iteration=iteration,
    )
    gen = result.generation
    retry = result.retry_generation
    total_cost = gen.cost_usd + (retry.cost_usd if retry else 0.0)
    total_input = gen.input_tokens + (retry.input_tokens if retry else 0)
    total_output = gen.output_tokens + (retry.output_tokens if retry else 0)
    total_cache = gen.cache_read_input_tokens + (
        retry.cache_read_input_tokens if retry else 0
    )
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
        "kind": kind,
        "cost_usd": total_cost,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cache_read_tokens": total_cache,
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
        "is_blocked": result.is_blocked_by_validation,
        "saved_to": str(saved_path) if saved_path else None,
    }


def _render_markdown(report: dict, *, baseline: dict | None) -> str:
    out = [
        f"# Run pipeline v7 — plan '{report.get('plan', 'smoke')}'",
        f"\nFecha: {report['fecha']}",
        f"\nIteraciones: {report.get('iteraciones', 1)}",
        f"\nFlags: MP_PREWRITING_LLM={report.get('mp_prewriting_llm', '0')}",
        f"\nN total: {report['n_total']} (ok: {report.get('n_ok', '?')})",
        f"\nCoste acumulado: ${report.get('cost_acumulado_usd', 0):.4f} USD "
        f"(budget ${report.get('budget_usd', '?')})",
        f"\nAbortado por budget: {report.get('aborted', False)}",
        "",
    ]

    # Tabla por iteración (la métrica clave para evaluar el caching).
    per_iter = report.get("per_iteration", {})
    if len(per_iter) > 1:
        out.append("\n## Evolución por iteración (efecto caching)\n")
        out.append("| Iter | Eps | Coste total | Coste medio | Cache hit % | Pass-first | Retries medio |")
        out.append("|---|---|---|---|---|---|---|")
        for it in sorted(per_iter):
            s = per_iter[it]
            out.append(
                f"| {it} | {s['n']} | ${s['cost_total_usd']:.4f} | "
                f"${s['cost_mean']:.4f} | {100 * s['cache_hit_rate_global']:.0f}% | "
                f"{100 * s['pass_first_rate']:.0f}% | {s['retries_mean']} |"
            )
        # Δ entre iter 1 y iter N.
        first = per_iter[min(per_iter)]
        last = per_iter[max(per_iter)]
        if first["cost_mean"] > 0:
            delta_pct = (last["cost_mean"] - first["cost_mean"]) / first["cost_mean"]
            out.append(f"\n**Δ coste medio iter {max(per_iter)} vs iter 1: "
                       f"{delta_pct:+.1%}** (negativo = ahorro por cache)")

    for kind in ("M", "T", "S"):
        section = report["per_kind"].get(kind, {})
        if not section:
            continue
        out.append(f"\n## {kind}\n")
        out.append("| Métrica | v7 |")
        out.append("|---|---|")
        for key, label in (
            ("n", "Episodios"),
            ("cost_total_usd", "Coste TOTAL (USD)"),
            ("cost_mean", "Coste medio (USD)"),
            ("cost_p95", "Coste p95 (USD)"),
            ("latency_p50_ms", "Latencia p50 (ms)"),
            ("latency_p95_ms", "Latencia p95 (ms)"),
            ("retries_mean", "Retries medio"),
            ("any_retry_rate", "% con ≥1 retry"),
            ("patch_retries_total", "Patch retries (total)"),
            ("pass_first_rate", "Pass-first rate"),
            ("cache_hit_rate_global", "Cache hit rate global"),
        ):
            if key in section:
                out.append(f"| {label} | {section[key]} |")
        if section.get("top_hard"):
            out.append("\n**Top hard fails**: " +
                       ", ".join(f"{n}×{r}" for r, n in section["top_hard"]))
        if section.get("top_soft"):
            out.append("\n**Top soft fails**: " +
                       ", ".join(f"{n}×{r}" for r, n in section["top_soft"]))

    if baseline:
        out.append("\n\n## Comparación contra baseline\n")
        out.append("| Kind | Métrica | baseline | v7 | Δ |")
        out.append("|---|---|---|---|---|")
        for kind in ("M", "T", "S"):
            b = baseline.get("summary", {}).get("by_kind", {}).get(kind) or {}
            v = report["per_kind"].get(kind) or {}
            for key in ("cost_mean", "pass_first_rate", "any_retry_rate"):
                if key in v and key in b.get("cost_usd", {}) if key == "cost_mean" else key in v and key in b:
                    pass  # placeholder
            # cost medio baseline está en b['cost_usd']['mean'].
            if "cost_usd" in b and "cost_mean" in v:
                a = b["cost_usd"].get("mean")
                bv = v["cost_mean"]
                delta = f"{(bv - a) / a:+.1%}" if a else ""
                out.append(f"| {kind} | cost_mean | {a} | {bv} | {delta} |")
            if "pass_first_rate" in b and "pass_first_rate" in v:
                out.append(f"| {kind} | pass_first | {b['pass_first_rate']} | {v['pass_first_rate']} | |")

    out.append("\n\n## Episodios individuales\n")
    out.append("| Iter | Ep | Cost USD | Cache% | Retries | Patch | Hard | Soft | WC | Bloqueado |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in report["runs"]:
        it = r.get("iteration", 1)
        if r.get("error"):
            out.append(f"| {it} | {r['episode_id']} | ERROR: {r['error']} |||||||| |")
            continue
        cache_pct = "—"
        total = r["input_tokens"] + r["cache_read_tokens"]
        if total > 0:
            cache_pct = f"{100 * r['cache_read_tokens'] / total:.0f}%"
        out.append(
            f"| {it} | {r['episode_id']} | {r['cost_usd']:.4f} | {cache_pct} | "
            f"{r['retries_done']} | {r['patch_retries']} | {r['hard_failed']} | "
            f"{r['soft_failed']} | {r['word_count']} | "
            f"{'SÍ' if r['is_blocked'] else 'no'} |"
        )
    return "\n".join(out)


def _resolve_plan(plan: str) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    if plan == "smoke":
        return PLAN_M, PLAN_T, PLAN_S
    if plan == "produccion":
        return PROD_M, PROD_T, PROD_S
    raise ValueError(f"plan desconocido: {plan!r}")


def _estimate_total_usd(plan_m: list, plan_t: list, plan_s: list,
                         iteraciones: int) -> float:
    """Estimación cold-cache. Para iteraciones >1, asume cache caliente
    en las iteraciones 2..N (descuento medio 50% sobre M y T)."""
    one_iter = (
        len(plan_m) * _COST_ESTIMATE_USD["M"]
        + len(plan_t) * _COST_ESTIMATE_USD["T"]
        + len(plan_s) * _COST_ESTIMATE_USD["S"]
    )
    if iteraciones <= 1:
        return one_iter
    warm_iter = one_iter * 0.5  # asumimos -50% en runs warm cache
    return one_iter + warm_iter * (iteraciones - 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                         help="Solo verificación de entorno + estimación (sin gasto).")
    parser.add_argument("--run", action="store_true",
                         help="Ejecutar la suite (gasta API).")
    parser.add_argument("--plan", choices=["smoke", "produccion"], default="smoke",
                         help="smoke=2M+4T+5S (~$0.50). produccion=6M+11T+8S (~$2.50).")
    parser.add_argument("--iteraciones", type=int, default=1,
                         help="Veces que se repite el plan completo (smoke x3 valida caching).")
    parser.add_argument("--solo", choices=["M", "T", "S"], default=None,
                         help="Limita a un solo tipo.")
    parser.add_argument("--budget-usd", type=float, default=15.0,
                         help="Tope de gasto en USD. Aborta si el coste acumulado lo supera.")
    parser.add_argument("--con-prewriting-llm", action="store_true",
                         help="Activa MP_PREWRITING_LLM=1 (Haiku tool call).")
    parser.add_argument("--baseline", default=None,
                         help="JSON de baseline previo para comparar.")
    parser.add_argument("--salida", default=None,
                         help="Ruta del MD de salida (default: docs/<plan>_v7_<fecha>.md).")
    args = parser.parse_args()

    if not args.check and not args.run:
        parser.print_help()
        return 2

    plan_m, plan_t, plan_s = _resolve_plan(args.plan)
    if args.solo == "M":
        plan_t, plan_s = [], []
    elif args.solo == "T":
        plan_m, plan_s = [], []
    elif args.solo == "S":
        plan_m, plan_t = [], []

    issues = _check_env(plan_m, plan_t, plan_s)

    if issues:
        print("[!] PRE-FLIGHT - issues detectados:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("[OK] PRE-FLIGHT OK")

    n_per_iter = len(plan_m) + len(plan_t) + len(plan_s)
    n_total = n_per_iter * args.iteraciones
    estimate = _estimate_total_usd(plan_m, plan_t, plan_s, args.iteraciones)
    print(f"\nPlan '{args.plan}' x {args.iteraciones} iter: "
          f"{len(plan_m)} M + {len(plan_t)} T + {len(plan_s)} S "
          f"= {n_per_iter} eps/iter, {n_total} total")
    print(f"  M: {plan_m}")
    print(f"  T: {plan_t}")
    print(f"  S: {[ep for ep, _ in plan_s]}")
    print(f"\nCoste estimado: ~${estimate:.2f} USD (~{estimate * 0.92:.2f} EUR)")
    print(f"Budget cap: ${args.budget_usd:.2f} USD")
    if estimate > args.budget_usd:
        print("[ERROR] Estimación supera budget. Sube --budget-usd o reduce plan.")
        return 1

    if args.check or not args.run:
        if args.run and any("Falta ANTHROPIC_API_KEY" in i for i in issues):
            print("\n[ERROR] No se puede --run sin ANTHROPIC_API_KEY.")
            return 1
        if args.check:
            return 0 if not issues else 1

    if args.con_prewriting_llm:
        os.environ["MP_PREWRITING_LLM"] = "1"
        print("\nMP_PREWRITING_LLM=1 (Haiku tool call activo para pre-writing)")

    print(f"\n> Ejecutando {args.iteraciones} iteración(es). Esto gasta API real.")
    print(f"> Guiones se guardan en {OUTPUT_DIR_NAME}/<tipo>/<ep>[_iterN].txt\n")

    runs: list[dict] = []
    cost_acc = 0.0
    aborted = False

    for it in range(1, args.iteraciones + 1):
        if aborted:
            break
        print(f"\n=== Iteración {it}/{args.iteraciones} ===")
        todo: list[tuple[str, str, str | None]] = []
        todo.extend((ep, "M", None) for ep in plan_m)
        todo.extend((ep, "T", None) for ep in plan_t)
        todo.extend((ep, "S", term) for ep, term in plan_s)

        for i, (ep, kind, term) in enumerate(todo, 1):
            print(f"[iter{it} {i}/{len(todo)}] {kind} {ep}...")
            try:
                r = _run_one(ep, kind, term, iteration=it)
                r["iteration"] = it
                cost_acc += r["cost_usd"]
                tag = "OK" if not r["is_blocked"] else "BLOQUEADO"
                cache_pct = ""
                tot = r["input_tokens"] + r["cache_read_tokens"]
                if tot > 0:
                    cache_pct = f" cache={100 * r['cache_read_tokens'] / tot:.0f}%"
                print(f"  {tag} | ${r['cost_usd']:.4f}{cache_pct} | "
                      f"retries={r['retries_done']} patch={r['patch_retries']} "
                      f"wc={r['word_count']} hard={r['hard_failed']} soft={r['soft_failed']}")
                print(f"  acumulado: ${cost_acc:.4f} / ${args.budget_usd:.2f}")
                runs.append(r)
                if cost_acc > args.budget_usd:
                    print(f"\n[ABORT] Budget excedido (${cost_acc:.4f} > "
                          f"${args.budget_usd:.2f}). Parando.")
                    aborted = True
                    break
            except Exception as exc:  # noqa: BLE001
                print(f"  ERROR: {exc}")
                runs.append({"episode_id": ep, "kind": kind, "iteration": it,
                              "error": str(exc)})

    valid = [r for r in runs if "error" not in r]
    per_kind: dict[str, dict] = {}
    for kind in ("M", "T", "S"):
        items = [r for r in valid if r["kind"] == kind]
        if items:
            per_kind[kind] = _summarize(items)

    # Métricas por iteración para ver el efecto del caching.
    per_iter: dict[int, dict] = {}
    iters_present = sorted({r.get("iteration", 1) for r in valid})
    for it in iters_present:
        per_iter[it] = _summarize([r for r in valid if r.get("iteration") == it])

    report = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "variante": "v7",
        "plan": args.plan,
        "iteraciones": args.iteraciones,
        "budget_usd": args.budget_usd,
        "cost_acumulado_usd": round(cost_acc, 4),
        "aborted": aborted,
        "mp_prewriting_llm": os.environ.get("MP_PREWRITING_LLM", "0"),
        "n_total": len(runs),
        "n_ok": len(valid),
        "per_kind": per_kind,
        "per_iteration": per_iter,
        "runs": runs,
    }
    baseline = None
    if args.baseline:
        bpath = Path(args.baseline)
        if bpath.exists():
            baseline = json.loads(bpath.read_text(encoding="utf-8"))

    out_path = Path(args.salida) if args.salida else (
        REPO_ROOT / "docs"
        / f"{args.plan}_v7_iter{args.iteraciones}_{datetime.now():%Y%m%d_%H%M%S}.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_render_markdown(report, baseline=baseline),
                         encoding="utf-8")
    json_path = out_path.with_suffix(".json")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    print(f"\nReporte MD : {out_path}")
    print(f"Raw JSON   : {json_path}")
    print("CSV costes : logs/.. (auto) y costes_generacion.log (raíz)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="scripts/smoke_test_v7.py",
                            params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        sys.exit(main())
