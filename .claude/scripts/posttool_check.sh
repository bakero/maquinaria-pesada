#!/usr/bin/env bash
# PostToolUse hook: tras Edit/Write/MultiEdit sobre código de la app,
# ejecuta ruff + pytest. Opcionalmente (MP_RUN_E2E=1) también corre la
# suite Playwright si el cambio toca la UI o el web_server.
#
# stdin: JSON del hook con tool_input.file_path
# stdout: vacío si OK; JSON con decision="block" si falla.

set -u

REPO_ROOT="/home/user/maquinaria-pesada"

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_response.filePath // ""')

# Solo correr para ediciones en código de la app (Python + frontend Vite).
case "$FILE" in
    */cockpit/*|*/tests/*|*pyproject.toml|*/web_server.py|*/vite_app/src/*)
        ;;
    *)
        exit 0
        ;;
esac

cd "$REPO_ROOT" || exit 0

# 1. Ruff · solo si el cambio toca Python; las edits de TS/CSS no aplican
case "$FILE" in
    *.py|*pyproject.toml)
        if ! RUFF_OUT=$(ruff check cockpit/ tests/ 2>&1); then
            jq -n --arg out "$RUFF_OUT" --arg file "$FILE" \
                '{decision: "block", reason: ("Ruff falló tras editar " + $file + ":\n\n" + $out + "\n\nCorrige los errores antes de continuar.")}'
            exit 0
        fi
        ;;
esac

# 2. Pytest unit · excluye la suite e2e (es lenta; se corre en su propio paso)
case "$FILE" in
    *.py|*pyproject.toml)
        if ! PYTEST_OUT=$(pytest tests/ -q --tb=line --ignore=tests/test_e2e_vite.py 2>&1); then
            jq -n --arg out "$PYTEST_OUT" --arg file "$FILE" \
                '{decision: "block", reason: ("Pytest falló tras editar " + $file + ":\n\n" + $out + "\n\nCorrige los tests antes de continuar.")}'
            exit 0
        fi
        ;;
esac

# 3. E2E opcional · solo si MP_RUN_E2E=1 y el cambio toca UI/web_server.
# Diseñado opt-in porque la suite tarda ~90 s y ralentizaría cada Edit
# del usuario. Para activarlo en una sesión:  export MP_RUN_E2E=1
if [ "${MP_RUN_E2E:-0}" = "1" ]; then
    case "$FILE" in
        */vite_app/src/*|*/web_server.py|*/cockpit/core/episodes.py)
            # Rebuild de Vite si tocamos el frontend; el server sirve dist/.
            case "$FILE" in
                */vite_app/src/*)
                    if ! NPM_OUT=$(cd vite_app && npm run build 2>&1); then
                        jq -n --arg out "$NPM_OUT" --arg file "$FILE" \
                            '{decision: "block", reason: ("vite build falló tras editar " + $file + ":\n\n" + $out)}'
                        exit 0
                    fi
                    ;;
            esac
            # python3 -m pytest porque pytest-playwright vive en pip global
            # y el binario `pytest` (uv tool) no lo ve.
            if ! E2E_OUT=$(python3 -m pytest tests/test_e2e_vite.py -q --tb=short 2>&1); then
                jq -n --arg out "$E2E_OUT" --arg file "$FILE" \
                    '{decision: "block", reason: ("E2E falló tras editar " + $file + ":\n\n" + $out + "\n\nCorrige los tests Playwright antes de continuar.")}'
                exit 0
            fi
            ;;
    esac
fi

# Todo OK: salir limpio.
exit 0
