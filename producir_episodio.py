#!/usr/bin/env python3
# ruff: noqa
"""producir_episodio.py — Pipeline guion+audio (LEGACY).

🚫 SCRIPT LEGACY — RETIRADO 2026-05-19.
   Encadenaba el legacy `generar_guion.py` + `generar_episodio_v2.py`. El
   pipeline canónico de guiones vivo es `lanzar_produccion.py`. La síntesis
   de audio sigue en `generar_episodio_v2.py` por ahora. Ver `GENERACION.md`.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    sys.stderr.write(
        "\n❌ producir_episodio.py está retirado.\n"
        "   El generador legacy del que dependía ya no existe.\n"
        "   Usa el pipeline canónico:\n"
        "       python lanzar_produccion.py --kind M --ep M<N>      # guion\n"
        "       python generar_episodio_v2.py --ep <ep> ...          # audio\n"
        "   Ver GENERACION.md para el mapa completo.\n\n"
    )
    raise SystemExit(2)

# ---- Código histórico inaccesible ----------------------------------------
import argparse
import subprocess
from pathlib import Path

from podcast_spec import DEFAULT_SPEC_PATH, load_master_spec, next_episode_code


def run_command(args: list[str]) -> None:
    result = subprocess.run(args, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline completo: guion + audio")
    parser.add_argument("--spec", default=str(DEFAULT_SPEC_PATH), help="Ruta a la especificacion maestra")
    parser.add_argument("--ep", default=None, help="Codigo del episodio")
    parser.add_argument("--modulo", default=None, help="Modulo o unidad del episodio")
    parser.add_argument("--tema", default=None, help="Tema principal")
    parser.add_argument("--objetivo", default=None, help="Objetivo de aprendizaje")
    parser.add_argument("--duracion-min", type=int, default=None, help="Duracion objetivo")
    parser.add_argument("--contexto-file", default=None, help="Archivo de contexto .txt o .md")
    parser.add_argument("--pdf", default=None, help="PDF fuente dentro de PDFs o ruta completa")
    parser.add_argument("--master-pdf", default=None, help="PDF maestro completo con referencias")
    parser.add_argument("--estudios", default="", help="Estudios o informes a citar")
    parser.add_argument("--aplicacion-empresarial", default="", help="Aplicacion empresarial dominante")
    parser.add_argument("--token-budget", type=int, default=None, help="Presupuesto de tokens para el guion")
    parser.add_argument("--generar-musica", action="store_true", help="Generar nueva musica de fondo")
    args = parser.parse_args()

    spec = load_master_spec(args.spec)
    ep_code = args.ep or next_episode_code(spec["directories"]["scripts_dir"])
    script_path = Path(spec["directories"]["scripts_dir"]) / f"{ep_code}.txt"

    command_guion = [
        sys.executable,
        "generar_guion.py",
        "--spec",
        args.spec,
        "--ep",
        ep_code,
    ]
    if args.modulo:
        command_guion.extend(["--modulo", args.modulo])
    if args.tema:
        command_guion.extend(["--tema", args.tema])
    if args.objetivo:
        command_guion.extend(["--objetivo", args.objetivo])
    if args.duracion_min is not None:
        command_guion.extend(["--duracion-min", str(args.duracion_min)])
    if args.contexto_file:
        command_guion.extend(["--contexto-file", args.contexto_file])
    if args.pdf:
        command_guion.extend(["--pdf", args.pdf])
    if args.master_pdf:
        command_guion.extend(["--master-pdf", args.master_pdf])
    if args.estudios:
        command_guion.extend(["--estudios", args.estudios])
    if args.aplicacion_empresarial:
        command_guion.extend(["--aplicacion-empresarial", args.aplicacion_empresarial])
    if args.token_budget is not None:
        command_guion.extend(["--token-budget", str(args.token_budget)])

    run_command(command_guion)

    command_audio = [
        sys.executable,
        "generar_episodio_v2.py",
        "--spec",
        args.spec,
        "--guion",
        str(script_path),
        "--ep",
        ep_code,
    ]
    if args.generar_musica:
        command_audio.append("--generar-musica")

    run_command(command_audio)

    from estado_proyecto import print_estado_resumen
    print_estado_resumen()


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    import sys as _sys
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="producir_episodio.py", params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        main()
