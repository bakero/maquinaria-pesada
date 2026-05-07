#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lanzar_produccion.py
--------------------
Ejecuta todos los episodios pendientes de audio.
Captura stdout + stderr completos en episodios/{ep}_cmd.log.
Acumula un log maestro en episodios/produccion_runs.log.

Uso:
  python lanzar_produccion.py              # todos los pendientes
  python lanzar_produccion.py --ep M3_E_Machine_Learning_Clasico
  python lanzar_produccion.py --dry-run    # muestra comandos sin ejecutar

Logs generados:
  episodios/{ep}_cmd.log        stdout+stderr completo de cada episodio
  episodios/produccion_runs.log acumula todas las sesiones con timestamps
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(__file__).parent
EPISODIOS_DIR = BASE_DIR / "episodios"
MASTER_LOG    = EPISODIOS_DIR / "produccion_runs.log"

sys.path.insert(0, str(BASE_DIR))
from estado_proyecto import scan, GUIONES_DIR, AUDIO_DIR, GUION_RE, AUDIO_RE


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pendientes() -> list[tuple[str, Path]]:
    """Devuelve [(ep_code, guion_path)] para modulos con guion pero sin audio."""
    guiones = scan(GUIONES_DIR, GUION_RE)
    audios  = scan(AUDIO_DIR,   AUDIO_RE)
    result  = []
    for mod, guion_path in sorted(guiones.items()):
        if mod not in audios:
            ep_code = guion_path.stem.replace("_T_", "_E_", 1)
            result.append((ep_code, guion_path))
    return result


def cmd_log_path(ep_code: str) -> Path:
    EPISODIOS_DIR.mkdir(parents=True, exist_ok=True)
    return EPISODIOS_DIR / f"{ep_code}_cmd.log"


def append_master_log(entry: str) -> None:
    EPISODIOS_DIR.mkdir(parents=True, exist_ok=True)
    with MASTER_LOG.open("a", encoding="utf-8") as fh:
        fh.write(entry + "\n")


def _extract_error_hint(stdout: str, stderr: str) -> str:
    """Extrae la linea de error mas informativa del output combinado."""
    combined = (stderr + "\n" + stdout).splitlines()
    priority = [
        ln.strip() for ln in combined
        if any(kw in ln for kw in ("Error", "Exception", "FATAL", "Traceback", "SystemExit"))
    ]
    if priority:
        return priority[-1][:200]
    nonempty = [ln.strip() for ln in combined if ln.strip()]
    return nonempty[-1][:200] if nonempty else "(sin output)"


