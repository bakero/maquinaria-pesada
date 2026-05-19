#!/usr/bin/env python3
"""CLI de generación de episodios — único pipeline activo.

Soporta los 3 formatos del corpus con `--kind`. Delega cada llamada en el
generador especialista del paquete `generadores/`. Ver `GENERACION.md`
para el mapa completo.

Uso:
    python lanzar_produccion.py --kind M --ep M3
    python lanzar_produccion.py --kind T --ep M3_T2
    python lanzar_produccion.py --kind S --ep S1_RAG --term RAG

Cada llamada usa el generador especialista correspondiente
(`generadores.m_generator`, `t_generator`, `s_generator`), que a su vez:
  - lee las fuentes pertinentes (PDF resumen/tema, glosario, fuentes-marco),
  - construye el prompt con la pre-escritura inyectada,
  - llama al LLM (Sonnet para M/T, Haiku para S),
  - aplica post-process (num2words + pronunciation_overrides + SSML pauses),
  - valida con el validador del formato,
  - reintenta con feedback explícito si hay hard-fail,
  - registra la corrida en `costes_generacion.log`,
  - guarda el guion final en `Guiones/<ep>.md`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generadores import m_generator, s_generator, t_generator
from validators.result import summarize


def _save_script(text: str, ep: str, repo_root: Path) -> Path:
    out = repo_root / "Guiones" / f"{ep}_v6.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def _run(kind: str, args: argparse.Namespace, repo_root: Path):
    if kind == "M":
        return m_generator.generate(args.ep, repo_root=repo_root)
    if kind == "T":
        return t_generator.generate(args.ep, repo_root=repo_root)
    if kind == "S":
        if not args.term:
            raise SystemExit("--term es obligatorio para --kind S")
        return s_generator.generate(args.ep, term=args.term, repo_root=repo_root)
    raise SystemExit(f"--kind debe ser M, T o S (recibido: {kind})")


def main(argv: list[str] | None = None) -> int:
    from cockpit.core.log_helpers import get_run_logger
    log = get_run_logger("lanzar_produccion")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", required=True, choices=["M", "T", "S"])
    ap.add_argument("--ep", required=True, help="id del episodio (M3, M3_T2, S1_RAG)")
    ap.add_argument("--term", default=None, help="término del glosario (solo S)")
    ap.add_argument("--repo-root", default=".", type=Path)
    ap.add_argument("--dry-run", action="store_true",
                    help="no guarda el guion, solo muestra el resumen")
    args = ap.parse_args(argv)

    repo_root = args.repo_root.resolve()
    print(f"\n=== Generando {args.kind} · {args.ep} ===")
    log.step("plan", kind=args.kind, ep=args.ep, dry_run=args.dry_run)

    log.step("produce", kind=args.kind, ep=args.ep)
    result = _run(args.kind, args, repo_root)
    gen = result.generation
    print(f"  Modelo:          {gen.model}")
    print(f"  Tokens input:    {gen.input_tokens}")
    print(f"  Tokens output:   {gen.output_tokens}")
    print(f"  Coste estimado:  {gen.cost_usd:.4f} USD")
    log.info("generación completada",
             model=gen.model, tokens_in=gen.input_tokens,
             tokens_out=gen.output_tokens, cost_usd=round(gen.cost_usd, 4))
    if result.used_retry:
        rg = result.retry_generation
        log.retry(attempt=2, reason="validation_hard_fail",
                  extra_tokens_out=rg.output_tokens, extra_cost_usd=round(rg.cost_usd, 4))
        print(f"  Retry aplicado:  +{rg.output_tokens} tokens output, "
              f"+{rg.cost_usd:.4f} USD")
    if not gen.ok:
        log.error("generación falló", error=str(gen.error)[:200])
        print(f"  ERROR generación: {gen.error}")
        return 2

    log.step("validate")
    summary = summarize(result.validation_results)
    log.info("validación", passed=summary["passed"], total=summary["total"],
             hard_failed=summary["hard_failed"], soft_failed=summary["soft_failed"])
    print(f"  Validación:      {summary['passed']}/{summary['total']} reglas "
          f"OK (hard-fail: {summary['hard_failed']}, soft-warn: "
          f"{summary['soft_failed']})")
    for r in result.validation_results:
        if not r.passed and r.severity == "HARD":
            print(f"    × {r.rule_name}: {r.message}")

    if args.dry_run:
        print("  [dry-run] guion NO guardado")
        log.info("dry-run · guion no guardado")
        return 0 if not summary["blocking"] else 1

    log.step("save")
    out = _save_script(result.final_text, args.ep, repo_root)
    print(f"  Guion guardado:  {out.relative_to(repo_root).as_posix()}")
    if summary["blocking"]:
        log.warn("guion guardado con hard-fails de validación", path=str(out))
    else:
        log.ok("guion guardado", path=str(out))
    return 0 if not summary["blocking"] else 1


if __name__ == "__main__":  # pragma: no cover
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="lanzar_produccion.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        raise SystemExit(main())
