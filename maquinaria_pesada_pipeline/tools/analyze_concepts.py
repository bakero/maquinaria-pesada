#!/usr/bin/env python3
"""
Dashboard CLI para analizar el catalogo de conceptos:
  - Conceptos mas repetidos entre modulos.
  - Estado de la biblioteca de escenas (cuantos generados con Luma).
  - Sugerencias de prioridad para generar.

Uso:
    python tools/analyze_concepts.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.scene_library import SceneLibrary

LIBRARY_BASE = r"C:\Users\Asus\maquinaria_pesada\Videos\escenas_biblioteca"
CONCEPTS_PATH = Path(LIBRARY_BASE) / "_concepts_index.json"


def main():
    library = SceneLibrary(LIBRARY_BASE)
    print()
    print("=" * 70)
    print("  CATALOGO DE CONCEPTOS · MaquinarIA Pesada")
    print("=" * 70)

    if not CONCEPTS_PATH.exists():
        print("  El catalogo de conceptos aun no existe.")
        print("  Ejecuta: python -m pipeline.concept_extractor --pdfs <folder> --out <json>")
        return 1

    repeated = library.repeated_concepts(CONCEPTS_PATH, min_apariciones=2)
    print(f"\n  Conceptos detectados en >=2 modulos: {len(repeated)}")
    print()
    print(f"  {'Aparic':<7} {'Modulos':<25} {'Concepto':<40} {'En lib':<7}")
    print("  " + "-" * 70)
    for c in repeated[:30]:
        modulos = ", ".join(c["modulos"])[:23]
        in_lib = "OK" if c["in_library"] else "-"
        print(f"  {c['apariciones']:<7} {modulos:<25} {c['name'][:38]:<40} {in_lib:<7}")

    print()
    stats = library.stats()
    print(f"  Biblioteca actual: {stats['total']} escenas")
    for cat, n in stats.get("by_category", {}).items():
        print(f"    {cat}: {n}")

    if repeated:
        non_existing = [c for c in repeated if not c["in_library"]]
        print()
        print(f"  Para maximizar reuso, recomendado generar primero los TOP-{min(10, len(non_existing))}:")
        for c in non_existing[:10]:
            print(f"    [{c['apariciones']}x] {c['name']}")
            if c.get("luma_prompt"):
                print(f"         prompt: {c['luma_prompt'][:90]}...")
    return 0


if __name__ == "__main__":
    # Bitácora diaria centralizada (logs/run/). Localiza daylog.py subiendo
    # directorios; si fallara, el script sigue con un nullcontext de respaldo.
    import sys as _sys
    from pathlib import Path as _Path
    for _p in _Path(__file__).resolve().parents:
        if (_p / "daylog.py").exists():
            if str(_p) not in _sys.path:
                _sys.path.insert(0, str(_p))
            break
    try:
        from daylog import RunLog as _RunLog
        _run_ctx = _RunLog(script=_Path(__file__).name, params=_sys.argv[1:])
    except Exception:  # noqa: BLE001
        from contextlib import nullcontext as _nullcontext
        _run_ctx = _nullcontext()
    with _run_ctx:
        raise SystemExit(main())
