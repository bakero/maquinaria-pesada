"""Entry point del evaluador."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .detect import detect_kind_from_filename, verify_kind_with_content
from .parser import parse_script
from .renderers.json_out import render_json
from .renderers.markdown import render_markdown
from .renderers.terminal import render_terminal
from .rules import evaluate_all


def discover_scripts(directory: Path, only_kind: str | None = None) -> list[Path]:
    """Encuentra .txt y .md en el directorio (no recursivo)."""
    candidates = sorted(
        list(directory.glob("*.txt")) + list(directory.glob("*.md"))
    )
    out = []
    for p in candidates:
        det = detect_kind_from_filename(p.name)
        if det.kind is None:
            continue
        if only_kind and det.kind != only_kind:
            continue
        out.append(p)
    return out


def evaluate_one(path: Path) -> dict:
    """Evalúa un único fichero y devuelve dict con metadata + findings."""
    det = detect_kind_from_filename(path.name)
    if det.kind is None:
        return {
            "filename": str(path),
            "kind": None,
            "metadata": {},
            "findings": [],
            "error": det.reason,
        }

    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return {
            "filename": str(path),
            "kind": det.kind,
            "metadata": {},
            "findings": [],
            "error": f"Error de lectura: {exc}",
        }

    ok, msg = verify_kind_with_content(det.kind, raw)
    pre_findings: list[dict] = []
    if not ok:
        pre_findings.append(
            {
                "code": "type_filename_content_mismatch",
                "severity": "hard",
                "line": None,
                "speaker": None,
                "section": None,
                "snippet": None,
                "message": msg,
                "autofixable": False,
            }
        )

    try:
        script = parse_script(path, det.kind)
    except Exception as exc:  # noqa: BLE001
        return {
            "filename": str(path),
            "kind": det.kind,
            "metadata": {},
            "findings": pre_findings,
            "error": f"Error de parsing: {exc}",
        }

    findings = evaluate_all(script)
    return {
        "filename": str(path),
        "kind": det.kind,
        "metadata": script.metadata,
        "findings": pre_findings + [f.to_dict() for f in findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evaluador",
        description="Evaluador de guiones MaquinarIA Pesada",
    )
    parser.add_argument("--dir", default="Guiones", help="Directorio (default: Guiones/)")
    parser.add_argument("--file", help="Evaluar un único fichero")
    parser.add_argument("--only-kind", choices=["M", "T", "S"], help="Filtrar por tipo")
    parser.add_argument("--md", help="Generar informe markdown en path")
    parser.add_argument("--json", dest="json_path", help="Generar informe JSON en path")
    parser.add_argument(
        "--strict", action="store_true", help="exit 1 también si hay soft-warns"
    )
    parser.add_argument(
        "--mode",
        default="check",
        choices=["check", "fix", "suggest"],
        help="Modo de operación (sólo 'check' implementado en v1)",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="No emitir informe a stdout"
    )
    parser.add_argument(
        "--check-run-log",
        metavar="DATE",
        nargs="?",
        const="today",
        help=(
            "Valida el día-log indicado (YYYY-MM-DD; 'today' = hoy) y "
            "reporta inconsistencias. Salida en stdout; exit 1 si hay issues."
        ),
    )

    args = parser.parse_args(argv)

    # ── Modo alterno: validar el día-log ──────────────────────────────────
    if args.check_run_log is not None:
        return _run_log_check(args.check_run_log)

    from cockpit.core.log_helpers import get_run_logger
    log = get_run_logger("evaluador")
    log.step("discover", directory=args.dir, only_kind=args.only_kind or "")

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"ERROR: fichero no existe: {path}", file=sys.stderr)
            return 2
        results = [evaluate_one(path)]
        directory = str(path.parent)
    else:
        directory = args.dir
        d_path = Path(directory)
        if not d_path.exists() or not d_path.is_dir():
            print(f"ERROR: directorio no existe: {directory}", file=sys.stderr)
            return 2
        scripts = discover_scripts(d_path, only_kind=args.only_kind)
        results = [evaluate_one(p) for p in scripts]
    log.step("evaluate", files=len(results))

    if not args.quiet:
        print(render_terminal(results, directory, args.mode))

    if args.md:
        Path(args.md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md).write_text(
            render_markdown(results, directory), encoding="utf-8"
        )
        print(f"[md] {args.md}", file=sys.stderr)

    if args.json_path:
        Path(args.json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_path).write_text(
            render_json(results, directory, args.mode, args.strict),
            encoding="utf-8",
        )
        print(f"[json] {args.json_path}", file=sys.stderr)

    has_hard = any(
        any(f["severity"] == "hard" for f in r.get("findings", [])) or r.get("error")
        for r in results
    )
    has_soft = any(
        any(f["severity"] == "soft" for f in r.get("findings", []))
        for r in results
    )

    n_hard = sum(
        sum(1 for f in r.get("findings", []) if f["severity"] == "hard")
        for r in results
    )
    n_soft = sum(
        sum(1 for f in r.get("findings", []) if f["severity"] == "soft")
        for r in results
    )
    if has_hard:
        log.warn("evaluación con hard-fails", files=len(results),
                 hard=n_hard, soft=n_soft)
        return 1
    if args.strict and has_soft:
        log.warn("evaluación con soft-warns en modo strict",
                 files=len(results), soft=n_soft)
        return 1
    log.ok("evaluación limpia", files=len(results), soft=n_soft)
    return 0


def _run_log_check(date_arg: str) -> int:
    """Implementación de `--check-run-log`: valida el día-log y reporta."""
    from datetime import date as _date

    from cockpit.core import log_validator

    if date_arg in ("today", "hoy", "*"):
        target_date = None
    else:
        try:
            y, m, d = [int(x) for x in date_arg.split("-")]
            target_date = _date(y, m, d)
        except (ValueError, AttributeError):
            print(
                f"ERROR: fecha inválida '{date_arg}' (esperado YYYY-MM-DD o 'today')",
                file=sys.stderr,
            )
            return 2

    reports = log_validator.validate_day(target_date)
    if not reports:
        target_label = date_arg if date_arg not in ("today", "hoy", "*") else "hoy"
        print(f"(no hay runs registrados en el día-log de {target_label})")
        return 0

    print(f"# Validación de día-log · {len(reports)} ejecuciones\n")
    has_issues = False
    for rid, rep in sorted(reports.items()):
        sev = "OK" if rep.ok else "ISSUE"
        bits = [f"run={rid}", f"script={rep.run.script}", f"status={rep.run.status}"]
        if rep.run.elapsed_s is not None:
            bits.append(f"elapsed={rep.run.elapsed_s}s")
        if rep.run.ai_calls_started:
            bits.append(
                f"ai={rep.run.ai_calls_ok}/{rep.run.ai_calls_started}"
                + (f"(err={rep.run.ai_calls_error})" if rep.run.ai_calls_error else "")
            )
        if rep.run.retries:
            bits.append(f"retries={rep.run.retries}")
        print(f"[{sev}] {' '.join(bits)}")
        for issue in rep.issues:
            print(f"   - issue: {issue}")
            has_issues = True
        for warn in rep.warnings:
            print(f"   - warn:  {warn}")
    return 1 if has_issues else 0


if __name__ == "__main__":  # pragma: no cover
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="evaluador/cli.py", params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        sys.exit(main())
