#!/usr/bin/env bash
# Respaldo de las 3 bases de AzerothCore en un solo archivo .sql.gz
set -euo pipefail

BASE="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE/azerothcore-wotlk"

set -a
# shellcheck disable=SC1091
source .env
set +a

FECHA="$(date +%Y%m%d-%H%M%S)"
DESTINO="$BASE/backups/azerothcore-$FECHA.sql.gz"
mkdir -p "$BASE/backups"

echo "==> Generando respaldo..."
docker exec ac-database mysqldump \
    -uroot -p"$DOCKER_DB_ROOT_PASSWORD" \
    --databases acore_auth acore_characters acore_world \
    --single-transaction --routines --events \
    | gzip > "$DESTINO"

echo "Listo: $DESTINO ($(du -h "$DESTINO" | cut -f1))"
