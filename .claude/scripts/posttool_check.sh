#!/usr/bin/env bash
# PostToolUse hook: tras Edit/Write/MultiEdit sobre código de la app,
# ejecuta ruff y pytest. Si fallan, emite JSON con decision="block"
# para que Claude vea el error y deba arreglarlo antes de continuar.
#
# stdin: JSON del hook con tool_input.file_path
# stdout: vacío si OK; JSON con decision="block" si falla.

set -u

REPO_ROOT="/home/user/maquinaria-pesada"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_response.filePath // ""')

# Solo correr para ediciones en código.
case "$FILE" in
    */cockpit/*|*/tests/*|*pyproject.toml)
        ;;
    *)
        exit 0
        ;;
esac

cd "$REPO_ROOT" || exit 0

# 1. Ruff
if ! RUFF_OUT=$(ruff check cockpit/ tests/ 2>&1); then
    jq -n --arg out "$RUFF_OUT" --arg file "$FILE" \
        '{decision: "block", reason: ("Ruff falló tras editar " + $file + ":\n\n" + $out + "\n\nCorrige los errores antes de continuar.")}'
    exit 0
fi

# 2. Pytest
if ! PYTEST_OUT=$(pytest tests/ -q --tb=line 2>&1); then
    jq -n --arg out "$PYTEST_OUT" --arg file "$FILE" \
        '{decision: "block", reason: ("Pytest falló tras editar " + $file + ":\n\n" + $out + "\n\nCorrige los tests antes de continuar.")}'
    exit 0
fi

# Todo OK: salir limpio.
exit 0
