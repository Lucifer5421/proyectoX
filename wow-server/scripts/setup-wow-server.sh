#!/usr/bin/env bash
# Prepara el stack WoW: clona AzerothCore, copia la configuración custom
# y crea el virtualenv de la API. No arranca los contenedores.
set -euo pipefail

BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"

if [ ! -d azerothcore-wotlk/.git ]; then
    echo "==> Clonando AzerothCore (shallow)..."
    git clone --depth 1 https://github.com/azerothcore/azerothcore-wotlk.git
else
    echo "==> azerothcore-wotlk/ ya existe; no se vuelve a clonar."
fi

echo "==> Copiando docker-compose.yml custom..."
cp docker-compose.yml azerothcore-wotlk/docker-compose.yml

if [ ! -f azerothcore-wotlk/.env ]; then
    cp .env.example azerothcore-wotlk/.env
    echo "    Creado azerothcore-wotlk/.env (edítalo)."
else
    echo "    azerothcore-wotlk/.env ya existe; no se sobrescribe."
fi

if [ ! -d api/venv ]; then
    echo "==> Creando virtualenv de la API..."
    python3 -m venv api/venv
fi
api/venv/bin/pip install --upgrade pip
api/venv/bin/pip install -r api/requirements.txt

if [ ! -f api/.env ]; then
    cp api/.env.example api/.env
    echo "    Creado api/.env (edítalo)."
else
    echo "    api/.env ya existe; no se sobrescribe."
fi

echo
echo "Listo. Edita azerothcore-wotlk/.env y api/.env, y luego ejecuta:"
echo "  ./scripts/start.sh"
