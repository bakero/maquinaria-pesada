#!/usr/bin/env bash
# Mueve los scripts legacy a `_legacy/` preservando historia (git mv).
#
# Pre-requisitos:
# 1. La equivalencia entre legacy y moderno está validada (docs/auditoria_legacy.md §3).
# 2. Los invocadores activos (lanzar_guiones, produce_pending, producir_episodio,
#    run_iteration, wrappers de cockpit) ya están migrados al pipeline v6.
# 3. `pytest tests/ -q` está en verde.
#
# Tras ejecutar este script, validar manualmente:
#   - Cockpit web sigue arrancando: `python web_server.py`
#   - Tests verdes: `python -m pytest tests/ -q --ignore=tests/test_e2e_vite.py`
#
# Rollback: `git restore --staged _legacy/ && git checkout HEAD -- _legacy/`
# (los archivos quedarán en _legacy/ pero versionados; mover de vuelta con git mv).

set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p _legacy

LEGACY_FILES=(
    "generar_guion.py"
    "generar_guion_t.py"
    "fix_guiones_v4.py"
    "normalizar_guiones.py"
    "rebalance_blocks.py"
    "validar_episodio.py"
)

for f in "${LEGACY_FILES[@]}"; do
    if [[ -f "$f" ]]; then
        echo "git mv $f _legacy/$f"
        git mv "$f" "_legacy/$f"
    else
        echo "skip $f (no existe)"
    fi
done

echo
echo "Hecho. Verifica:"
echo "  python -m pytest tests/ -q --ignore=tests/test_e2e_vite.py"
echo "  python web_server.py  # cockpit debe arrancar"
echo
echo "Si todo OK, commit:"
echo "  git commit -m 'chore: mueve pipelines legacy a _legacy/ (Fase 8)'"
