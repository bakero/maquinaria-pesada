#!/usr/bin/env bash
# start_cockpit.sh — arranque end-to-end del cockpit web de MaquinarIA Pesada.
#
# Tras ejecutarlo, tendrás todo lo necesario para usar la cabina vía
# http://localhost:8765/ (una sola URL, una sola pestaña):
#
#   1. Dependencias Python (requirements-cockpit.txt) instaladas si faltan.
#   2. node_modules de vite_app instalados si faltan.
#   3. Build de vite_app/dist al día (rebuild si dist no existe o si algún
#      archivo de vite_app/src es más reciente).
#   4. web_server.py (FastAPI + uvicorn) sirviendo el build estático + la
#      API JSON + /files/<path> + SSE /api/stream.
#
# Uso:
#   bash start_cockpit.sh                 → arranca producción (puerto 8765)
#   bash start_cockpit.sh --dev           → además lanza vite dev (5173) con HMR
#   bash start_cockpit.sh --port 9000     → cambia puerto del web_server
#   bash start_cockpit.sh --skip-build    → no toca el build (úsalo si ya lo hiciste)
#
# El script es idempotente: ejecútalo cuantas veces quieras, sólo (re)hace
# lo necesario.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

PORT="${PORT:-8765}"
HOST="${HOST:-127.0.0.1}"
DEV=0
SKIP_BUILD=0

while [ $# -gt 0 ]; do
    case "$1" in
        --dev)        DEV=1; shift ;;
        --skip-build) SKIP_BUILD=1; shift ;;
        --port)       PORT="$2"; shift 2 ;;
        --host)       HOST="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,22p' "$0"
            exit 0 ;;
        *)
            echo "Argumento desconocido: $1" >&2; exit 2 ;;
    esac
done

bold()  { printf "\033[1m%s\033[0m\n" "$*"; }
ok()    { printf "  \033[32m✓\033[0m %s\n" "$*"; }
warn()  { printf "  \033[33m!\033[0m %s\n" "$*"; }
step()  { printf "\n\033[36m▸\033[0m \033[1m%s\033[0m\n" "$*"; }
fail()  { printf "  \033[31m✗\033[0m %s\n" "$*" >&2; exit 1; }

# ── 1. Python deps ───────────────────────────────────────────────────────
step "Comprobando dependencias Python"
if ! python3 -c "import fastapi, uvicorn, anthropic" 2>/dev/null; then
    warn "instalando requirements-cockpit.txt (tarda 30-60 s la primera vez)"
    python3 -m pip install --quiet -r requirements-cockpit.txt
    ok "deps Python instaladas"
else
    ok "deps Python OK"
fi

# ── 2. Node deps ─────────────────────────────────────────────────────────
step "Comprobando dependencias de vite_app"
if [ ! -d vite_app/node_modules ] || [ ! -f vite_app/node_modules/.package-lock.json ]; then
    warn "ejecutando 'npm ci' (vite_app/node_modules ausente)"
    (cd vite_app && npm ci)
    ok "node_modules instalados"
else
    ok "node_modules OK"
fi

# ── 3. Build de Vite ─────────────────────────────────────────────────────
need_build=0
if [ "$SKIP_BUILD" = "1" ]; then
    step "Build Vite (saltado por --skip-build)"
elif [ ! -f vite_app/dist/index.html ]; then
    step "Build Vite (no existe dist/index.html)"
    need_build=1
else
    # ¿algún archivo de src más reciente que el index.html?
    newest_src=$(find vite_app/src vite_app/index.html vite_app/vite.config.ts \
                      vite_app/tsconfig.json -type f -printf "%T@\n" 2>/dev/null \
                      | sort -nr | head -1)
    dist_ts=$(stat -c "%Y" vite_app/dist/index.html 2>/dev/null || echo 0)
    if awk -v s="$newest_src" -v d="$dist_ts" 'BEGIN{ exit !(s > d) }'; then
        step "Build Vite (hay cambios en vite_app/src)"
        need_build=1
    else
        step "Build Vite (al día)"
        ok "dist/ actualizado · $(ls vite_app/dist/assets/*.js 2>/dev/null | head -1 | xargs basename)"
    fi
fi

if [ "$need_build" = "1" ]; then
    (cd vite_app && npm run build)
    ok "build completado"
fi

# ── 4. Mata instancias previas en el mismo puerto ────────────────────────
# Buscamos sólo procesos python que estén ejecutando web_server.py con
# nuestro puerto. Evitamos `pkill -f` con patrones genéricos como
# "web_server.py": eso matchearía también el bash que ejecuta este script
# (cuyo argv0 contiene esa cadena) y nos cerraría a nosotros mismos.
step "Limpiando procesos previos en :$PORT"
prev_pids=$(pgrep -f "python.*web_server\.py.*--port $PORT" || true)
if [ -n "${prev_pids:-}" ]; then
    echo "$prev_pids" | xargs -r kill 2>/dev/null || true
    sleep 1
    ok "procesos previos cerrados ($prev_pids)"
else
    ok "puerto libre"
fi

# ── 5. (opcional) Vite dev server ────────────────────────────────────────
if [ "$DEV" = "1" ]; then
    step "Arrancando vite dev (HMR) en :5173"
    pkill -f "vite$" 2>/dev/null || true
    (cd vite_app && nohup npm run dev > /tmp/vite_dev.log 2>&1 &)
    sleep 3
    ok "vite dev arriba · logs en /tmp/vite_dev.log"
    echo "    URL dev (HMR):  http://localhost:5173"
fi

# ── 6. Web server (foreground) ───────────────────────────────────────────
step "Arrancando web_server.py en http://$HOST:$PORT"
echo ""
bold "  ╭─────────────────────────────────────────────────────╮"
bold "  │  Cockpit listo · abre en el navegador:              │"
bold "  │                                                     │"
bold "  │      http://localhost:$PORT/                         │"
bold "  │                                                     │"
bold "  │  Ctrl-C para parar.                                 │"
bold "  ╰─────────────────────────────────────────────────────╯"
echo ""
exec python3 web_server.py --host "$HOST" --port "$PORT"
