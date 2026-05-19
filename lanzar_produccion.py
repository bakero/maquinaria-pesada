#!/usr/bin/env python3
# ruff: noqa
"""
lanzar_produccion.py
--------------------

🚫 SCRIPT LEGACY — RETIRADO 2026-05-19.
   Encadenaba `generar_guion.py` (v5). Reemplazado por
   `lanzar_produccion_v6.py` que delega en el paquete `generadores/`.
   Ver `GENERACION.md` para el mapa canónico.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.stderr.write(
        "\n❌ lanzar_produccion.py está retirado (era v5).\n"
        "   Usa el pipeline canónico:\n"
        "       python lanzar_produccion_v6.py --kind M --ep M<N>\n"
        "       python lanzar_produccion_v6.py --kind T --ep M<N>_T<K>\n"
        "       python lanzar_produccion_v6.py --kind S --ep S<N>_<term> --term <term>\n"
        "   Ver GENERACION.md para el mapa completo.\n\n"
    )
    raise SystemExit(2)

# ---- Código histórico inaccesible ----------------------------------------
# Se elimina entero en un PR de limpieza dedicado.
# --------------------------------------------------------------------------

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(__file__).parent
GUIONES_DIR   = BASE_DIR / "Guiones"
EPISODIOS_DIR = BASE_DIR / "episodios"
MASTER_LOG    = EPISODIOS_DIR / "produccion_runs.log"

sys.path.insert(0, str(BASE_DIR))
from podcast_spec import guion_to_ep_code, episode_type

# Patrones de guion y audio
_GUION_RE = re.compile(r"^M(\d+)(?:_TX)?_(.+)\.txt$", re.IGNORECASE)
_AUDIO_RE = re.compile(r"^M(\d+)(?:_TX)?_E_(.+)\.mp3$", re.IGNORECASE)


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def scan_guiones() -> dict[str, Path]:
    """Devuelve {ep_code: guion_path} para todos los guiones en Guiones/."""
    result: dict[str, Path] = {}
    if not GUIONES_DIR.exists():
        return result
    for path in sorted(GUIONES_DIR.iterdir()):
        if path.suffix.lower() != ".txt":
            continue
        if _GUION_RE.match(path.name):
            ep_code = guion_to_ep_code(path.stem)
            result[ep_code] = path
    return result


def scan_audios() -> set[str]:
    """Devuelve set de ep_codes que ya tienen MP3 generado."""
    result: set[str] = {}
    if not EPISODIOS_DIR.exists():
        return set()
    codes: set[str] = set()
    for path in EPISODIOS_DIR.iterdir():
        if path.suffix.lower() != ".mp3":
            continue
        m = _AUDIO_RE.match(path.name)
        if m:
            # reconstruir ep_code desde nombre de audio
            codes.add(path.stem)
    return codes


def pendientes(tipo: str | None = None) -> list[tuple[str, Path]]:
    """Devuelve [(ep_code, guion_path)] con guion pero sin audio.

    tipo: 'M' solo módulos, 'T' solo temas, None todos.
    """
    guiones = scan_guiones()
    audios  = scan_audios()
    result  = []
    for ep_code, guion_path in sorted(guiones.items()):
        if ep_code in audios:
            continue
        ep_t = episode_type(guion_path.stem)
        if tipo and ep_t != tipo:
            continue
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
    ep_t = episode_type(guion_path.stem)
    spec_file = "PODCAST_T_SPEC.md" if ep_t == "T" else "PODCAST_M_SPEC.md"
    cmd = [
        sys.executable,
        str(BASE_DIR / "generar_episodio_v2.py"),
        "--guion", str(guion_path.relative_to(BASE_DIR)),
        "--ep",    ep_code,
        "--spec",  spec_file,
    ]
    log_path = cmd_log_path(ep_code)

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  EPISODIO : {ep_code}  [{ep_t}]")
    print(f"  Guion    : {guion_path.name}")
    print(f"  Log cmd  : {log_path.name}")

    if dry_run:
        print(f"  CMD      : {' '.join(cmd)}")
        print("  [DRY-RUN]")
        return True

    started = ts()
    print(f"  Inicio   : {started}")
    print("  Ejecutando...")
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
        finished   = ts()
        ok         = result.returncode == 0
        stdout     = result.stdout
        stderr     = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        finished   = ts()
        ok         = False
        stdout     = getattr(exc, "stdout", "") or ""
        stderr     = "[TIMEOUT] El proceso superó 30 minutos.\n"
        returncode = -1
    except Exception as exc:
        finished   = ts()
        ok         = False
        stdout     = ""
        stderr     = f"[EXCEPCION EN LANZADOR] {type(exc).__name__}: {exc}\n"
        returncode = -1

    status_str = "OK" if ok else "FALLO"

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
    stdout_section = "--- STDOUT ---\n" + (stdout if stdout.strip() else "(vacio)\n") + "\n"
    stderr_section = ("\n--- STDERR ---\n" + stderr + "\n") if stderr and stderr.strip() else ""
    log_path.write_text(header_log + stdout_section + stderr_section, encoding="utf-8")

    master_line = f"[{finished}] {status_str:5s} | {ep_code} | log: {log_path.name}"
    if not ok:
        hint = _extract_error_hint(stdout, stderr)
        master_line += f"\n              error: {hint}"
    append_master_log(master_line)

    print(f"  Fin      : {finished}  [{status_str}]")
    print(f"  Log      : {log_path}")

    if not ok:
        print(f"\n  {'-'*56}")
        print("  ERROR - detalle:")
        print(f"    {_extract_error_hint(stdout, stderr)}")
        stdout_tail = [ln for ln in stdout.splitlines() if ln.strip()][-8:]
        if stdout_tail:
            print(f"\n  [stdout - últimas {len(stdout_tail)} lineas]")
            for ln in stdout_tail:
                print(f"    {ln}")
        stderr_lines = [ln for ln in stderr.splitlines() if ln.strip()]
        if stderr_lines:
            max_show = 20
            label = "completo" if len(stderr_lines) <= max_show else f"últimas {max_show}"
            print(f"\n  [stderr - {label}]")
            for ln in stderr_lines[-max_show:]:
                print(f"    {ln}")
        print(f"  {'-'*56}")
        print(f"  -> Log: episodios/{log_path.name}")

    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Lanzador de producción de episodios")
    parser.add_argument("--ep",      default=None, help="Generar solo este ep_code exacto")
    parser.add_argument("--tipo",    default=None, choices=["M", "T"], help="Filtrar por tipo (M o T)")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar comandos sin ejecutar")
    args = parser.parse_args()

    todos = pendientes(tipo=args.tipo)

    if not todos:
        print("No hay episodios pendientes de audio.")
        return

    if args.ep:
        todos = [(ep, g) for ep, g in todos if ep == args.ep]
        if not todos:
            print(f"No se encontró '{args.ep}' en la lista de pendientes.")
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


# El bloque `if __name__ == "__main__"` original se ha movido al inicio del
# archivo (ver guard arriba). No se ejecutará por debajo del SystemExit.
if False:  # pragma: no cover - histórico inaccesible
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="lanzar_produccion.py", params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
