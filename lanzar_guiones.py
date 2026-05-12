#!/usr/bin/env python3
"""
lanzar_guiones.py — Lanzador batch de generación de guiones.

Ejecuta generar_guion.py (M) y generar_guion_t.py (T) en secuencia.
Cada guion tiene su propio log en Guiones/logs/{guion}_gen.log.
Log maestro en Guiones/logs/guiones_runs.log.

Uso:
  python lanzar_guiones.py          # genera todos los configurados
  python lanzar_guiones.py --dry-run
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
LOG_DIR  = BASE_DIR / "Guiones" / "logs"

# ---------------------------------------------------------------------------
# Episodios M a generar (M0–M14)
# ---------------------------------------------------------------------------

M_EPISODES = [
    (0,  "PDFs/resumenes/RESUMEN_M0_Introduccion_Estrategica.pdf"),
    (1,  "PDFs/resumenes/RESUMEN_M1_Fundamentos_Razonamiento.pdf"),
    (2,  "PDFs/resumenes/RESUMEN_M2_Matematicas_Fundamentos.pdf"),
    (3,  "PDFs/resumenes/RESUMEN_M3_Machine_Learning_Clasico.pdf"),
    (4,  "PDFs/resumenes/RESUMEN_M4_Deep_Learning.pdf"),
    (5,  "PDFs/resumenes/RESUMEN_M5_NLP_LLMs.pdf"),
    (6,  "PDFs/resumenes/RESUMEN_M6_Ingenieria_Prompts.pdf"),
    (7,  "PDFs/resumenes/RESUMEN_M7_Sistemas_RAG.pdf"),
    (8,  "PDFs/resumenes/RESUMEN_M8_Ingenieria_LLMOps.pdf"),
    (9,  "PDFs/resumenes/RESUMEN_M9_Infraestructura_Despliegue.pdf"),
    (10, "PDFs/resumenes/RESUMEN_M10_Sistemas_Agentes.pdf"),
    (11, "PDFs/resumenes/RESUMEN_M11_Automatizacion.pdf"),
    (12, "PDFs/resumenes/RESUMEN_M12_Seguridad_IA.pdf"),
    (13, "PDFs/resumenes/RESUMEN_M13_Gobernanza_Etica.pdf"),
    (14, "PDFs/resumenes/RESUMEN_M14_Estrategia_Empresa.pdf"),
]

# ---------------------------------------------------------------------------
# Episodios T a generar
# ---------------------------------------------------------------------------

T_EPISODES = [
    "PDFs/temas/M1_T10_tokenizacion.pdf",
    "PDFs/temas/M1_T11_limitaciones_llms.pdf",
    "PDFs/temas/M12_T2_prompt_injection.pdf",
    "PDFs/temas/M8_T1_ciclo_vida_modelos_llm.pdf",
    "PDFs/temas/M7_T1_que_es_rag.pdf",
    "PDFs/temas/M3_T2_modelos_clasicos.pdf",
    "PDFs/temas/M10_T5_tool_use_function_calling.pdf",
]


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append_master_log(entry: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "guiones_runs.log").open("a", encoding="utf-8") as fh:
        fh.write(entry + "\n")


def run_cmd(label: str, cmd: list[str], log_name: str, dry_run: bool) -> bool:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / log_name

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {label}")
    if dry_run:
        print(f"  CMD: {' '.join(cmd)}")
        print("  [DRY-RUN]")
        return True

    started = ts()
    print(f"  Inicio: {started}")
    sys.stdout.flush()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        finished   = ts()
        ok         = result.returncode == 0
        stdout     = result.stdout
        stderr     = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        finished, ok, returncode = ts(), False, -1
        stdout = getattr(exc, "stdout", "") or ""
        stderr = "[TIMEOUT] >10 min\n"
    except Exception as exc:
        finished, ok, returncode = ts(), False, -1
        stdout, stderr = "", f"[ERROR] {exc}\n"

    status = "OK" if ok else "FALLO"
    header = (
        f"{'='*60}\n{label}\nCMD: {' '.join(cmd)}\n"
        f"INICIO: {started}\nFIN: {finished}\nEXIT: {returncode} ({status})\n{'='*60}\n\n"
    )
    log_path.write_text(
        header
        + "--- STDOUT ---\n" + (stdout or "(vacío)") + "\n"
        + ("--- STDERR ---\n" + stderr if stderr and stderr.strip() else ""),
        encoding="utf-8",
    )

    print(f"  Fin: {finished}  [{status}]")
    if not ok:
        lines = [ln for ln in (stderr + stdout).splitlines() if ln.strip()]
        hint = lines[-1][:200] if lines else "(sin output)"
        print(f"  ERROR: {hint}")

    master_line = f"[{finished}] {status:5s} | {label}"
    if not ok:
        lines = [ln for ln in (stderr + stdout).splitlines() if ln.strip()]
        master_line += f"\n             error: {lines[-1][:200] if lines else '?'}"
    append_master_log(master_line)

    return ok


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    run_ts = ts()
    total  = len(M_EPISODES) + len(T_EPISODES)
    print(f"\n{'='*60}")
    print(f"  LANZADOR DE GUIONES — MaquinarIA Pesada")
    print(f"  {run_ts}")
    print(f"  Total a generar: {total} ({len(M_EPISODES)} M + {len(T_EPISODES)} T)")
    print(f"{'='*60}")

    append_master_log(
        f"\n{'='*60}\nINICIO: {run_ts}\nTotal: {total} ({len(M_EPISODES)} M + {len(T_EPISODES)} T)\n{'='*60}"
    )

    ok_list:   list[str] = []
    fail_list: list[str] = []

    # ── Episodios M ──────────────────────────────────────────────────────────
    for modulo_n, pdf_rel in M_EPISODES:
        # Si ya existe el guion, saltar
        guion_dir = BASE_DIR / "Guiones"
        existing = list(guion_dir.glob(f"M{modulo_n}_*.txt"))
        existing = [f for f in existing if not f.name.startswith(f"M{modulo_n}_TX_")]
        if existing:
            label = f"M{modulo_n} — ya existe ({existing[0].name})"
            print(f"\n  [SKIP] {label}")
            append_master_log(f"[SKIP]  {label}")
            ok_list.append(f"M{modulo_n}")
            continue

        label    = f"M{modulo_n} ({Path(pdf_rel).stem})"
        log_name = f"M{modulo_n}_gen.log"
        cmd      = [sys.executable, "generar_guion.py", "--modulo", str(modulo_n), "--pdf", pdf_rel]

        if run_cmd(label, cmd, log_name, dry_run):
            ok_list.append(f"M{modulo_n}")
        else:
            fail_list.append(f"M{modulo_n}")

    # ── Episodios T ──────────────────────────────────────────────────────────
    for pdf_rel in T_EPISODES:
        pdf_path  = Path(pdf_rel)
        stem      = pdf_path.stem  # M1_T11_limitaciones_llms
        label     = f"T: {stem}"
        log_name  = f"{stem}_gen.log"

        # Si ya existe el guion, saltar
        import re as _re
        mod_match = _re.match(r"M(\d+)_", stem)
        if mod_match:
            modulo_n = mod_match.group(1)
            topic    = _re.sub(r"^M\d+_", "", stem)
            guion_dir = BASE_DIR / "Guiones"
            expected  = guion_dir / f"M{modulo_n}_TX_{topic}.txt"
            if expected.exists():
                print(f"\n  [SKIP] {label} — ya existe ({expected.name})")
                append_master_log(f"[SKIP]  {label}")
                ok_list.append(stem)
                continue

        cmd = [sys.executable, "generar_guion_t.py", "--pdf", pdf_rel]

        if run_cmd(label, cmd, log_name, dry_run):
            ok_list.append(stem)
        else:
            fail_list.append(stem)

    end_ts = ts()
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  RESUMEN — {end_ts}")
    print(f"  OK    ({len(ok_list)}): {', '.join(ok_list) or '--'}")
    print(f"  FALLO ({len(fail_list)}): {', '.join(fail_list) or '--'}")
    if fail_list:
        print(f"\n  Logs en: Guiones/logs/")
    print(f"\n  Log maestro: Guiones/logs/guiones_runs.log")

    append_master_log(
        f"FIN: {end_ts}\nOK ({len(ok_list)}): {', '.join(ok_list) or '--'}\n"
        f"FALLO ({len(fail_list)}): {', '.join(fail_list) or '--'}\n{'-'*60}"
    )


if __name__ == "__main__":
    main()
