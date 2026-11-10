#!/usr/bin/env bash
# Arranca el servidor AzerothCore y la API REST.
set -euo pipefail

BASE="$(cd "$(dirname "$0")" && pwd)"

echo "==> Levantando contenedores..."
cd "$BASE/azerothcore-wotlk"
docker compose up -d

echo "==> Esperando a que el worldserver este listo..."
for i in $(seq 1 60); do
    if docker compose logs ac-worldserver 2>&1 | grep -q "worldserver-daemon) ready"; then
        break
    fi
    sleep 2
done

echo "==> Iniciando API REST..."
cd "$BASE/api"
if pgrep -f "uvicorn main:app" >/dev/null 2>&1; then
    echo "    La API ya estaba corriendo."
else
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
    nohup ./venv/bin/uvicorn main:app --host "${API_HOST:-127.0.0.1}" --port "${API_PORT:-8001}" \
        > api.log 2>&1 </dev/null & disown
    sleep 2
    echo "    API iniciada en http://${API_HOST:-127.0.0.1}:${API_PORT:-8001}"
fi

echo
echo "==> Estado:"
cd "$BASE/azerothcore-wotlk"
docker compose ps
echo
echo "Documentacion de la API: http://${API_HOST:-127.0.0.1}:${API_PORT:-8001}/docs"
