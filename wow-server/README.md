# Servidor WoW 3.3.5a — AzerothCore + Docker + Tailscale + API

Esta carpeta contiene la **parte custom** del servidor de World of Warcraft
3.3.5a que ya estaba funcionando en `~/preyecro_docker`, copiada y sanitizada
para que forme parte del repositorio de `proyectoX`.

> El código fuente oficial de AzerothCore **no** se copia aquí (pesa ~1.2 GB y
> ya está publicado por el proyecto). El script `scripts/setup-wow-server.sh`
> clona el repositorio oficial y aplica esta configuración encima.

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

- **Juego:** puertos `3724` (auth) y `8085` (world) publicados **solo** en la IP
  de Tailscale (`DOCKER_BIND_IP`).
- **SOAP:** `127.0.0.1:7878`, solo local.
- **MySQL:** `127.0.0.1:3307`, solo local.
- **API REST:** FastAPI en `127.0.0.1:8001` (o la IP de Tailscale, según
  `API_HOST`), con Swagger en `/docs` y registro web en `/registro`.
- **Base de datos del módulo de subastas:** PostgreSQL aparte, en
  `proyectoX` (puerto `5433`). No se mezcla con el MySQL de AzerothCore.

## Estructura

```
wow-server/
├── README.md                  # este archivo
├── docker-compose.yml         # compose de AzerothCore con los puertos custom
├── .env.example               # plantilla de variables del servidor
├── api/                       # API FastAPI de administración/registro
│   ├── main.py
│   ├── requirements.txt
│   ├── crear_cuentas.py
│   ├── crear_npc.py
│   ├── ejemplo_cliente.py
│   ├── cuentas.ejemplo.json
│   └── .env.example
├── scripts/
│   ├── setup-wow-server.sh    # clona AzerothCore y prepara el entorno
│   ├── start.sh               # levanta contenedores + API
│   ├── stop.sh                # detiene la API y los contenedores
│   ├── backup.sh              # respalda las 3 bases en .sql.gz
│   └── sync-wow.sh            # sincroniza datos reales hacia proyectoX
├── systemd/
│   └── wow-api.service        # plantilla de servicio de usuario
├── sql/
│   ├── 01_auditoria.sql
│   └── 02_ejemplos.sql
└── docs/
    ├── README_servidor.md     # documentación original del servidor
    ├── GUIA_OPERATIVA.md      # guía paso a paso
    └── INFORME_COMPLETO.md    # informe técnico completo
```

## Puesta en marcha

Requisitos: Docker, Docker Compose, Python 3.11+, Tailscale y el cliente WoW
3.3.5a.

```bash
cd wow-server
./scripts/setup-wow-server.sh
```

El script:

1. Clona `azerothcore/azerothcore-wotlk` en `wow-server/azerothcore-wotlk/`
   (si no existe).
2. Copia `docker-compose.yml` con los puertos custom.
3. Crea `azerothcore-wotlk/.env` desde `.env.example` (si no existe).
4. Crea el virtualenv de la API e instala `api/requirements.txt`.
5. Crea `api/.env` desde `api/.env.example` (si no existe).

Después edita **como mínimo**:

- `azerothcore-wotlk/.env`
  - `DOCKER_DB_ROOT_PASSWORD`: contraseña fuerte de MySQL.
  - `DOCKER_BIND_IP`: tu IP de Tailscale (p. ej. `100.x.y.z`).
  - `DOCKER_AC_CLIENT_FOLDER`: ruta a la carpeta `Data` del cliente WoW.
- `api/.env`
  - `DB_PASSWORD`: contraseña del usuario `acore_api` de MySQL.
  - `SOAP_PASS`: contraseña del usuario GM de SOAP.
  - `API_KEY`: clave que enviarán los clientes en `X-API-Key`.
  - `REGISTRATION_CODE`: código para crear cuentas desde `/registro`.
  - `API_HOST`: `127.0.0.1` si la API es solo local, o la IP de Tailscale.

Luego:

```bash
./scripts/start.sh
docker compose -f azerothcore-wotlk/docker-compose.yml ps
```

Detener y respaldar:

```bash
./scripts/stop.sh
./scripts/backup.sh
```

> El servidor que ya está corriendo en `~/preyecro_docker` **no se modifica**
> con estos scripts. Esta carpeta es una copia reproducible para el repositorio.
> No levantes las dos copias a la vez: comparten nombres de contenedor
> (`ac-database`, `ac-authserver`, `ac-worldserver`).

## API REST

La API está documentada en `docs/README_servidor.md` y en
`http://TU_IP_TAILSCALE:8001/docs` (o `http://127.0.0.1:8001/docs`).

Rutas principales:

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/status` | Estado de contenedores y worldserver. |
| `GET` | `/accounts` | Lista cuentas. |
| `POST` | `/accounts` | Crea una cuenta. |
| `GET` | `/characters` | Lista personajes. |
| `PUT` | `/characters/{nombre}` | Cambia nivel/oro de un personaje. |
| `POST` | `/gm` | Ejecuta un comando GM por SOAP. |
| `GET` | `/registro` | Portal web de registro. |
| `GET` | `/docs` | Swagger. |

Las rutas protegidas requieren `X-API-Key: <API_KEY>`.

## Integración con `proyectoX` (subastas)

El módulo de subastas sigue usando **PostgreSQL** y no se conecta al MySQL de
AzerothCore en tiempo de ejecución. La integración es un **CLI de solo
lectura** que copia personajes, oro e inventario reales hacia PostgreSQL:

```bash
cd ..                      # raíz de proyectoX
wow-server/scripts/sync-wow.sh --dry-run
wow-server/scripts/sync-wow.sh
wow-server/scripts/sync-wow.sh --skip-gold
```

- `--dry-run`: muestra lo que haría, sin escribir.
- `--skip-gold`: sincroniza personajes/ítems pero conserva el oro de la demo.
- El script lee `wow-server/api/.env` para las credenciales MySQL y
  `proyectoX/.env` para `DATABASE_URL_LOCAL`.
- **Nunca escribe en `acore_auth`, `acore_characters` ni `acore_world`.**
- El detalle técnico está en `../docs/integracion_wow.md`.

Si más adelante se quiere que la casa de subastas entregue ítems dentro del
juego, hay dos caminos:

1. Enviar correo/ítems por SOAP o por la API (requiere permisos y pruebas).
2. Instalar `mod-auctionsim` en AzerothCore (C++, requiere recompilar el
   worldserver). Es **opcional** y no forma parte de la entrega principal.

## Seguridad

- No publiques `.env`, `api/.env`, `backups/` ni el clon
  `azerothcore-wotlk/`: están en `.gitignore`.
- Cambia todas las contraseñas de ejemplo antes de usar el servidor.
- Los puertos del juego deben escuchar solo en Tailscale, nunca en `0.0.0.0`.
- La API debe ir detrás de Tailscale/Funnel o en `127.0.0.1`; no la expongas
  directamente a Internet.
- Los documentos de `docs/` son la versión histórica del montaje; las rutas
  `~/preyecro_docker` y los nombres de host pueden diferir de tu instalación.
