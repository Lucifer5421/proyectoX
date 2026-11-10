# Guía operativa — WoW 3.3.5a + Docker + Tailscale + Registro web

Documentación de la instalación real de este equipo: arranque, Tailscale, contenedores,
API de registro, acceso desde móviles, publicación con Funnel y resolución de los
problemas que aparecieron.

> **Credenciales:** las contraseñas de MySQL y la `API_KEY` están en
> `api/.env` y `azerothcore-wotlk/.env`. No se copian aquí a propósito.
> El **código público de registro** sí se documenta porque lo necesitan los alumnos.

---

## Índice

1. [Datos de esta instalación](#1-datos-de-esta-instalación)
2. [Arquitectura](#2-arquitectura)
3. [Arranque y parada](#3-arranque-y-parada)
4. [Tailscale](#4-tailscale)
5. [Docker / AzerothCore](#5-docker--azerothcore)
6. [API de registro (FastAPI)](#6-api-de-registro-fastapi)
7. [Acceso desde otros dispositivos](#7-acceso-desde-otros-dispositivos)
8. [Registro de cuentas de juego](#8-registro-de-cuentas-de-juego)
9. [Solución de problemas](#9-solución-de-problemas)
10. [Chuleta de comandos](#10-chuleta-de-comandos)
11. [Seguridad y recomendaciones](#11-seguridad-y-recomendaciones)
12. [Checklist de verificación](#12-checklist-de-verificación)

---

## 1. Datos de esta instalación

| Dato | Valor |
|---|---|
| Máquina | `arch` (Arch Linux), usuario `luis` |
| Proyecto | `/home/luis/preyecro_docker` |
| IP LAN | `192.168.1.210` |
| IP Tailscale | `TU_IP_TAILSCALE` |
| DNS Tailscale | `TU_NODO.tailXXXX.ts.net` |
| Tailnet | `tail8eba6d.ts.net` |
| Cuenta Tailscale | `Lucifer5421` (login con **GitHub**) |
| Versión Tailscale | 1.104.2 |
| Código de registro | `CAMBIAR_CODIGO_REGISTRO` |
| Cuentas de juego existentes | `LUIS`, `LUCI` (WotLK, expansion 2) |

### Puertos

| Puerto | Servicio | Escucha en |
|---|---|---|
| `3724` | Authserver (login del juego) | IP de Tailscale |
| `8085` | Worldserver (mundo) | IP de Tailscale |
| `7878` | SOAP (comandos GM) | `127.0.0.1` |
| `3307` | MySQL | `127.0.0.1` |
| `8001` | API REST / registro web | `0.0.0.0` |
| `443` | Funnel (HTTPS público) | `tailscaled` |

---

## 2. Arquitectura

```
Cliente WoW 3.3.5a
      |
      |  Tailscale (red privada 100.x.x.x)  o  Funnel (solo web)
      v
+-------------------+        +------------------+
|  ac-authserver    |        |  ac-database     |
|  3724            | <----> |  MySQL 8.4       |
+-------------------+        |  3307 (local)    |
      |                      +------------------+
      v                               ^
+-------------------+                  |
|  ac-worldserver   | <----------------+
|  8085 juego       |
|  7878 SOAP        | <---- API REST FastAPI :8001
+-------------------+
```

### Estructura de carpetas

```
~/preyecro_docker/
├── azerothcore-wotlk/      # servidor (repo oficial AzerothCore)
│   ├── docker-compose.yml
│   ├── .env                # DOCKER_BIND_IP, puertos, contraseña MySQL
│   └── env/dist/           # configuración y logs del servidor
├── api/                    # API REST + registro web (FastAPI)
│   ├── main.py
│   ├── .env                # DB, SOAP, API_HOST/PORT, registro
│   ├── venv/
│   └── api.log
├── backups/                # copias .sql.gz
├── sql/
├── start.sh                # arranca contenedores + API
├── stop.sh                 # para API + contenedores
└── backup.sh               # respaldo de las 3 bases
```

---

## 3. Arranque y parada

### Arranque completo

```bash
cd ~/preyecro_docker
./start.sh
```

Hace tres cosas:

1. `docker compose up -d` en `azerothcore-wotlk/`
2. Espera a que el worldserver esté listo
3. Arranca la API si no está corriendo

### Parada

```bash
cd ~/preyecro_docker
./stop.sh
```

> ⚠️ **Ojo:** `stop.sh` hace `pkill -f "uvicorn main:app"`, pero ahora la API está
> gestionada por systemd con `Restart=always`, así que **se volverá a levantar sola**.
> Para pararla de verdad:
>
> ```bash
> systemctl --user stop wow-api
> ```

### Respaldos

```bash
cd ~/preyecro_docker
./backup.sh
```

Genera `backups/azerothcore-AAAAMMDD-HHMMSS.sql.gz` con `acore_auth`,
`acore_characters` y `acore_world`.

---

## 4. Tailscale

### 4.1 Qué hace aquí

Tailscale es la red privada por la que el cliente WoW llega al servidor cuando no
está en la misma Wi-Fi. El servidor **solo publica los puertos 3724 y 8085 en su IP
de Tailscale** (`TU_IP_TAILSCALE`), no en la IP local ni en `0.0.0.0`.

Consecuencia importante:

> Si Tailscale no está autenticado, el nodo **pierde la IP `TU_IP_TAILSCALE`**, los
> contenedores quedan escuchando en una dirección que ya no existe y el cliente WoW
> se queda en **"Connecting"** para siempre.

### 4.2 Iniciar sesión (headless, sin navegador en el servidor)

```bash
tailscale up
```

Imprime una URL del tipo `https://login.tailscale.com/a/xxxxxxxx`. Se abre en otro
dispositivo (móvil/PC) y se autoriza con **GitHub** (`Lucifer5421`).

Verificar:

```bash
tailscale status
tailscale ip -4          # debe devolver TU_IP_TAILSCALE
```

### 4.3 El problema de las dos cuentas (causa real del fallo)

En el log de `tailscaled` aparecía:

```
While you were logged into tailnet "lucifer5421.github",
you attempted to log into tailnet "TU_CUENTA_TAILSCALE",
which does not exist.
```

**Causa:** el navegador tenía sesión en la tailnet de **GitHub**, pero se intentó
autorizar con la cuenta de **Google**, que no tiene tailnet. Tailscale rechaza el
cambio con un `400` y el nodo se queda en `NeedsLogin`.

**Solución:**

1. Cerrar sesión del panel: <https://login.tailscale.com/logout>
2. Abrir la URL de `tailscale up` en **ventana privada**
3. Elegir **"Sign in with GitHub"**

### 4.4 Comandos útiles

```bash
tailscale status            # estado y peers
tailscale ip -4             # IP asignada
tailscale netcheck          # calidad de red / relays DERP
tailscale ping <ip>         # probar un peer
journalctl -u tailscaled -n 50 --no-pager
```

> El aviso `no-derp-connection` con el relay de São Paulo es intermitente y **no
> bloquea**: la conexión directa y los demás relays funcionan.

### 4.5 Arranque automático

`tailscaled` está `enabled`, así que arranca solo al encender la máquina.

---

## 5. Docker / AzerothCore

### 5.1 Contenedores

| Contenedor | Imagen | Estado esperado |
|---|---|---|
| `ac-database` | `mysql:8.4` | `Up (healthy)` |
| `ac-authserver` | `acore/ac-wotlk-authserver:master` | `Up` |
| `ac-worldserver` | `acore/ac-wotlk-worldserver:master` | `Up` |
| `ac-db-import` | `acore/ac-wotlk-db-import:master` | `Exited (0)` (normal) |
| `ac-client-data-init` | `acore/ac-wotlk-client-data:master` | `Exited (0)` (normal) |

```bash
docker ps -a
docker logs --tail 50 ac-worldserver
docker logs --tail 50 ac-authserver
```

### 5.2 Bind a la IP de Tailscale

En `azerothcore-wotlk/.env`:

```env
DOCKER_BIND_IP=TU_IP_TAILSCALE
DOCKER_AUTH_EXTERNAL_PORT=3724
DOCKER_WORLD_EXTERNAL_PORT=8085
```

Esto hace que Docker publique:

```
ac-authserver   TU_IP_TAILSCALE:3724->3724
ac-worldserver  TU_IP_TAILSCALE:8085->8085
```

> ⚠️ Si los contenedores se levantan **antes** de que Tailscale tenga la IP, Docker
> falla con `cannot assign requested address`. Arranca primero Tailscale, o cambia
> `DOCKER_BIND_IP=0.0.0.0` y limita el acceso con firewall/ACLs.

### 5.3 realmlist (lo que recibe el cliente)

Tabla `acore_auth.realmlist`:

| Campo | Valor |
|---|---|
| `address` | `TU_IP_TAILSCALE` |
| `localAddress` | `127.0.0.1` |
| `port` | `8085` |

El authserver la lee al arrancar y escribe en el log:

```
Added realm "AzerothCore" at TU_IP_TAILSCALE:8085.
```

Si cambia la IP de Tailscale hay que actualizar la tabla **y** reiniciar authserver.

### 5.4 Cliente WoW

En `WTF/realmlist.wtf` y `Data/enUS/realmlist.wtf`:

```
set realmlist TU_IP_TAILSCALE:3724
```

En `WTF/Config.wtf`:

```
SET realmList "TU_IP_TAILSCALE:3724"
```

---

## 6. API de registro (FastAPI)

### 6.1 Qué es

Servicio Python en `~/preyecro_docker/api` que sirve:

- Página web de **registro** para alumnos
- API de administración (estado, cuentas, personajes, GM, realmlist, auditoría)

Arranque manual (sin systemd):

```bash
cd ~/preyecro_docker/api
./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
```

### 6.2 Configuración (`api/.env`)

```env
DB_HOST=127.0.0.1
DB_PORT=3307
DB_USER=acore_api
DB_PASSWORD=***            # ver archivo

SOAP_URL=http://127.0.0.1:7878/
SOAP_USER=luis
SOAP_PASS=***              # ver archivo

API_KEY=***                # ver archivo
API_HOST=0.0.0.0
API_PORT=8001

REGISTRATION_ENABLED=1
REGISTRATION_CODE=CAMBIAR_CODIGO_REGISTRO
REGISTRATION_MAX=5
REGISTRATION_WINDOW=3600
```

| Variable | Significado |
|---|---|
| `API_HOST=0.0.0.0` | Escucha en LAN, Tailscale y localhost |
| `REGISTRATION_ENABLED=1` | Activa `/registro` |
| `REGISTRATION_CODE` | Código que piden a los alumnos |
| `REGISTRATION_MAX` | Máximo de registros por IP |
| `REGISTRATION_WINDOW` | Ventana en segundos (3600 = 1 hora) |

### 6.3 Rutas

| Método | Ruta | Protegida | Qué hace |
|---|---|---|---|
| GET | `/` | No | Info del servicio |
| GET | `/registro` | No | Formulario web de registro |
| POST | `/registro` | No (código) | Crea cuenta de juego |
| GET | `/docs` | No | Swagger |
| GET | `/status` | `X-API-Key` | Estado de contenedores |
| POST | `/restart/{service}` | `X-API-Key` | Reinicia auth/world |
| POST | `/gm` | `X-API-Key` | Comando GM por SOAP |
| GET/POST | `/accounts` | `X-API-Key` | Lista / crea cuentas |
| DELETE | `/accounts/{username}` | `X-API-Key` | Borra cuenta y personajes |
| GET | `/characters` | `X-API-Key` | Lista personajes |
| PATCH | `/characters/{name}` | `X-API-Key` | Cambia nivel/oro |
| POST | `/npc` | `X-API-Key` | Crea NPC |
| GET/PUT | `/realmlist` | `X-API-Key` | Consulta / cambia reino |
| POST | `/query` | `X-API-Key` | SELECT de solo lectura |
| GET | `/audit` | `X-API-Key` | Historial de cambios |

Ejemplo:

```bash
K="X-API-Key: $(grep '^API_KEY=' ~/preyecro_docker/api/.env | cut -d= -f2-)"
curl -H "$K" http://127.0.0.1:8001/status
```

### 6.4 Servicio systemd de usuario (persistente)

Archivo: `~/.config/systemd/user/wow-api.service`

```ini
[Unit]
Description=AzerothCore Registration API (FastAPI)
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/luis/preyecro_docker/api
EnvironmentFile=/home/luis/preyecro_docker/api/.env
ExecStart=/home/luis/preyecro_docker/api/venv/bin/uvicorn main:app --host ${API_HOST} --port ${API_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

- `Linger=yes` → arranca al encender el equipo, sin iniciar sesión.
- `Restart=always` → si falla (p. ej. Tailscale aún sin IP), reintenta cada 5 s.

Gestión:

```bash
systemctl --user status wow-api
systemctl --user restart wow-api
systemctl --user stop wow-api
journalctl --user -u wow-api -f
```

---

## 7. Acceso desde otros dispositivos

### 7.1 Misma Wi-Fi (sin instalar nada)

```
http://192.168.1.210:8001/registro
```

Vale para crear cuentas desde el móvil en la misma red.

> Si no carga estando en la misma Wi-Fi, suele ser **aislamiento de clientes** del
> router o estar en la red de invitados. Usa Funnel o Tailscale.

### 7.2 URL pública con Funnel (solo web, sin Tailscale)

```
https://TU_NODO.tailXXXX.ts.net/registro
```

Requisitos y activación:

1. Activar Funnel en el panel: <https://login.tailscale.com/f/funnel>
2. Publicar el puerto:

```bash
tailscale funnel --bg 8001
```

3. Ver estado:

```bash
tailscale funnel status
```

4. Desactivar:

```bash
tailscale funnel --https=443 off
```

Funnel solo publica **HTTPS** (443). Los puertos del juego (`3724`/`8085`) **no** se
pueden publicar así.

El certificado TLS se emite automáticamente vía ACME la primera vez (puede tardar
1–2 minutos; en el log se ve `got cert`).

### 7.3 Compartir el equipo con Tailscale (para jugar) — **Opción recomendada**

No se comparte toda la tailnet, solo el equipo `arch`.

**Quien comparte (tú):**

1. <https://login.tailscale.com/admin/machines>
2. Buscar `arch` (`TU_IP_TAILSCALE`)
3. Menú `⋯` → **Share…**
4. Copiar el enlace

**Quien se conecta (alumno/jugador):**

1. Instalar Tailscale: <https://tailscale.com/download>
2. Crear cuenta gratuita (Google, GitHub o Microsoft)
3. Abrir el enlace de compartir y aceptar
4. Ya puede usar `TU_IP_TAILSCALE`

**Mensaje listo para enviar:**

> Hola, para entrar al servidor:
> 1. Instala Tailscale: https://tailscale.com/download
> 2. Crea una cuenta gratuita (con Google vale).
> 3. Abre este enlace y acepta el equipo compartido: **[pegar enlace]**
> 4. Web para crear cuenta: https://TU_NODO.tailXXXX.ts.net/registro (código: CAMBIAR_CODIGO_REGISTRO)
> 5. Para jugar, en `realmlist.wtf` pon: `set realmlist TU_IP_TAILSCALE:3724`

> Si el enlace de compartir caduca, se genera otro desde `⋯ → Share`.

### 7.4 Invitar a la tailnet (alternativa)

<https://login.tailscale.com/admin/users> → **Invite external users**.

Da acceso a **todos** tus equipos y consume licencia de usuario. Para alumnos es
preferible la opción 7.3.

---

## 8. Registro de cuentas de juego

| Vía | URL |
|---|---|
| LAN | `http://192.168.1.210:8001/registro` |
| Tailscale | `http://TU_IP_TAILSCALE:8001/registro` |
| Pública | `https://TU_NODO.tailXXXX.ts.net/registro` |

- **Código:** `CAMBIAR_CODIGO_REGISTRO`
- **Límite:** 5 registros por IP cada hora
- Crea cuentas normales (GM 0)
- Cuentas ya existentes: `LUIS`, `LUCI`

---

## 9. Solución de problemas

### 9.1 WoW se queda en "Connecting"

**Síntoma:** el cliente no pasa de la pantalla de conexión.

**Causa más probable:** Tailscale está en `NeedsLogin` y el nodo perdió
`TU_IP_TAILSCALE`, pero los contenedores siguen publicados en esa IP.

**Diagnóstico:**

```bash
tailscale status
tailscale ip -4
ss -tlnp | grep -E '3724|8085'
docker logs --tail 20 ac-authserver
```

**Solución:**

```bash
tailscale up        # autorizar con GitHub
tailscale ip -4     # confirmar TU_IP_TAILSCALE
```

Si la IP cambió:

```bash
cd ~/preyecro_docker/azerothcore-wotlk
# editar .env -> DOCKER_BIND_IP=<nueva_ip>
PASS=$(grep -E '^DOCKER_DB_ROOT_PASSWORD=' .env | cut -d= -f2-)
docker exec ac-database mysql -uroot -p"$PASS" \
  -e "UPDATE acore_auth.realmlist SET address='<nueva_ip>' WHERE id=1;"
docker compose up -d --force-recreate
docker restart ac-authserver ac-worldserver
```

### 9.2 Tailscale no deja iniciar sesión

**Síntoma:** `Logged out`, `NeedsLogin`, o error `400` en el navegador.

**Causa:** conflicto de identidades (GitHub vs Google) o sesión antigua en el panel.

**Solución:**

1. <https://login.tailscale.com/logout>
2. `tailscale up`
3. Abrir la URL en ventana privada → **Sign in with GitHub**

Si persiste, usar una **auth key**:

```bash
sudo tailscale up --authkey=tskey-auth-XXXX
```

(Generar en <https://login.tailscale.com/admin/settings/keys>, estando en la tailnet
correcta.)

### 9.3 La página `/registro` no carga

**Diagnóstico:**

```bash
ss -tlnp | grep 8001
systemctl --user status wow-api
curl -I http://127.0.0.1:8001/registro
```

**Causas y soluciones:**

| Causa | Solución |
|---|---|
| API caída | `systemctl --user restart wow-api` |
| Escucha solo en una IP | `API_HOST=0.0.0.0` en `api/.env` + reiniciar |
| Móvil fuera de la red | Usar Funnel o Tailscale |
| Móvil en otra Wi-Fi/red invitados | Usar Funnel o Tailscale |

### 9.4 Los móviles no cargan la página

- Misma Wi-Fi → `http://192.168.1.210:8001/registro`
- Datos móviles / fuera → `https://TU_NODO.tailXXXX.ts.net/registro` (Funnel)
- O instalar Tailscale y usar `http://TU_IP_TAILSCALE:8001/registro`

### 9.5 El certificado de Funnel tarda

Es normal la primera vez. Esperar 1–2 min y comprobar:

```bash
journalctl -u tailscaled -n 50 | grep -iE 'cert|acme'
tailscale funnel status
```

### 9.6 Docker no arranca los contenedores

Si el error es `cannot assign requested address`, es que `DOCKER_BIND_IP` apunta a
una IP de Tailscale que aún no existe. Solución: arrancar Tailscale primero, o usar
`DOCKER_BIND_IP=0.0.0.0`.

---

## 10. Chuleta de comandos

```bash
# --- Tailscale ---
tailscale status
tailscale ip -4
tailscale up
tailscale funnel --bg 8001
tailscale funnel status
tailscale funnel --https=443 off

# --- Docker ---
docker ps -a
docker logs -f ac-worldserver
docker logs -f ac-authserver
docker restart ac-authserver ac-worldserver

# --- API ---
systemctl --user status wow-api
systemctl --user restart wow-api
journalctl --user -u wow-api -f
curl -I http://127.0.0.1:8001/registro

# --- Proyecto ---
cd ~/preyecro_docker && ./start.sh
cd ~/preyecro_docker && ./stop.sh
cd ~/preyecro_docker && ./backup.sh

# --- Comprobar puertos ---
ss -tlnp | grep -E '3724|8085|8001'

# --- Base de datos ---
cd ~/preyecro_docker/azerothcore-wotlk
PASS=$(grep -E '^DOCKER_DB_ROOT_PASSWORD=' .env | cut -d= -f2-)
docker exec ac-database mysql -uroot -p"$PASS" -e "SELECT * FROM acore_auth.realmlist\G"
```

---

## 11. Seguridad y recomendaciones

1. **Cambiar credenciales** antes de entregar el proyecto (MySQL, API key, código de
   registro). Están en los `.env`.
2. **`API_HOST=0.0.0.0`** expone la API en toda red a la que se conecte el equipo.
   Si solo se usa por Tailscale/LAN, limitar con firewall:
   ```bash
   # ejemplo con ufw
   sudo ufw allow from 192.168.1.0/24 to any port 8001
   sudo ufw allow from 100.64.0.0/10 to any port 8001
   sudo ufw deny 8001
   ```
3. **Funnel** publica `/docs` y las rutas de administración en internet. Están
   protegidas por `X-API-Key`, pero conviene no publicar Funnel de forma permanente:
   desactivarlo cuando no se necesite.
4. **Compartir nodo** (7.3) es más seguro que invitar a la tailnet.
5. **Bind frágil:** `DOCKER_BIND_IP=TU_IP_TAILSCALE` depende de Tailscale. Para un
   servidor 24/7, valorar `0.0.0.0` + firewall, o asegurar el orden de arranque.
6. **Backups** periódicos con `./backup.sh` (idealmente con `cron`).
7. La API escribe auditoría en `acore_auth.admin_audit`; revisable con `GET /audit`.

---

## 12. Checklist de verificación

Antes de decir "está listo":

- [ ] `tailscale status` → `Running` y `TU_IP_TAILSCALE`
- [ ] `ss -tlnp | grep -E '3724|8085'` → escuchando en la IP de Tailscale
- [ ] `docker ps` → `ac-database`, `ac-authserver`, `ac-worldserver` arriba
- [ ] `docker logs ac-authserver` → `Added realm "AzerothCore" at TU_IP_TAILSCALE:8085`
- [ ] `systemctl --user is-active wow-api` → `active`
- [ ] `curl -I http://127.0.0.1:8001/registro` → `200`
- [ ] `curl -I https://TU_NODO.tailXXXX.ts.net/registro` → `200`
- [ ] Cliente con `realmlist` → `TU_IP_TAILSCALE:3724`
- [ ] Cuenta de juego existente y login correcto
- [ ] Enlace de compartir generado (si se usa la opción 7.3)

---

*Última actualización: 2026-10-30*
