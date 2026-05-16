#!/usr/bin/env python3
"""Valida todos los guiones de Guiones/iter_<N>/ y produce un resumen
agregado de fallos hard/soft por regla y por episodio.

Uso: python scripts/validate_iter.py --iter 1
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from validators import m_validator, s_validator, t_validator
from validators.shared.parity import opener_for


def _validate(path: Path):
    ep = path.stem.replace("_v6", "")
    if re.match(r"^M\d+$", ep):
        return ep, "M", m_validator.validate(path.read_text(encoding="utf-8"),
                                              ep, repo_root=REPO_ROOT)
    if re.match(r"^M\d+_T\d+$", ep):
        return ep, "T", t_validator.validate(path.read_text(encoding="utf-8"), ep)
    if re.match(r"^S\d+", ep):
        n = int(re.match(r"^S(\d+)", ep).group(1))
        return ep, "S", s_validator.validate(
            path.read_text(encoding="utf-8"), ep,
            s_number=n, voice=opener_for(n), filename=f"{ep}_x.mp3",
        )
    return ep, "?", []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", type=int, required=True)
    args = ap.parse_args()

    iter_dir = REPO_ROOT / "Guiones" / f"iter_{args.iter}"
    if not iter_dir.exists():
        print(f"No existe {iter_dir}")
        return 1

    hard = Counter()
    soft = Counter()
    per_ep_hard: dict[str, list[str]] = defaultdict(list)
    per_ep_soft: dict[str, list[str]] = defaultdict(list)
    totals = {"M": 0, "T": 0, "S": 0}
    clean = {"M": 0, "T": 0, "S": 0}

    files = sorted(iter_dir.glob("*_v6.md"))
    print(f"=== ITER {args.iter}: {len(files)} guiones ===\n")
    for f in files:
        ep, kind, rs = _validate(f)
        totals[kind] = totals.get(kind, 0) + 1
        hard_rs = [r for r in rs if r.severity == "HARD" and not r.passed]
        soft_rs = [r for r in rs if r.severity == "SOFT" and not r.passed]
        if not hard_rs and not soft_rs:
            clean[kind] = clean.get(kind, 0) + 1
        print(f"{ep:18s} [{kind}]  hard={len(hard_rs):2d}  soft={len(soft_rs):2d}")
        for r in hard_rs:
            hard[r.rule_name] += 1
            per_ep_hard[ep].append(f"{r.rule_name}: {r.message}")
        for r in soft_rs:
            soft[r.rule_name] += 1
            per_ep_soft[ep].append(f"{r.rule_name}: {r.message}")

    print(f"\n=== RESUMEN HARD ({sum(hard.values())} totales) ===")
    for rule, n in hard.most_common():
        print(f"  {n:2d}× {rule}")
    print(f"\n=== RESUMEN SOFT ({sum(soft.values())} totales) ===")
    for rule, n in soft.most_common():
        print(f"  {n:2d}× {rule}")

    clean_total = sum(clean.values())
    total = sum(totals.values())
    print(f"\n=== LIMPIOS: {clean_total}/{total} "
          f"(M:{clean['M']}/{totals['M']}, "
          f"T:{clean['T']}/{totals['T']}, "
          f"S:{clean['S']}/{totals['S']}) ===")

    if per_ep_hard:
        print("\n=== DETALLE HARD POR EPISODIO ===")
        for ep, issues in per_ep_hard.items():
            print(f"\n{ep}:")
            for i in issues:
                print(f"  - {i}")

    return 0


if __name__ == "__main__":
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script="scripts/validate_iter.py", params=sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        sys.exit(main())
