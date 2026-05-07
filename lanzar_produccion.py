#!/usr/bin/env python3
"""
lanzar_produccion.py
--------------------
Ejecuta todos los episodios pendientes de audio y guarda la salida completa
(stdout + stderr) en episodios/{ep}_cmd.log para revision posterior.

Uso:
  python lanzar_produccion.py              # todos los pendientes
  python lanzar_produccion.py --ep M3_E_Machine_Learning_Clasico  # uno solo
  python lanzar_produccion.py --dry-run    # muestra comandos sin ejecutar
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from estado_proyecto import scan, GUIONES_DIR, AUDIO_DIR, GUION_RE, AUDIO_RE


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
    return BASE_DIR / "episodios" / f"{ep_code}_cmd.log"


def run_episode(ep_code: str, guion_path: Path, dry_run: bool) -> bool:
    """Ejecuta el generador y guarda toda la salida en _cmd.log. Devuelve True si OK."""
    cmd = [
        sys.executable,
        str(BASE_DIR / "generar_episodio_v2.py"),
        "--guion", str(guion_path.relative_to(BASE_DIR)),
        "--ep",    ep_code,
    ]
    log_path = cmd_log_path(ep_code)

    print(f"\n{'='*60}")
    print(f"  {ep_code}")
    print(f"  Guion : {guion_path.name}")
    print(f"  Log   : {log_path.name}")
    if dry_run:
        print(f"  CMD   : {' '.join(cmd)}")
        print("  [dry-run — no se ejecuta]")
        return True

    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Inicio: {started}")

    result = subprocess.run(
        cmd,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    finished = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = result.returncode == 0

    header = (
        f"COMANDO: {' '.join(cmd)}\n"
        f"INICIO:  {started}\n"
        f"FIN:     {finished}\n"
        f"EXIT:    {result.returncode} ({'OK' if ok else 'FALLO'})\n"
        f"{'='*60}\n\n"
    )

    log_path.write_text(
        header + result.stdout + ("\n--- STDERR ---\n" + result.stderr if result.stderr.strip() else ""),
        encoding="utf-8",
    )

    status = "OK" if ok else "FALLO"
    print(f"  Fin   : {finished}  [{status}]")
    if not ok:
        # Mostrar las primeras lineas del error para diagnostico rapido
        stderr_lines = [l for l in result.stderr.splitlines() if l.strip()]
        if stderr_lines:
            print(f"  Error : {stderr_lines[-1]}")
        else:
            stdout_lines = [l for l in result.stdout.splitlines() if l.strip()]
            for line in stdout_lines[-3:]:
                print(f"         {line}")

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

    print(f"\nEpisodios pendientes: {len(todos)}")
    for ep, g in todos:
        print(f"  {ep}")

    ok_list:   list[str] = []
    fail_list: list[str] = []

    for ep_code, guion_path in todos:
        if run_episode(ep_code, guion_path, args.dry_run):
            ok_list.append(ep_code)
        else:
            fail_list.append(ep_code)

    print(f"\n{'='*60}")
    print(f"RESUMEN")
    print(f"  OK    ({len(ok_list)}): {', '.join(ok_list) or '—'}")
    print(f"  FALLO ({len(fail_list)}): {', '.join(fail_list) or '—'}")
    if fail_list:
        print("\nLogs de fallos:")
        for ep in fail_list:
            print(f"  episodios/{ep}_cmd.log")


if __name__ == "__main__":
    main()
