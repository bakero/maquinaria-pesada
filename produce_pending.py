#!/usr/bin/env python3
"""Genera audio para todos los guiones que no tienen mp3 con el nombre simple
(M0.mp3, M1_T10.mp3, etc.). Usado para producir en masa sin lanzar_produccion."""
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent
GUIONES = BASE / "Guiones"
EPISODIOS = BASE / "episodios"
EPISODIOS.mkdir(exist_ok=True)


def ep_code_from_filename(name: str) -> str:
    base = name.replace(".txt", "")
    if "_TX_T" in base:  # legacy Mn_TX_Tk_...
        m = re.match(r"(M\d+)_TX_(T\d+)", base)
        return f"{m.group(1)}_{m.group(2)}"
    m = re.match(r"(M\d+)_(T\d+)_", base)  # naming actual Mn_Tk_slug
    if m:
        return f"{m.group(1)}_{m.group(2)}"
    return re.match(r"(M\d+)", base).group(1)


def detect_type(name: str) -> str:
    # Naming actual (Mn_Tk_slug) y legacy (Mn_TX_Tk_...).
    if "_TX_T" in name or re.match(r"^M\d+_T\d+_", name, re.IGNORECASE):
        return "T"
    return "M"


def already_done(ep: str) -> bool:
    return (EPISODIOS / f"{ep}.mp3").exists()


def main():
    from cockpit.core.log_helpers import get_run_logger
    log = get_run_logger("produce_pending")

    log.step("scan_pending")
    pending = []
    for f in sorted(GUIONES.glob("*.txt")):
        ep = ep_code_from_filename(f.name)
        if already_done(ep):
            continue
        pending.append((ep, f))

    log.info("pendientes detectados", count=len(pending))
    print(f"Pendientes: {len(pending)}")
    for ep, _ in pending:
        print(f"  - {ep}")
    print()

    log.step("produce", total=len(pending))
    failed = []
    for i, (ep, guion) in enumerate(pending, 1):
        t = detect_type(guion.name)
        spec = "PODCAST_T_SPEC.md" if t == "T" else "PODCAST_M_SPEC.md"
        log.info("produciendo episodio", ep=ep, kind=t, idx=i, total=len(pending))
        print(f"\n[{i}/{len(pending)}] === {ep} ({t}) ===")
        t0 = time.time()
        result = subprocess.run(
            [
                sys.executable, "generar_episodio_v2.py",
                "--guion", str(guion.relative_to(BASE)),
                "--ep", ep,
                "--spec", spec,
            ],
            cwd=str(BASE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=2400,
        )
        elapsed = time.time() - t0
        mp3 = EPISODIOS / f"{ep}.mp3"
        ok = mp3.exists() and mp3.stat().st_size > 1_048_576
        status = "OK" if ok else "FAIL"
        size_mb = mp3.stat().st_size / 1_048_576 if mp3.exists() else 0
        print(f"  -> {status}  {elapsed/60:.1f} min  {size_mb:.1f} MB")
        if ok:
            log.ok("episodio producido", ep=ep, elapsed_s=round(elapsed, 1), size_mb=round(size_mb, 1))
        else:
            log.error("episodio falló", ep=ep, elapsed_s=round(elapsed, 1), returncode=result.returncode)
            failed.append(ep)

    print("\n========== RESUMEN ==========")
    print(f"Total: {len(pending)}  OK: {len(pending)-len(failed)}  FAIL: {len(failed)}")
    if failed:
        print(f"Fallaron: {failed}")
        log.error("ejecución con episodios fallidos", failed=",".join(failed))
        return 1
    log.ok("todos los episodios producidos", total=len(pending))
    return 0


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Si daylog fallara, el pipeline
    # sigue igual gracias al nullcontext de respaldo.
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="produce_pending.py", params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        sys.exit(main())
