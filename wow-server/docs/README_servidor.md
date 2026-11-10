# AzerothCore WoW + Docker + Tailscale + API REST

Proyecto: infraestructura cliente-servidor para un servidor privado de World of Warcraft 3.3.5a (WotLK) con administración remota.

## Arquitectura

```
Cliente WoW 3.3.5a
      |
      |  Tailscale (red privada 100.x.x.x)
      v
+-------------------+        +------------------+
|  ac-authserver    |        |  ac-database     |
|  puerto 3724      | <----> |  MySQL 8.4       |
+-------------------+        |  puerto 3307     |
      |                      |  (solo localhost)|
      v                      +------------------+
+-------------------+               ^
|  ac-worldserver   | <-------------+
|  8085 (juego)     |
|  7878 (SOAP)      | <---- API REST (FastAPI, puerto 8001)
+-------------------+
```

## Estructura

```
~/preyecro_docker/
├── azerothcore-wotlk/     # servidor (repo oficial)
│   ├── docker-compose.yml
│   ├── .env               # contraseña de MySQL
│   └── env/dist/          # configuración, logs y datos del cliente
├── api/                   # API REST en Python
│   ├── main.py
│   ├── ejemplo_cliente.py # cambios, cuentas, oro, auditoría y GM
│   ├── crear_cuentas.py   # alta masiva de cuentas
│   ├── crear_npc.py       # crea NPCs desde Python
│   ├── cuentas.json       # lista para crear_cuentas.py
│   ├── .env
│   ├── requirements.txt
│   └── venv/
├── sql/                   # scripts y consultas de ejemplo
├── start.sh
└── stop.sh
```

## Arrancar

```bash
cd ~/preyecro_docker
./start.sh
```

La primera vez tarda varios minutos (importación de las 3 bases y descarga de datos del cliente).

## Parar

```bash
cd ~/preyecro_docker
./stop.sh
```

`stop.sh` usa `docker compose down` (conserva la base de datos en el volumen `ac-database`).

## Credenciales

| Servicio | Usuario | Contraseña |
|---|---|---|
| Cuenta GM del juego | `luis` | `CAMBIAR_GM_PASSWORD` |
| MySQL root (local) | `root` | `CAMBIAR_MYSQL_ROOT_PASSWORD` |
| MySQL API | `acore_api` | `CAMBIAR_MYSQL_API_PASSWORD` |
| API REST (header `X-API-Key`) | — | `CAMBIAR_API_KEY` |
| Código de registro web | — | `CAMBIAR_CODIGO_REGISTRO` |

> Cambia estas claves antes de entregar el proyecto. El registro web solo crea cuentas normales (GM 0).

## API REST

- Documentación interactiva (Swagger): <http://TU_IP_TAILSCALE:8001/docs>
- Todas las rutas protegidas requieren el header `X-API-Key: CAMBIAR_API_KEY`.

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/status` | Estado de contenedores + `server info` |
| POST | `/restart/{worldserver\|authserver}` | Reinicia un servicio |
| POST | `/gm` | Ejecuta un comando GM por SOAP |
| GET | `/accounts` | Lista cuentas y nivel GM |
| POST | `/accounts` | Crea cuenta (`username`, `password`, `gmlevel`) |
| DELETE | `/accounts/{username}` | Elimina cuenta y sus personajes |
| GET | `/characters` | Lista personajes |
| PATCH | `/characters/{name}` | Cambia `level` y/o `money_gold` |
| GET | `/realmlist` | Consulta la configuración del reino |
| PUT | `/realmlist` | Cambia IP/puerto que recibe el cliente |
| POST | `/query` | Ejecuta un `SELECT` (solo lectura) |
| GET | `/audit` | Historial de cambios |

### Ejemplos

```bash
K='X-API-Key: CAMBIAR_API_KEY'
B=http://TU_IP_TAILSCALE:8001

curl -H "$K" $B/status
curl -H "$K" $B/accounts
curl -H "$K" -H 'Content-Type: application/json' \
     -d '{"command":"server info"}' $B/gm
curl -H "$K" -H 'Content-Type: application/json' \
     -d '{"username":"jugador1","password":"clave123","gmlevel":0}' $B/accounts
curl -X PATCH -H "$K" -H 'Content-Type: application/json' \
     -d '{"level":80,"money_gold":1000}' $B/characters/NombreDelPersonaje
curl -H "$K" -H 'Content-Type: application/json' \
     -d '{"address":"100.x.x.x","port":8085}' -X PUT $B/realmlist
```

## Base de datos

Tres bases dentro de `ac-database`:

| Base | Tablas importantes |
|---|---|
| `acore_auth` | `account`, `account_access`, `realmlist`, `admin_audit` |
| `acore_characters` | `characters` (`level`, `money`), `character_inventory` |
| `acore_world` | `creature_template`, `creature`, `item_template` |

El dinero se guarda en **cobre**: `1 oro = 10000`.

Conectarse desde el host (DBeaver, MySQL Workbench, etc.):

```
Host: 127.0.0.1
Puerto: 3307
Usuario: acore_api
Contraseña: CAMBIAR_MYSQL_API_PASSWORD
```

## Tailscale

```bash
sudo tailscale up          # iniciar sesión (una sola vez)
tailscale ip -4            # ver la IP 100.x.x.x
```

Luego hay que decirle al servidor y al cliente esa IP:

```bash
curl -X PUT -H 'X-API-Key: CAMBIAR_API_KEY' -H 'Content-Type: application/json' \
     -d '{"address":"TU_IP_TAILSCALE","port":8085}' \
     http://TU_IP_TAILSCALE:8001/realmlist
```

Y en el cliente, editar `WTF/realmlist.wtf` y `WTF/Config.wtf`:

```
set realmlist TU_IP_TAILSCALE:3724
```

## Comandos GM de prueba (dentro del juego)

```
.levelup 80
.modify money 1000000
.npc add 12345
.gm on
```

## Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| Docker se cierra solo | Falta de RAM. Cierra Brave/juegos y sube la RAM en Docker Desktop → Settings → Resources. |
| `ac-database` no arranca | Otro MySQL usa el puerto 3306. Aquí está mapeado a `127.0.0.1:3307`. |
| El cliente queda en "Conectando" | `realmlist.wtf` o la tabla `acore_auth.realmlist` tienen la IP incorrecta. |
| SOAP responde vacío | Espera a que el worldserver diga `ready...`; el puerto tarda unos segundos. |
| `Access denied` en Tailscale | Ejecuta `sudo tailscale up`. |

## Reproducir desde cero

```bash
git clone --depth 1 https://github.com/azerothcore/azerothcore-wotlk.git
cd azerothcore-wotlk
# ajustar docker-compose.yml: DB en 127.0.0.1:3307 y SOAP en 127.0.0.1:7878
docker compose up -d
```

> Las imágenes usadas son `acore/ac-wotlk-*:master`; no hace falta compilar para el servidor base.
