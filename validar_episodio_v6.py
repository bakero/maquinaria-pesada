#!/usr/bin/env python3
"""CLI de validación de guiones v6 — usa los validadores nuevos.

Este es el reemplazo de `validar_episodio.py` para los formatos v6 (M, T, S).
Coexiste con el legacy mientras se migra el cockpit y los entrypoints
existentes. Cuando esos llamen al nuevo pipeline, `validar_episodio.py` legacy
puede eliminarse junto con `podcast_spec.py`.

Uso:
    python validar_episodio_v6.py --kind M --ep M3 --guion Guiones/M3.txt
    python validar_episodio_v6.py --kind T --ep M3_T2 --guion ...
    python validar_episodio_v6.py --kind S --ep S1_RAG --guion ... \\
        --s-number 1 --voice IAGO --filename S1_RAG.mp3
"""
from __future__ import annotations

import argparse
from pathlib import Path

from validators import m_validator, s_validator, t_validator
from validators.result import summarize


def _read_guion(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _validate(kind: str, args: argparse.Namespace, text: str, repo_root: Path):
    if kind == "M":
        return m_validator.validate(text, args.ep, repo_root=repo_root)
    if kind == "T":
        return t_validator.validate(text, args.ep)
    if kind == "S":
        return s_validator.validate(
            text, args.ep,
            s_number=args.s_number, voice=args.voice, filename=args.filename,
        )
    raise SystemExit(f"--kind debe ser M, T o S (recibido: {kind})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", required=True, choices=["M", "T", "S"])
    ap.add_argument("--ep", required=True, help="id del episodio (M3, M3_T2, S1_RAG...)")
    ap.add_argument("--guion", required=True, type=Path, help="ruta al fichero del guion")
    ap.add_argument("--repo-root", default=".", type=Path)
    ap.add_argument("--s-number", type=int, default=None, help="solo para S")
    ap.add_argument("--voice", default=None, choices=[None, "IAGO", "MARIA"])
    ap.add_argument("--filename", default=None, help="solo para S")
    args = ap.parse_args(argv)

    if not args.guion.exists():
        raise SystemExit(f"No existe el guion: {args.guion}")
    repo_root = args.repo_root.resolve()
    text = _read_guion(args.guion)

    results = _validate(args.kind, args, text, repo_root)
    summary = summarize(results)

    print(f"\n=== Validación {args.kind} · {args.ep} ===")
    print(f"  Total reglas:    {summary['total']}")
    print(f"  Pasaron:         {summary['passed']}")
    print(f"  Hard-fail:       {summary['hard_failed']}")
    print(f"  Soft-warn:       {summary['soft_failed']}")
    if summary["hard_failures"]:
        print("\n  Reglas HARD no superadas:")
        for r in results:
            if r.severity == "HARD" and not r.passed:
                print(f"    × {r.rule_name}: {r.message}")
    if summary["soft_warnings"]:
        print("\n  Advertencias SOFT:")
        for r in results:
            if r.severity == "SOFT" and not r.passed:
                print(f"    ! {r.rule_name}: {r.message}")
    print()
    return 1 if summary["blocking"] else 0


if __name__ == "__main__":  # pragma: no cover
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="validar_episodio_v6.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        raise SystemExit(main())