def run_episode(ep_code: str, guion_path: Path, dry_run: bool) -> bool:
    """Ejecuta generar_episodio_v2.py para un episodio. Devuelve True si OK."""
    cmd = [
        sys.executable,
        str(BASE_DIR / "generar_episodio_v2.py"),
        "--guion", str(guion_path.relative_to(BASE_DIR)),
        "--ep",    ep_code,
    ]
    log_path = cmd_log_path(ep_code)

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  EPISODIO : {ep_code}")
    print(f"  Guion    : {guion_path.name}")
    print(f"  Log cmd  : {log_path.name}")

    if dry_run:
        print(f"  CMD      : {' '.join(cmd)}")
        print("  [DRY-RUN - no se ejecuta]")
        return True

    started = ts()
    print(f"  Inicio   : {started}")
    print("  Ejecutando... (puede tardar varios minutos)")
    sys.stdout.flush()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
        finished = ts()
        ok       = result.returncode == 0
        stdout   = result.stdout
        stderr   = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        finished   = ts()
        ok         = False
        stdout     = getattr(exc, "stdout", "") or ""
        stderr     = "[TIMEOUT] El proceso supero 30 minutos de ejecucion.\n"
        returncode = -1
    except Exception as exc:
        finished   = ts()
        ok         = False
        stdout     = ""
        stderr     = f"[EXCEPCION EN LANZADOR] {type(exc).__name__}: {exc}\n"
        returncode = -1

    status_str = "OK" if ok else "FALLO"

    # ── Log por episodio ──────────────────────────────────────────────────────
    header_log = (
        f"{'='*60}\n"
        f"EPISODIO : {ep_code}\n"
        f"GUION    : {guion_path}\n"
        f"COMANDO  : {' '.join(cmd)}\n"
        f"INICIO   : {started}\n"
        f"FIN      : {finished}\n"
        f"EXIT     : {returncode} ({status_str})\n"
        f"{'='*60}\n\n"
    )
    stdout_section = (
        "--- STDOUT ---\n"
        + (stdout if stdout.strip() else "(vacio)\n")
        + "\n"
    )
    stderr_section = (
        ("\n--- STDERR ---\n" + stderr + "\n")
        if stderr and stderr.strip() else ""
    )
    log_path.write_text(header_log + stdout_section + stderr_section, encoding="utf-8")

    # ── Log maestro ──────────────────────────────────────────────────────────
    master_line = f"[{finished}] {status_str:5s} | {ep_code} | log: {log_path.name}"
    if not ok:
        hint = _extract_error_hint(stdout, stderr)
        master_line += f"\n              error: {hint}"
    append_master_log(master_line)

    # ── Consola ──────────────────────────────────────────────────────────────
    print(f"  Fin      : {finished}  [{status_str}]")
    print(f"  Log      : {log_path}")

    if not ok:
        print(f"\n  {'-'*56}")
        print("  ERROR - detalle:")
        hint = _extract_error_hint(stdout, stderr)
        print(f"    {hint}")

        stdout_tail = [ln for ln in stdout.splitlines() if ln.strip()][-8:]
        if stdout_tail:
            print(f"\n  [stdout - ultimas {len(stdout_tail)} lineas]")
            for ln in stdout_tail:
                print(f"    {ln}")

        stderr_lines = [ln for ln in stderr.splitlines() if ln.strip()]
        if stderr_lines:
            max_show = 20
            label = "completo" if len(stderr_lines) <= max_show else f"ultimas {max_show} lineas"
            print(f"\n  [stderr - {label}]")
            for ln in stderr_lines[-max_show:]:
                print(f"    {ln}")

        print(f"  {'-'*56}")
        print(f"  -> Log completo: episodios/{log_path.name}")

    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Lanzador de produccion de episodios")
    parser.add_argument("--ep",      default=None, help="Generar solo este episodio (ep_code exacto)")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar comandos sin ejecutar")
    args = parser.parse_args()

    todos = pendientes()

    if not todos:
        print("No hay episodios pendientes de audio.")
        return

    if args.ep:
        todos = [(ep, g) for ep, g in todos if ep == args.ep]
        if not todos:
            print(f"No se encontro '{args.ep}' en la lista de pendientes.")
            return

    run_ts = ts()
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  LANZADOR DE PRODUCCION - {run_ts}")
    print(f"  Log maestro: {MASTER_LOG}")
    print(f"  Episodios pendientes: {len(todos)}")
    for ep, _ in todos:
        print(f"    * {ep}")
    print("-" * 60)

    append_master_log(
        f"\n{'='*60}\n"
        f"INICIO SESION : {run_ts}\n"
        f"Episodios     : {len(todos)}\n"
        f"{'='*60}"
    )

    ok_list:   list[str] = []
    fail_list: list[str] = []

    for ep_code, guion_path in todos:
        if run_episode(ep_code, guion_path, args.dry_run):
            ok_list.append(ep_code)
        else:
            fail_list.append(ep_code)

    end_ts = ts()
    print(f"\n{sep}")
    print(f"  RESUMEN - {end_ts}")
    print(f"  OK    ({len(ok_list)}): {', '.join(ok_list) or '--'}")
    print(f"  FALLO ({len(fail_list)}): {', '.join(fail_list) or '--'}")
    if fail_list:
        print("\n  Logs de fallos:")
        for ep in fail_list:
            print(f"    episodios/{ep}_cmd.log")
    print(f"\n  Log maestro: {MASTER_LOG}")

    append_master_log(
        f"FIN SESION    : {end_ts}\n"
        f"OK ({len(ok_list)}): {', '.join(ok_list) or '--'}\n"
        f"FALLO ({len(fail_list)}): {', '.join(fail_list) or '--'}\n"
        f"{'-'*60}"
    )


if __name__ == "__main__":
    main()
