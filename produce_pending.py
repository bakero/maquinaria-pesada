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
    if "_TX_T" in base:
        m = re.match(r"(M\d+)_TX_(T\d+)", base)
        return f"{m.group(1)}_{m.group(2)}"
    return re.match(r"(M\d+)", base).group(1)


def detect_type(name: str) -> str:
    return "T" if "_TX_T" in name else "M"


def already_done(ep: str) -> bool:
    return (EPISODIOS / f"{ep}.mp3").exists()


def main():
    pending = []
    for f in sorted(GUIONES.glob("*.txt")):
        ep = ep_code_from_filename(f.name)
        if already_done(ep):
            continue
        pending.append((ep, f))

    print(f"Pendientes: {len(pending)}")
    for ep, _ in pending:
        print(f"  - {ep}")
    print()

    failed = []
    for i, (ep, guion) in enumerate(pending, 1):
        t = detect_type(guion.name)
        spec = "PODCAST_T_SPEC.md" if t == "T" else "PODCAST_M_SPEC.md"
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
        if not ok:
            failed.append(ep)

    print(f"\n========== RESUMEN ==========")
    print(f"Total: {len(pending)}  OK: {len(pending)-len(failed)}  FAIL: {len(failed)}")
    if failed:
        print(f"Fallaron: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
