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

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
LOG_DIR  = BASE_DIR / "Guiones" / "logs"

# El mapeo episodio → PDF + script vive en un único sitio compartido con
# web_server.py (generación bajo demanda desde la app visual).
sys.path.insert(0, str(BASE_DIR))
from cockpit.core.episode_sources import EpisodeSource, all_sources  # noqa: E402


def guion_exists(src: EpisodeSource) -> Path | None:
    """Devuelve el guion ya generado para esta fuente, o None."""
    guion_dir = BASE_DIR / "Guiones"
    if src.kind == "M":
        modulo_n = src.module[1:]
        for f in guion_dir.glob(f"M{modulo_n}_*.txt"):
            # Excluir guiones T (naming actual Mn_Tk_ y legacy Mn_TX_Tk_).
            if not re.match(rf"M{modulo_n}_(?:TX_)?T\d+_", f.name, re.IGNORECASE):
                return f
        return None
    # T: "M7_T1" → Guiones/M7_T1_*.txt (legacy: Guiones/M7_TX_T1_*.txt)
    m = re.fullmatch(r"M(\d+)_T(\d+)", src.ep_id)
    if not m:
        return None
    matches = (
        list(guion_dir.glob(f"M{m.group(1)}_T{m.group(2)}_*.txt"))
        + list(guion_dir.glob(f"M{m.group(1)}_TX_T{m.group(2)}_*.txt"))
    )
    return matches[0] if matches else None


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

    sources = all_sources()
    n_m = sum(1 for s in sources if s.kind == "M")
    n_t = sum(1 for s in sources if s.kind == "T")
    total = len(sources)

    run_ts = ts()
    print(f"\n{'='*60}")
    print("  LANZADOR DE GUIONES — MaquinarIA Pesada")
    print(f"  {run_ts}")
    print(f"  Total a generar: {total} ({n_m} M + {n_t} T)")
    print(f"{'='*60}")

    append_master_log(
        f"\n{'='*60}\nINICIO: {run_ts}\nTotal: {total} ({n_m} M + {n_t} T)\n{'='*60}"
    )

    ok_list:   list[str] = []
    fail_list: list[str] = []

    for src in sources:
        # Si ya existe el guion, saltar
        existing = guion_exists(src)
        if existing:
            label = f"{src.ep_id} — ya existe ({existing.name})"
            print(f"\n  [SKIP] {label}")
            append_master_log(f"[SKIP]  {label}")
            ok_list.append(src.ep_id)
            continue

        label    = f"{src.ep_id} ({Path(src.pdf).stem})"
        log_name = f"{src.ep_id}_gen.log"
        cmd      = [sys.executable, src.script, *src.flags]

        if run_cmd(label, cmd, log_name, dry_run):
            ok_list.append(src.ep_id)
        else:
            fail_list.append(src.ep_id)

    end_ts = ts()
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  RESUMEN — {end_ts}")
    print(f"  OK    ({len(ok_list)}): {', '.join(ok_list) or '--'}")
    print(f"  FALLO ({len(fail_list)}): {', '.join(fail_list) or '--'}")
    if fail_list:
        print("\n  Logs en: Guiones/logs/")
    print("\n  Log maestro: Guiones/logs/guiones_runs.log")

    append_master_log(
        f"FIN: {end_ts}\nOK ({len(ok_list)}): {', '.join(ok_list) or '--'}\n"
        f"FALLO ({len(fail_list)}): {', '.join(fail_list) or '--'}\n{'-'*60}"
    )


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="lanzar_guiones.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
