#!/usr/bin/env bash
# Detiene la API y los contenedores. La base de datos se conserva.
set -euo pipefail

BASE="$(cd "$(dirname "$0")" && pwd)"

echo "==> Deteniendo API..."
pkill -f "uvicorn main:app" 2>/dev/null || true

echo "==> Deteniendo contenedores..."
cd "$BASE/azerothcore-wotlk"
docker compose down

echo "Listo. Los datos de MySQL siguen en el volumen 'ac-database'."
