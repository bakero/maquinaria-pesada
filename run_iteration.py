#!/usr/bin/env python3
# ruff: noqa
"""run_iteration.py — Lanza una iteración de prueba de generación de guiones.

🚫 SCRIPT LEGACY — RETIRADO 2026-05-19.
   Encadenaba el legacy `generar_guion.py` / `generar_guion_t.py`. El
   pipeline canónico vivo es `lanzar_produccion.py`. Para iterar varios
   episodios usa `lanzar_guiones.py`. Ver `GENERACION.md`.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.stderr.write(
        "\n❌ run_iteration.py está retirado.\n"
        "   Encadenaba scripts legacy ya eliminados.\n"
        "   Para batch usa:\n"
        "       python lanzar_guiones.py\n"
        "   Ver GENERACION.md para el mapa completo.\n\n"
    )
    raise SystemExit(2)

# ---- Código histórico inaccesible ----------------------------------------
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent

EPISODES = [
    {
        "id": "RESUMEN_M6_Ingenieria_Prompts",
        "type": "M",
        "cmd": [
            sys.executable, "generar_guion.py",
            "--modulo", "6",
            "--pdf", "PDFs/resumenes/RESUMEN_M6_Ingenieria_Prompts.pdf",
            "--nombre", "Ingenieria_Prompts",
            "--max-intentos", "4",
        ],
        "guion": "Guiones/M6_Ingenieria_Prompts.txt",
        "spec": "PODCAST_M_SPEC.md",
    },
    {
        "id": "RESUMEN_M7_Sistemas_RAG",
        "type": "M",
        "cmd": [
            sys.executable, "generar_guion.py",
            "--modulo", "7",
            "--pdf", "PDFs/resumenes/RESUMEN_M7_Sistemas_RAG.pdf",
            "--nombre", "Sistemas_RAG",
            "--max-intentos", "4",
        ],
        "guion": "Guiones/M7_Sistemas_RAG.txt",
        "spec": "PODCAST_M_SPEC.md",
    },
    {
        "id": "RESUMEN_M8_Ingenieria_LLMOps",
        "type": "M",
        "cmd": [
            sys.executable, "generar_guion.py",
            "--modulo", "8",
            "--pdf", "PDFs/resumenes/RESUMEN_M8_Ingenieria_LLMOps.pdf",
            "--nombre", "Ingenieria_LLMOps",
            "--max-intentos", "4",
        ],
        "guion": "Guiones/M8_Ingenieria_LLMOps.txt",
        "spec": "PODCAST_M_SPEC.md",
    },
    {
        "id": "M3_T2_modelos_clasicos",
        "type": "T",
        "cmd": [
            sys.executable, "generar_guion_t.py",
            "--pdf", "PDFs/temas/M3_T2_modelos_clasicos.pdf",
            "--max-intentos", "3",
        ],
        "guion": "Guiones/M3_T2_modelos_clasicos.txt",
        "spec": "PODCAST_T_SPEC.md",
    },
    {
        "id": "M7_T1_que_es_rag",
        "type": "T",
        "cmd": [
            sys.executable, "generar_guion_t.py",
            "--pdf", "PDFs/temas/M7_T1_que_es_rag.pdf",
            "--max-intentos", "3",
        ],
        "guion": "Guiones/M7_T1_que_es_rag.txt",
        "spec": "PODCAST_T_SPEC.md",
    },
    {
        "id": "M10_T5_tool_use_function_calling",
        "type": "T",
        "cmd": [
            sys.executable, "generar_guion_t.py",
            "--pdf", "PDFs/temas/M10_T5_tool_use_function_calling.pdf",
            "--max-intentos", "3",
        ],
        "guion": "Guiones/M10_T5_tool_use_function_calling.txt",
        "spec": "PODCAST_T_SPEC.md",
    },
]


def validate_guion(guion_path: Path, spec_path: Path) -> tuple[list[str], list[str]]:
    """Validates guion and returns (hard_issues, soft_issues)."""
    sys.path.insert(0, str(BASE_DIR))
    from podcast_spec import guion_to_ep_code, load_spec, validate_script_text

    spec = load_spec(str(spec_path))
    ep_code = guion_to_ep_code(guion_path.stem)
    text = guion_path.read_text(encoding="utf-8")
    issues = validate_script_text(text, ep_code, spec)
    hard = [i for i in issues if not i.startswith("[WARN]")]
    soft = [i for i in issues if i.startswith("[WARN]")]
    return hard, soft


def run_episode(ep: dict, log_dir: Path, delete_existing: bool) -> dict:
    guion_path = BASE_DIR / ep["guion"]
    spec_path = BASE_DIR / ep["spec"]

    if delete_existing and guion_path.exists():
        guion_path.unlink()
        print(f"  [DEL] {guion_path.name}")

    print(f"  [GEN] {ep['id']} ...", flush=True)
    t0 = datetime.now()
    result = subprocess.run(
        ep["cmd"],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        timeout=600,
    )
    elapsed = (datetime.now() - t0).total_seconds()

    full_log = result.stdout + ("\n--- STDERR ---\n" + result.stderr if result.stderr.strip() else "")

    # Save full log
    log_file = log_dir / f"{ep['id']}.log"
    log_file.write_text(full_log, encoding="utf-8")

    # Validate generated guion
    hard: list[str] = []
    soft: list[str] = []
    gen_ok = guion_path.exists()

    if gen_ok:
        try:
            hard, soft = validate_guion(guion_path, spec_path)
        except Exception as e:
            hard = [f"ERROR en validación: {e}"]

    report = {
        "id": ep["id"],
        "type": ep["type"],
        "generated": gen_ok,
        "returncode": result.returncode,
        "elapsed_s": round(elapsed, 1),
        "hard_count": len(hard),
        "soft_count": len(soft),
        "hard_issues": hard,
        "soft_issues": soft,
    }

    # Save structured report
    report_file = log_dir / f"{ep['id']}.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not gen_ok:
        status = "NO_GENERADO"
    elif hard:
        status = f"HARD:{len(hard)}"
    else:
        status = "OK"
    print(f"    → {status} | soft:{len(soft)} | {elapsed:.0f}s")
    for h in hard:
        print(f"      [HARD] {h}")
    for s in soft:
        print(f"      [soft] {s}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera 6 episodios y guarda logs/informes")
    parser.add_argument("--iter", type=int, required=True, help="Número de iteración (1-4)")
    parser.add_argument("--delete-existing", action="store_true", help="Borrar guion existente antes de generar")
    parser.add_argument("--episode", help="Generar solo este episodio (por id)")
    args = parser.parse_args()

    log_dir = BASE_DIR / "logs" / "guiones" / f"it{args.iter}"
    log_dir.mkdir(parents=True, exist_ok=True)

    episodes = EPISODES
    if args.episode:
        episodes = [e for e in EPISODES if e["id"] == args.episode]
        if not episodes:
            print(f"ERROR: episodio '{args.episode}' no encontrado")
            sys.exit(1)

    print(f"\n=== ITERACIÓN {args.iter} — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    print(f"Log dir: {log_dir}")

    all_reports = []
    for ep in episodes:
        report = run_episode(ep, log_dir, args.delete_existing)
        all_reports.append(report)

    # Save summary
    summary = {
        "iter": args.iter,
        "timestamp": datetime.now().isoformat(),
        "episodes": all_reports,
        "total_hard": sum(r["hard_count"] for r in all_reports),
        "total_soft": sum(r["soft_count"] for r in all_reports),
        "all_generated": all(r["generated"] for r in all_reports),
    }
    summary_file = log_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n--- RESUMEN ITERACIÓN {args.iter} ---")
    print(f"Total HARD: {summary['total_hard']}")
    print(f"Total soft: {summary['total_soft']}")
    for r in all_reports:
        status = "✓" if not r["hard_issues"] else "✗"
        print(f"  {status} {r['id']}: hard={r['hard_count']} soft={r['soft_count']}")
    print(f"Summary: {summary_file}")


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="run_iteration.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
