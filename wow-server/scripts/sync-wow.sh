#!/usr/bin/env bash
# Sincroniza personajes, ítems y oro desde el MySQL de AzerothCore
# (solo lectura) hacia el PostgreSQL de proyectoX.
#
# Uso:
#   wow-server/scripts/sync-wow.sh --dry-run
#   wow-server/scripts/sync-wow.sh
#   wow-server/scripts/sync-wow.sh --skip-gold
set -euo pipefail

BASE="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$BASE"

# Configuración del proyecto (DATABASE_URL_LOCAL, etc.).
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# Credenciales del MySQL de WoW desde la API del servidor.
if [ -f wow-server/api/.env ]; then
    set -a
    # shellcheck disable=SC1091
    source wow-server/api/.env
    set +a
    export WOW_DB_HOST="${WOW_DB_HOST:-${DB_HOST:-127.0.0.1}}"
    export WOW_DB_PORT="${WOW_DB_PORT:-${DB_PORT:-3307}}"
    export WOW_DB_USER="${WOW_DB_USER:-${DB_USER:-acore_api}}"
    export WOW_DB_PASSWORD="${WOW_DB_PASSWORD:-${DB_PASSWORD:-}}"
fi

: "${WOW_DB_PASSWORD:?Define WOW_DB_PASSWORD o crea wow-server/api/.env}"

# El contenedor usa postgres-db:5432; desde el host es localhost:5433.
export DATABASE_URL="${DATABASE_URL_LOCAL:-${DATABASE_URL:-}}"
: "${DATABASE_URL:?Define DATABASE_URL_LOCAL en .env (PostgreSQL localhost:5433)}"

PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
    if [ -x .venv/bin/python ]; then
        PYTHON=".venv/bin/python"
    else
        PYTHON="python3"
    fi
fi

exec "$PYTHON" -m src.integrations.wow.sync "$@"
