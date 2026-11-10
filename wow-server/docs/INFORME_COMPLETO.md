# Informe completo — Servidor AzerothCore 3.3.5a + Docker + Tailscale + API

**Proyecto:** servidor privado de World of Warcraft 3.3.5a (WotLK)  
**Máquina servidor:** Arch Linux, 14 GB de RAM, Docker Desktop  
**Fecha del informe:** 29/30 de octubre de 2026  
**IP LAN del servidor:** `192.168.100.28`  
**IP Tailscale:** `TU_IP_TAILSCALE`  
**Nombre Tailscale:** `TU_NODO.tailXXXX.ts.net`  
**Cuenta Tailscale:** `TU_CUENTA_TAILSCALE`  
**Cliente WoW:** ChromieCraft 3.3.5a, build `12340`, en `/home/luis/Descargas/ChromieCraft_3.3.5a`

> **Advertencia de seguridad:** este documento contiene contraseñas y claves del servidor. No lo publiques ni lo compartas tal cual. Cambia las credenciales antes de entregar el proyecto y elimina esta sección si vas a subirlo a GitHub.

---

## Índice

1. Resumen ejecutivo
2. Entorno inicial y problemas encontrados
3. Cronología completa de lo realizado
4. Permisos, usuarios y credenciales
5. Reinicios y eventos de Docker
6. Lo completado, lo que falló y lo pendiente
7. Estado actual
8. Guía paso a paso para que un amigo o compañero se conecte desde Windows
9. Solución de problemas
10. Comandos útiles y rutas
11. Siguientes pasos recomendados
12. Seguridad antes de invitar
13. Apéndice: endpoints, puertos y consultas

---

## 1. Resumen ejecutivo

El servidor está funcionando:

- Docker Desktop con tres contenedores activos: `ac-database`, `ac-authserver` y `ac-worldserver`.
- Las tres bases están importadas: `acore_auth`, `acore_characters` y `acore_world`.
- Cuenta GM: `luis` / `CAMBIAR_GM_PASSWORD`, nivel GM 3.
- SOAP activo y probado.
- API REST funcionando en `http://TU_IP_TAILSCALE:8001` (incluye Swagger en `/docs`, portal web en `/registro` y endpoint `/npc`).
- Tailscale instalado, servicio activo y conectado con IP `TU_IP_TAILSCALE`.
- Puertos del juego (`3724` y `8085`) protegidos y escuchando **exclusivamente en la IP de Tailscale** (`TU_IP_TAILSCALE`).
- El cliente WoW autenticó contra el servidor (`AUTH_OK`) y el personaje principal **`Luis`** está creado, nivel 80, 2000 de oro y verificado en el mundo.
- Cuenta de compañero **`LUCI`** creada con éxito desde la página web `/registro` (código `CAMBIAR_CODIGO_REGISTRO`).
- Scripts en Python probados y funcionales: generación de NPCs en vivo (`Mottled Crimson Raptor`), modificación de nivel y oro, y registro en `admin_audit`.
- Respaldo de la base: `backups/azerothcore-20261029-210140.sql.gz` (82 MB).

Lo que falta para cerrar la demo con la clase:

1. Que los compañeros o docente instalen Tailscale en Windows, acepten el enlace de invitación de la máquina y configuren su `realmlist.wtf`.
2. Probar la conexión simultánea desde Windows con la cuenta `LUCI` o nuevas cuentas.
3. Que los alumnos ejecuten sus propios scripts de Python en VS Code para interactuar con el servidor.
4. Opcional: instalar el módulo `mod-auctionsim`.
5. Cambiar las contraseñas débiles antes de la entrega final.

---

## 2. Entorno inicial y problemas encontrados

### 2.1 Estado inicial de la PC

- Arch Linux con Docker Desktop.
- MariaDB local ocupando el puerto `3306`.
- httpd local corriendo.
- Tailscale instalado pero **sin login**.
- `sudo` pedía contraseña; el asistente no podía ejecutar `sudo`.
- 14 GB de RAM; Brave y otros programas consumían mucha memoria.
- Cliente WoW de ChromieCraft 3.3.5a descargado, con el realmlist apuntando a `100.99.62.32` (servidor del instructor).
- Había dos copias del cliente; una era un duplicado.

### 2.2 Errores del `docker-compose.yml` original del usuario

El compose que estaba en `~/Descargas/docker-compose.yml` tenía estos problemas:

| Problema | Detalle |
|---|---|
| Imagen inexistente | Usaba `acore/ac-worldserver:latest`, que da 404. La correcta es `acore/ac-wotlk-worldserver`. |
| MySQL expuesto | Publicaba `3306` en `0.0.0.0`, chocando con MariaDB local. |
| SSH innecesario | Publicaba el puerto `2222`. |
| SOAP público | Publicaba `7878` a toda la red. |
| Healthcheck mal escrito | Faltaban comillas. |
| Auth mal mapeado | Usaba `3725:3724`. |

Por eso se decidió usar el **repositorio oficial de AzerothCore** en vez de ese compose.

### 2.3 Problema de memoria RAM

Docker Desktop se cerró varias veces por falta de memoria:

- El kernel mató procesos por OOM.
- Se confirmó en logs: `Out of memory: Killed process 2500 (brave)` y `com.docker.back invoked oom-killer`.
- Docker Desktop generó el diagnóstico `4B376579-5FE8-4F95-8A9D-5A06257C28B9` y el archivo `/tmp/4B376579-5FE8-4F95-8A9D-5A06257C28B9/20261030004733.zip`.
- Se intentó subir la RAM de Docker Desktop a 4.6 GB y luego a 4 GB.
- Después del último reinicio, la VM quedó en **~3.8 GB**. Es suficiente y está estable.
- Se creó un respaldo de la configuración: `~/.docker/desktop/settings-store.json.bak`.

### 2.4 Contraseña de GitHub

Se escribió una contraseña de GitHub en el chat. **No se usó**, no se creó ningún repositorio y no se hizo push.

**Cámbiala y activa 2FA.** No se incluye en este documento por seguridad.

---

## 3. Cronología completa de lo realizado

### 3.1 Limpieza y descarga del servidor

1. Se verificó que no existía una copia funcional de AzerothCore.
2. Se borró una carpeta duplicada del cliente:
   - `/home/luis/Descargas/ChromieCraft_3.3.5a/ChromieCraft_3.3.5a`
   - Se liberaron ~17 GB.
   - Se conservó el ZIP original `chromiecraft_3.3.5a.zip` (17.6 GB).
3. Se clonó el repositorio oficial:

```bash
git clone --depth 1 --single-branch https://github.com/azerothcore/azerothcore-wotlk.git
```

- Tamaño: ~1.2 GB.
- Tiempo: ~71 segundos.

4. El proyecto quedó en:

```
/home/luis/preyecro_docker/azerothcore-wotlk
```

### 3.2 Configuración de Docker y del compose

Se editó `docker-compose.yml`:

| Puerto | Antes | Después |
|---|---|---|
| MySQL | `3306:3306` | `127.0.0.1:3307:3306` |
| SOAP | `7878:7878` | `127.0.0.1:7878:7878` |
| Auth | `3724:3724` | `3724:3724` |
| Mundo | `8085:8085` | `8085:8085` |

Se creó `.env` en `azerothcore-wotlk/`:

```env
DOCKER_DB_ROOT_PASSWORD=CAMBIAR_MYSQL_ROOT_PASSWORD
DOCKER_DB_EXTERNAL_PORT=3307
DOCKER_SOAP_EXTERNAL_PORT=7878

# Carpeta del cliente WoW (solo se usa para extraer mapas con el perfil "tools")
DOCKER_AC_CLIENT_FOLDER=/home/luis/Descargas/ChromieCraft_3.3.5a
```

Se crearon las carpetas:

```
env/dist/etc
env/dist/logs
env/dist/data
```

Se validó el compose con:

```bash
docker compose config
```

Resultado: correcto.

### 3.3 Descarga de imágenes Docker

Se descargaron correctamente:

- `acore/ac-wotlk-client-data:master`
- `acore/ac-wotlk-authserver:master`
- `acore/ac-wotlk-worldserver:master`
- `acore/ac-wotlk-db-import:master`
- `mysql:8.4`

`mysql:8.4` falló la primera vez con `unexpected EOF` porque Docker Desktop se cerró por OOM. Después de reiniciar Docker Desktop, la descarga terminó bien.

### 3.4 Levantamiento del servidor

Comando:

```bash
docker compose up -d
```

Resultado:

- `ac-database`: creada y healthy.
- `ac-db-import`: ejecutó la importación y terminó con código `0`.
- `ac-client-data-init`: descargó y descomprimió 1.14 GB de datos del cliente; terminó con código `0`.
- `ac-authserver`: arriba.
- `ac-worldserver`: arriba.

Se verificaron las bases:

```
acore_auth
acore_characters
acore_world
```

El worldserver mostró:

```
WORLD: World Initialized In 0 Minutes 5 Seconds
AzerothCore rev. 993b45959556+ 2026-10-28 23:43:44 +0000 (master branch)
(worldserver-daemon) ready...
```

Apareció un aviso `ALE.BytecodeCache` faltante en la configuración; es **inofensivo** y no impide el funcionamiento.

### 3.5 Cuenta GM

Se creó la cuenta usando la consola del worldserver mediante un PTY de Python:

```bash
account create luis CAMBIAR_GM_PASSWORD
account set gmlevel luis 3 -1
```

Resultado:

```
Account created: luis
You change security level of account LUIS to 3.
```

Verificación en MySQL:

```
id: 1
username: LUIS
gmlevel: 3
RealmID: -1
```

### 3.6 SOAP

Se editó `env/dist/etc/worldserver.conf`:

```conf
SOAP.Enabled = 1
SOAP.IP = "0.0.0.0"
SOAP.Port = 7878
```

Detalle importante:

- Primero se puso `SOAP.IP = "127.0.0.1"` y **no funcionaba** desde el host, porque Docker le habla al contenedor por su IP interna.
- Se cambió a `0.0.0.0` dentro del contenedor.
- El host sigue publicando SOAP solo en `127.0.0.1:7878`, así que no queda expuesto a la red.

Se reinició el worldserver y se probó:

```bash
curl -u luis:CAMBIAR_GM_PASSWORD ...
```

Respuesta:

```
AzerothCore rev. 993b45959556+ ...
Connected players: 0 (peak: 0)
Server uptime: 33 second(s)
```

SOAP funcionando.

### 3.7 API REST en Python

Se creó el proyecto:

```
/home/luis/preyecro_docker/api
```

Se creó un entorno virtual con Python 3.14 y se instalaron:

- FastAPI 0.162.0
- Uvicorn 0.54.0
- PyMySQL
- cryptography
- requests
- docker
- python-dotenv

Se creó el usuario de base de datos `acore_api` con permisos limitados:

```sql
CREATE USER 'acore_api'@'%' IDENTIFIED BY 'CAMBIAR_MYSQL_API_PASSWORD';

GRANT SELECT, INSERT, UPDATE, DELETE ON acore_auth.* TO 'acore_api'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON acore_characters.* TO 'acore_api'@'%';
GRANT SELECT ON acore_world.* TO 'acore_api'@'%';
```

Se creó la tabla de auditoría:

```sql
CREATE TABLE acore_auth.admin_audit (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuario VARCHAR(64) NOT NULL,
  accion VARCHAR(64) NOT NULL,
  detalle TEXT
);
```

Archivos creados:

```
api/main.py
api/.env
api/requirements.txt
api/venv/
```

Endpoints implementados:

| Método | Ruta | Función |
|---|---|---|
| GET | `/` | Información básica |
| GET | `/status` | Estado de contenedores + `server info` |
| POST | `/restart/{service}` | Reinicia `worldserver` o `authserver` |
| POST | `/gm` | Ejecuta comando GM por SOAP |
| GET | `/accounts` | Lista cuentas |
| POST | `/accounts` | Crea cuenta |
| DELETE | `/accounts/{username}` | Elimina cuenta y personajes |
| GET | `/characters` | Lista personajes |
| PATCH | `/characters/{name}` | Cambia nivel y/o oro |
| GET | `/realmlist` | Consulta realmlist |
| PUT | `/realmlist` | Cambia IP/puerto del reino |
| POST | `/query` | Ejecuta un `SELECT` de solo lectura |
| GET | `/audit` | Historial de cambios |

Pruebas realizadas:

| Prueba | Resultado |
|---|---|
| `GET /` | Correcto |
| `GET /status` | Correcto; ve los contenedores y el worldserver |
| `GET /accounts` | Correcto; devuelve `LUIS`, gmlevel 3 |
| `POST /accounts` | Correcto; creó `APITEST` con gmlevel 1 |
| `DELETE /accounts/apitest` | Correcto; eliminó `APITEST` |
| `POST /gm` con `server info` | Correcto |
| `POST /query` con `SELECT ...` | Correcto |
| `GET /realmlist` | Correcto |
| `PUT /realmlist` | Correcto; cambió a `TU_IP_TAILSCALE:8085` |
| `GET /audit` | Correcto; muestra los registros |
| `POST /restart/authserver` | Correcto; reinició y quedó auditado |
| `GET /characters` | Correcto; vacío, 0 personajes |
| `PATCH /characters/{name}` | Pendiente: no hay personaje |
| `POST /restart/worldserver` | No probado; el de authserver ya validó el mecanismo |

La API se inició primero en `127.0.0.1:8001` y luego se cambió a `TU_IP_TAILSCALE:8001` para que sea accesible por Tailscale.

Hubo un incidente: un `pkill` mató al propio shell porque el patrón aparecía en el comando. Se reinició la API sin ese problema. No hubo pérdida de datos.

Documentación interactiva:

```
http://TU_IP_TAILSCALE:8001/docs
```

Header obligatorio en los endpoints protegidos:

```
X-API-Key: CAMBIAR_API_KEY
```

### 3.8 Respaldo y scripts

Se creó `backup.sh`, que hace `mysqldump` de las tres bases y lo comprime.

Prueba real:

```
backups/azerothcore-20261029-210140.sql.gz — 82 MB
```

Se crearon:

- `start.sh`: levanta contenedores y API.
- `stop.sh`: detiene API y contenedores; conserva la base.
- `README.md`: documentación del proyecto.
- `.gitignore`: excluye `.env`, `venv`, logs.
- `sql/01_auditoria.sql`: tabla de auditoría.
- `sql/02_ejemplos.sql`: consultas de ejemplo.

### 3.9 Tailscale

Tailscale ya estaba instalado:

```
paquete: tailscale 1.104.2-1
servicio: active
```

El asistente no podía ejecutar `sudo`; **tú** ejecutaste:

```bash
sudo tailscale up
```

y aceptaste el login. Resultado:

```
TU_IP_TAILSCALE  arch  TU_CUENTA_TAILSCALE  linux
hostname: TU_NODO.tailXXXX.ts.net
```

Se verificó:

- `tailscale serve status` → sin configuración.
- `tailscale funnel status` → sin configuración.
- Es decir, **no hay nada publicado a internet por Tailscale**.

### 3.10 Cliente WoW

El cliente está en:

```
/home/luis/Descargas/ChromieCraft_3.3.5a
```

El problema principal fue que el cliente usa **dos** archivos de realmlist:

```
WTF/realmlist.wtf
Data/enUS/realmlist.wtf
```

El que realmente mandaba era `Data/enUS/realmlist.wtf`, que seguía apuntando a:

```
100.99.62.32
```

Se corrigieron ambos a:

```
set realmlist TU_IP_TAILSCALE:3724
```

También se ajustó `WTF/Config.wtf`:

```
SET realmList "TU_IP_TAILSCALE:3724"
```

El cliente autenticó correctamente:

```
COP_AUTHENTICATE code=AUTH_OK result=TRUE
COP_GET_CHARACTERS code=44 result=TRUE
```

La base registró:

```
LUIS | 2026-10-30 01:14:55 | 192.168.65.1
LUIS | 2026-10-30 01:17:40 | 192.168.65.1
```

Después se desconectó:

```
LOGIN_STATE_DISCONNECTED
```

y quedaron **0 personajes**.

#### Intentos con Wine

Se intentó lanzar el cliente automáticamente con Wine:

- Primer intento: pantalla negra, no dejaba escribir la contraseña.
- Se puso modo ventana 1280x720 (`gxWindow=1`, `gxResolution=1280x720`, `rawMouseEnable=0`).
- Se intentó con `wine explorer /desktop=WoW,1280x720 Wow.exe -windowed -d3d9` (escritorio virtual).
- El cliente llegó a autenticar, pero la interacción seguía incómoda.
- **Conclusión:** no es un problema del servidor. Tú puedes abrir el juego normalmente desde tus archivos, y así ya autenticó. No hace falta usar Wine por terminal.

Se tomó una captura con `spectacle`, pero no fue posible interpretarla automáticamente; el log de conexión fue la prueba definitiva.

### 3.11 Seguridad y exposición de puertos

Estado actual de los puertos:

| Puerto | Servicio | Escucha en | Quién puede llegar |
|---|---|---|---|
| `3724` | Login | `TU_IP_TAILSCALE` | Exclusivamente red Tailscale |
| `8085` | Mundo | `TU_IP_TAILSCALE` | Exclusivamente red Tailscale |
| `8001` | API / Swagger / Registro | `TU_IP_TAILSCALE` | Exclusivamente red Tailscale (con API key) |
| `7878` | SOAP | `127.0.0.1` | Solo la propia PC (localhost) |
| `3307` | MySQL | `127.0.0.1` | Solo la propia PC (localhost) |

Datos adicionales:

- IP LAN: `192.168.100.28`.
- Tailscale IP: `TU_IP_TAILSCALE`.
- **Restricción de puertos aplicada y verificada:** Se configuró `DOCKER_BIND_IP=TU_IP_TAILSCALE` en `.env` y se mapearon los puertos en `docker-compose.yml`. Ningún puerto del juego escucha ya en `0.0.0.0` ni en IPv6 global (`[::]`).
- Tailscale Funnel/Serve: apagado.
- Máquina compartida mediante enlace directo desde la consola de Tailscale para invitar a compañeros.

---

## 4. Permisos, usuarios y credenciales

### 4.1 Permisos

| Acción | Quién la hizo | Nota |
|---|---|---|
| `sudo tailscale up` | Tú | El asistente no tenía la contraseña de sudo. |
| Comandos Docker | Usuario `luis` | Docker Desktop corre como usuario; no hizo falta sudo. |
| Edición de archivos del proyecto | Usuario `luis` | Los archivos son de `luis:luis`. |
| `chmod +x` en scripts | Asistente | `start.sh`, `stop.sh`, `backup.sh`. |
| Creación de usuario MySQL | Asistente | `acore_api` con permisos limitados. |
| Creación de cuenta GM | Asistente | Vía consola del worldserver. |
| Login de Tailscale | Tú | Cuenta `TU_CUENTA_TAILSCALE`. |

### 4.2 Credenciales del servidor

> **No compartas este documento tal cual.** Cambia estas claves antes de entregar el proyecto.

| Servicio | Usuario | Contraseña | Notas |
|---|---|---|---|
| Cuenta GM del juego | `luis` | `CAMBIAR_GM_PASSWORD` | GM nivel 3; cámbiala antes de invitar amigos |
| MySQL root | `root` | `CAMBIAR_MYSQL_ROOT_PASSWORD` | Solo accesible en `127.0.0.1:3307` |
| MySQL API | `acore_api` | `CAMBIAR_MYSQL_API_PASSWORD` | Permisos limitados |
| API REST | — | `CAMBIAR_API_KEY` | Header `X-API-Key` |
| Tailscale | `TU_CUENTA_TAILSCALE` | — | IP `TU_IP_TAILSCALE` |
| GitHub | — | — | La contraseña se expuso en el chat; cámbiala |

### 4.3 Permisos de la base de datos

`acore_api` puede:

- `SELECT`, `INSERT`, `UPDATE`, `DELETE` en `acore_auth`.
- `SELECT`, `INSERT`, `UPDATE`, `DELETE` en `acore_characters`.
- `SELECT` en `acore_world`.

No puede borrar bases ni cambiar usuarios.

---

## 5. Reinicios y eventos de Docker

| Evento | Causa | Resultado |
|---|---|---|
| Docker Desktop se cerró | OOM por RAM durante `docker pull mysql:8.4` | Se reinició con `docker desktop start` |
| `mysql:8.4` falló con `unexpected EOF` | Docker murió a mitad de descarga | Se reintentó y funcionó |
| `docker compose up -d` | Levantar servicios | Contenedores creados |
| `ac-db-import` | Importación de las tres bases | Terminó con código 0 |
| `ac-client-data-init` | Descarga de datos del cliente | Terminó con código 0 |
| Worldserver reiniciado | Activar `SOAP.Enabled=1` | SOAP activo |
| Worldserver reiniciado otra vez | Cambiar `SOAP.IP` a `0.0.0.0` | SOAP responde |
| Authserver reiniciado | Actualizar realmlist a `TU_IP_TAILSCALE` | `Auth.log`: “Added realm at TU_IP_TAILSCALE:8085” |
| API reiniciada | Cambiar de `127.0.0.1` a `TU_IP_TAILSCALE` | API accesible por Tailscale |
| API reiniciada | Un `pkill` mató el shell por error | Se levantó de nuevo sin pérdida de datos |
| Authserver reiniciado por API | Prueba de `/restart/authserver` | Funcionó y quedó auditado |

**No se ejecutó `docker compose down`**, así que la base y los volúmenes se conservaron.  
**No se borró ninguna base** después de la importación.

---

## 6. Lo completado, lo que falló y lo pendiente

### Completado

- Repositorio oficial clonado e instalado.
- `docker-compose.yml` corregido y validado.
- Imágenes Docker descargadas.
- Bases `acore_auth`, `acore_characters` y `acore_world` importadas.
- Datos de cliente descargados (1.14 GB).
- Cuenta GM `luis` con nivel 3.
- SOAP activo y probado.
- API REST creada, con base de datos propia y tabla `admin_audit`.
- Endpoints de estado, cuentas, GM, consultas, realmlist, registro web y auditoría probados.
- Creación de personaje `Luis` completada (nivel 80, 2000 oro, verificado online y en base de datos).
- Endpoint `POST /npc` creado y probado (spawn de `Mottled Crimson Raptor` entry 12345 en vivo al lado de `Luis`).
- Página web de auto-registro `/registro` completada y probada (creación de cuenta `LUCI`, `gmlevel 0`).
- Puertos del juego restringidos a Tailscale-only (`TU_IP_TAILSCALE`).
- Scripts de Python para estudiantes (`ejemplo_estudiantes.py`, `mi_script.py`, `crear_cuentas.py`, `crear_npc.py`).
- Respaldo de 82 MB generado.
- Scripts `start.sh`, `stop.sh`, `backup.sh`.
- Tailscale conectado con IP `TU_IP_TAILSCALE` y máquina configurada para compartir.
- Cliente WoW autenticando contra el servidor.
- Documentación `README.md` y ejemplos SQL.

### No completado o que falló

| Tema | Detalle |
|---|---|
| Lanzamiento automático con Wine | Pantalla negra y problemas de teclado; se descartó. El cliente abre perfecto normalmente. |
| `mod-auctionsim` | No instalado; es opcional y requiere recompilar. |
| Prueba simultánea con amigo en Windows | Pendiente de que el compañero acepte el enlace de Tailscale y conecte su cliente. |
| RAM exacta de Docker | Quedó en ~3.8 GB, no en 4 GB; es estable. |
| Repositorio GitHub | No se creó ni se hizo push; la contraseña se expuso y debe cambiarse. |
| `/restart/worldserver` | No probado; `/restart/authserver` ya validó el mecanismo. |

### Pendiente

1. Compartir el enlace de invitación de Tailscale con el compañero o docente.
2. Que el compañero instale Tailscale en Windows, apunte su `realmlist.wtf` a `TU_IP_TAILSCALE:3724` y entre con `LUCI`.
3. Que los alumnos ejecuten en VS Code `ejemplo_estudiantes.py` para probar sus propias modificaciones.
4. Cambiar contraseñas débiles antes de la entrega formal.
5. Opcional: instalar `mod-auctionsim`.
6. Respaldo final y demo.

---

## 7. Estado actual

| Elemento | Estado |
|---|---|
| Docker Desktop | Corriendo |
| `ac-database` | Activo y healthy (`127.0.0.1:3307`) |
| `ac-authserver` | Activo (`TU_IP_TAILSCALE:3724`) |
| `ac-worldserver` | Activo (`TU_IP_TAILSCALE:8085`) |
| API REST | `http://TU_IP_TAILSCALE:8001` (activo con daemon) |
| Swagger Docs | `http://TU_IP_TAILSCALE:8001/docs` → HTTP 200 |
| Portal Web Registro | `http://TU_IP_TAILSCALE:8001/registro` (código: `CAMBIAR_CODIGO_REGISTRO`) |
| Cuenta GM | `LUIS` (gmlevel 3, expansión 2) |
| Cuentas registradas | `LUIS` (GM 3), `LUCI` (GM 0) |
| Personajes | `Luis` (GUID 1, Humano Pícaro, nivel 80, 2000 oro) |
| Tailscale | Conectado, `TU_IP_TAILSCALE` (nodo `arch`) |
| Realmlist DB | `TU_IP_TAILSCALE:8085`, build 12340 |
| Cliente | `Data/enUS/realmlist.wtf` correcto (`TU_IP_TAILSCALE:3724`) |
| Puertos del juego | Solo `TU_IP_TAILSCALE` (Tailscale) |
| API | Solo `TU_IP_TAILSCALE` (Tailscale) |
| SOAP / MySQL | Solo `127.0.0.1` (Localhost) |
| Respaldo | `backups/azerothcore-20261029-210140.sql.gz` (82 MB) |
| Auditoría | Con registros de cuentas, personajes, reinicios y creación de NPCs |

Comandos de verificación:

```bash
cd /home/luis/preyecro_docker/azerothcore-wotlk
docker compose ps

curl -H "X-API-Key: CAMBIAR_API_KEY" \
  http://TU_IP_TAILSCALE:8001/status

ss -ltnp | grep -E '3724|8085|8001|7878|3307'

tailscale status
```

---

## 8. Guía paso a paso para que un amigo o compañero se conecte desde Windows

### 8.1 Idea clave

Tu IP `TU_IP_TAILSCALE` es una IP **privada de Tailscale**. No basta con saberla: el amigo tiene que estar autorizado de alguna de estas dos formas:

1. **Compartir tu nodo** con él (recomendado para un solo amigo).
2. **Invitarlo a tu tailnet** (útil para varios compañeros).

El amigo necesita:

- Una cuenta propia de Tailscale.
- El cliente de Tailscale para Windows.
- El cliente WoW 3.3.5a, build `12340`.
- Los archivos `realmlist.wtf` apuntando a `TU_IP_TAILSCALE:3724`.

El amigo **no necesita Linux, Docker ni la API**. Solo Tailscale y el juego.

---

### 8.2 Preparar el servidor en Arch Linux (lo haces tú)

1. Abre Docker Desktop o arráncalo:

```bash
docker desktop start
```

2. Verifica Tailscale:

```bash
tailscale status
```

Debe aparecer `TU_IP_TAILSCALE arch ...`.

3. Arranca el servidor y la API:

```bash
cd /home/luis/preyecro_docker
./start.sh
```

4. Verifica que todo esté arriba:

```bash
cd /home/luis/preyecro_docker/azerothcore-wotlk
docker compose ps

curl -H "X-API-Key: CAMBIAR_API_KEY" \
  http://TU_IP_TAILSCALE:8001/status
```

5. Verifica el realmlist de la base:

```bash
docker exec ac-database mysql -uroot -pCAMBIAR_MYSQL_ROOT_PASSWORD -e \
"SELECT id,name,address,localAddress,port,gamebuild FROM acore_auth.realmlist;"
```

Debe salir:

```
address: TU_IP_TAILSCALE
localAddress: 127.0.0.1
port: 8085
gamebuild: 12340
```

6. Crea una cuenta **sin GM** para el amigo:

```bash
curl -X POST \
  -H "X-API-Key: CAMBIAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"amigo1","password":"clave123","gmlevel":0}' \
  http://TU_IP_TAILSCALE:8001/accounts
```

Notas:

- Usuario: 3 a 16 caracteres alfanuméricos.
- Contraseña: 6 a 16 caracteres alfanuméricos.
- Si la API rechaza la contraseña, usa solo letras y números.
- No le des la cuenta `luis`; esa es GM nivel 3.

7. Comprueba que la cuenta existe:

```bash
curl -H "X-API-Key: CAMBIAR_API_KEY" \
  http://TU_IP_TAILSCALE:8001/accounts
```

También puedes crear la cuenta desde la consola del worldserver:

```bash
docker attach ac-worldserver
account create amigo1 clave123
account set gmlevel amigo1 0 -1
```

Para salir sin apagar el servidor: `Ctrl+P`, luego `Ctrl+Q`. No uses `Ctrl+C`.

---

### 8.3 Invitar al amigo por Tailscale

#### Opción A — Compartir solo tu nodo (recomendada)

Es la más segura para un servidor: el amigo accede solo a tu máquina, no a todos tus dispositivos.

1. Entra a:

```
https://login.tailscale.com/admin/machines
```

2. Busca tu máquina `arch` con IP `TU_IP_TAILSCALE`.

3. Haz clic en el menú `...` de esa máquina.

4. Elige **Share** / **Compartir**.

5. Copia el enlace y envíalo al amigo por WhatsApp, correo, etc.

6. El amigo abre el enlace, inicia sesión o crea una cuenta Tailscale y acepta.

7. Instala Tailscale en Windows y entra con **esa misma cuenta**.

8. En su lista de máquinas debe aparecer `arch` como nodo compartido.

Notas:

- El enlace puede caducar; si pasa, genera otro.
- El amigo no entra a tu tailnet; solo ve ese nodo.
- Es la opción recomendada para una demo con un amigo.
- Si el plan gratuito marca un límite, revisa el plan o usa otra cuenta/organización.

#### Opción B — Invitar a tu tailnet (para varios compañeros)

1. Entra a:

```
https://login.tailscale.com/admin/users
```

2. Usa **Invite external users** / **Invitar usuarios**.

3. Escribe el correo del amigo y envía la invitación.

4. El amigo acepta, crea su cuenta Tailscale e instala el cliente de Windows.

5. Al aceptar, entra a tu tailnet y puede ver tus dispositivos.

Ventaja: es más cómodo para un grupo.  
Desventaja: por defecto puede acceder a más de lo necesario. Si vas a usar esta opción, configura ACLs para limitar el acceso a los puertos `3724` y `8085`.

#### Opción C — Tailnet de la clase

Si el instructor tiene una tailnet común y te invita, podrías unirte a esa red. Pero:

- Tu servidor está hoy en **tu** tailnet.
- Al cambiar de cuenta Tailscale, tu IP puede cambiar.
- Habría que actualizar `.env`, el compose, la base `realmlist`, el cliente y el README.

Para la demo, es más simple compartir tu nodo o invitar al amigo a tu tailnet.

**Importante:** no le des tu cuenta `TU_CUENTA_TAILSCALE` ni tu contraseña de Tailscale. Él debe usar su propia cuenta y aceptar el share/invitación.

---

### 8.4 Instalar Tailscale en Windows (lo hace el amigo)

1. Descarga el instalador desde:

```
https://tailscale.com/download/windows
```

2. Ejecútalo. Necesita permisos de administrador.

3. Cuando se abra, pulsa **Log in**.

4. Inicia sesión con la cuenta que aceptó el share o la invitación.

5. Verifica que el icono de Tailscale diga **Connected**.

6. Abre PowerShell y prueba:

```powershell
tailscale status
ping TU_IP_TAILSCALE
Test-NetConnection TU_IP_TAILSCALE -Port 3724
Test-NetConnection TU_IP_TAILSCALE -Port 8085
```

Lo importante es:

```
TcpTestSucceeded : True
```

en ambos puertos.

7. Prueba la API desde el navegador:

```
http://TU_IP_TAILSCALE:8001/docs
```

Si carga la página de Swagger, la conexión Tailscale funciona.  
Si no carga, el problema es Tailscale, el share o las ACLs; el juego tampoco va a conectar.

8. Si Windows pregunta por el firewall, permite Tailscale y `Wow.exe` en redes privadas.

---

### 8.5 Preparar el cliente WoW en Windows

1. Consigue el **mismo cliente 3.3.5a, build 12340**.

   Opciones:
   - Copiar la carpeta extraída desde tu PC por USB o disco externo.
   - Descargar el mismo cliente ChromieCraft 3.3.5a.

   Necesita unos **20 GB libres**.

2. Colócalo en una carpeta con permisos de usuario, por ejemplo:

```
C:\WoW-3.3.5a
```

Evita `C:\Program Files` para no tener problemas de permisos.

3. Si copiaste tu carpeta completa, borra en la copia del amigo:

```
WTF\Account
Cache
```

Así no lleva tus perfiles ni datos viejos.

4. Edita el archivo:

```
C:\WoW-3.3.5a\Data\enUS\realmlist.wtf
```

con Notepad. Debe contener exactamente:

```
set realmlist TU_IP_TAILSCALE:3724
```

Si el cliente es de otro idioma, la ruta puede ser `Data\esES\realmlist.wtf` o similar. Usa la carpeta de idioma que tenga el cliente.

5. Edita también:

```
C:\WoW-3.3.5a\WTF\realmlist.wtf
```

con la misma línea. Si no existe la carpeta `WTF`, créala.

6. Opcional, en:

```
C:\WoW-3.3.5a\WTF\Config.wtf
```

agrega o corrige:

```
SET realmList "TU_IP_TAILSCALE:3724"
```

El juego puede sobrescribir `Config.wtf`; el archivo que manda es `Data\enUS\realmlist.wtf`.

7. Asegúrate de que el archivo se llame `realmlist.wtf`, no `realmlist.wtf.txt`. En Notepad usa **Guardar como → Todos los archivos**.

8. Ejecuta `Wow.exe` **directamente**. No uses el launcher de ChromieCraft si lo tiene, porque puede volver a poner el realmlist del servidor de ChromieCraft.

9. En la pantalla de login debe verse abajo:

```
3.3.5a (12340)
```

10. Entra con la cuenta del amigo, elige el reino y crea el personaje.

---

### 8.6 Verificar desde el servidor

Cuando el amigo entre:

```bash
curl -H "X-API-Key: CAMBIAR_API_KEY" \
  http://TU_IP_TAILSCALE:8001/status

curl -H "X-API-Key: CAMBIAR_API_KEY" \
  http://TU_IP_TAILSCALE:8001/accounts

curl -H "X-API-Key: CAMBIAR_API_KEY" \
  http://TU_IP_TAILSCALE:8001/characters
```

También puedes ver los logs:

```bash
cd /home/luis/preyecro_docker/azerothcore-wotlk
docker compose logs ac-authserver
docker compose logs ac-worldserver
```

o:

```bash
tail -f env/dist/logs/Auth.log
```

Si el personaje aparece en `/characters`, ya puedes probar:

```bash
curl -X PATCH \
  -H "X-API-Key: CAMBIAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"level":80,"money_gold":1000}' \
  http://TU_IP_TAILSCALE:8001/characters/NOMBRE_DEL_PERSONAJE
```

Hazlo con el personaje **desconectado**; si está online, el juego puede sobrescribir los cambios al guardar.

Comandos GM en el juego, solo con la cuenta `luis`:

```
.levelup 80
.modify money 10000000
.npc add <entry_valida>
```

`10000000` de cobre = 1000 de oro.  
`.npc add 12345` solo funciona si esa entrada existe en `creature_template`; si no, prueba otra.

---

### 8.7 Probar sin un segundo PC

Puedes validar Tailscale antes de que el amigo esté disponible:

1. Instala Tailscale en tu teléfono.
2. Inicia sesión con tu cuenta o acepta el share.
3. Abre en el navegador del teléfono:

```
http://TU_IP_TAILSCALE:8001/docs
```

Si carga, Tailscale funciona.  
Si no carga, revisa que el teléfono esté conectado a Tailscale y que el servidor esté encendido.

La prueba definitiva del juego requiere el cliente WoW en Windows.

---

## 9. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El amigo no puede hacer ping ni abrir `/docs` | Tailscale desconectado, share no aceptado o ACL | Revisar icono de Tailscale, `tailscale status`, aceptar el share, revisar ACLs |
| `/docs` carga pero el juego no conecta | Realmlist mal, versión incorrecta o puerto bloqueado | Revisar `realmlist.wtf`, build 12340, `Test-NetConnection` a 3724 y 8085 |
| Se queda en “Connecting” | No llega al authserver 3724 | Revisar Tailscale, firewall, que el servidor esté arriba |
| Entra pero se queda en “Retrieving character list” | No llega al worldserver 8085 o realmlist DB mal | Revisar `realmlist` en la base, puerto 8085, Tailscale |
| “Account does not exist” | Cuenta mal escrita o no creada | Crear de nuevo con la API o consola |
| “Already logged in” | Otra sesión abierta | Cerrar el otro cliente y esperar |
| “Version mismatch” | Cliente distinto de 3.3.5a 12340 | Usar el cliente correcto |
| El launcher vuelve a poner otro servidor | El launcher reescribe el realmlist | Ejecutar `Wow.exe` directamente |
| `Config.wtf` se revierte | El juego lo sobrescribe | Editar `Data\enUS\realmlist.wtf`, que es el que manda |
| El amigo está en la misma Wi-Fi pero no usa Tailscale | El realmlist DB apunta a la IP Tailscale | Instalar Tailscale; la LAN sola no basta para el puerto 8085 |
| La IP de Tailscale cambió | Se reinstaló o reautenticó el nodo | Actualizar `.env`, compose, base `realmlist`, cliente y README |
| El servidor no responde | Docker Desktop apagado, PC dormida o Tailscale caído | Arrancar Docker, `./start.sh`, revisar Tailscale |
| El amigo está en otra tailnet sin share | No tiene ruta al nodo | Compartir el nodo o invitarlo |
| Tailscale gratis marca límite | Límite de usuarios/dispositivos | Usar node sharing o revisar el plan |

---

## 10. Comandos útiles y rutas

### 10.1 Arrancar, detener y respaldar

```bash
cd /home/luis/preyecro_docker
./start.sh
./stop.sh
./backup.sh
```

`start.sh` levanta los contenedores y la API.  
`stop.sh` detiene la API y los contenedores, pero conserva la base.  
`backup.sh` genera un `.sql.gz` en `backups/`.

### 10.2 API

```bash
curl -H "X-API-Key: CAMBIAR_API_KEY" http://TU_IP_TAILSCALE:8001/status
curl -H "X-API-Key: CAMBIAR_API_KEY" http://TU_IP_TAILSCALE:8001/accounts
curl -H "X-API-Key: CAMBIAR_API_KEY" http://TU_IP_TAILSCALE:8001/characters
curl -H "X-API-Key: CAMBIAR_API_KEY" http://TU_IP_TAILSCALE:8001/audit
```

Crear cuenta:

```bash
curl -X POST \
  -H "X-API-Key: CAMBIAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"amigo1","password":"clave123","gmlevel":0}' \
  http://TU_IP_TAILSCALE:8001/accounts
```

Cambiar nivel/oro de un personaje:

```bash
curl -X PATCH \
  -H "X-API-Key: CAMBIAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"level":80,"money_gold":1000}' \
  http://TU_IP_TAILSCALE:8001/characters/NOMBRE
```

Ejecutar comando GM:

```bash
curl -X POST \
  -H "X-API-Key: CAMBIAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"server info"}' \
  http://TU_IP_TAILSCALE:8001/gm
```

Reiniciar authserver:

```bash
curl -X POST \
  -H "X-API-Key: CAMBIAR_API_KEY" \
  http://TU_IP_TAILSCALE:8001/restart/authserver
```

### 10.3 Consola del worldserver

```bash
docker attach ac-worldserver
```

Para salir sin apagar el servidor: `Ctrl+P`, luego `Ctrl+Q`.  
No uses `Ctrl+C`, porque puede detener el worldserver.

### 10.4 Tailscale

```bash
tailscale status
tailscale ip -4
sudo tailscale up
tailscale serve status
tailscale funnel status
```

### 10.5 Consultas SQL útiles

Ver cuentas:

```bash
docker exec ac-database mysql -uroot -pCAMBIAR_MYSQL_ROOT_PASSWORD -e \
"SELECT id,username,last_login FROM acore_auth.account;"
```

Ver realmlist:

```bash
docker exec ac-database mysql -uroot -pCAMBIAR_MYSQL_ROOT_PASSWORD -e \
"SELECT id,name,address,localAddress,port,gamebuild FROM acore_auth.realmlist;"
```

Ver personajes:

```bash
docker exec ac-database mysql -uroot -pCAMBIAR_MYSQL_ROOT_PASSWORD -e \
"SELECT guid,name,level,race,class FROM acore_characters.characters;"
```

Ver auditoría:

```bash
docker exec ac-database mysql -uroot -pCAMBIAR_MYSQL_ROOT_PASSWORD -e \
"SELECT * FROM acore_auth.admin_audit ORDER BY id DESC LIMIT 20;"
```

### 10.6 Rutas importantes

```
preyecro_docker/INFORME_COMPLETO.md
preyecro_docker/README.md
preyecro_docker/start.sh
preyecro_docker/stop.sh
preyecro_docker/backup.sh
preyecro_docker/ejemplo_estudiantes.py
preyecro_docker/sql/01_auditoria.sql
preyecro_docker/sql/02_ejemplos.sql
preyecro_docker/backups/
preyecro_docker/azerothcore-wotlk/docker-compose.yml
preyecro_docker/azerothcore-wotlk/.env
preyecro_docker/azerothcore-wotlk/env/dist/etc/worldserver.conf
preyecro_docker/azerothcore-wotlk/env/dist/logs/
preyecro_docker/api/main.py
preyecro_docker/api/crear_cuentas.py
preyecro_docker/api/crear_npc.py
preyecro_docker/api/ejemplo_cliente.py
preyecro_docker/api/cuentas.json
preyecro_docker/api/.env
Documentos/mi_script.py
Descargas/ChromieCraft_3.3.5a/Data/enUS/realmlist.wtf
Descargas/ChromieCraft_3.3.5a/WTF/realmlist.wtf
```

### 10.7 Ubicación exacta de scripts de Python, configuración de IP y desarrollo

Para referencia rápida de la arquitectura y dónde se ubica cada elemento:

#### 1. Dónde están los scripts y códigos de Python para hacer modificaciones
- **`preyecro_docker/api/main.py`**: Servidor de la API REST. Contiene la lógica para procesar peticiones HTTP de cambio de nivel, oro, registro de cuentas y generación de NPCs (`POST /npc`).
- **`preyecro_docker/api/ejemplo_cliente.py`**: Cliente de línea de comandos en Python para interactuar con la API (consultar oro, subir nivel, ejecutar comandos GM, auditoría y spawnear NPCs con `npc`).
- **`preyecro_docker/api/crear_cuentas.py`**: Script en Python para dar de alta cuentas masivas leyendo desde `cuentas.json`.
- **`preyecro_docker/api/crear_npc.py`**: Script directo que calcula coordenadas del personaje e inserta el spawn en la base de datos `acore_world.creature`.
- **`preyecro_docker/ejemplo_estudiantes.py`**: Plantilla preparada para que los compañeros o el docente abran en VS Code (Windows/Linux) y prueben modificaciones con la librería `requests`.
- **`Documentos/mi_script.py`**: Script personal configurado y probado en el entorno local para modificar personajes y verificar auditoría.

#### 2. Dónde se configura la IP privada para que los demás se unan
- **En el cliente WoW del jugador (Windows o Linux):**
  - Archivo `Data/enUS/realmlist.wtf` (o la carpeta de idioma correspondiente como `esES`).
  - Archivo `WTF/realmlist.wtf`.
  - Configuración: `set realmlist TU_IP_TAILSCALE:3724`.
- **En las variables de entorno del servidor (Docker):**
  - Archivo `preyecro_docker/azerothcore-wotlk/.env` -> Variable `DOCKER_BIND_IP=TU_IP_TAILSCALE`.
- **En la API REST de Python:**
  - Archivo `preyecro_docker/api/.env` -> Variable `API_HOST=TU_IP_TAILSCALE`.
- **En la base de datos del servidor:**
  - Tabla `acore_auth.realmlist` -> Columna `address = 'TU_IP_TAILSCALE'`, `port = 8085`.

#### 3. En qué archivos crear código de Python para que funcione
Cualquier compañero en Windows o en Linux puede crear un archivo `.py` en **cualquier carpeta** de su equipo. Solo requiere tener instalada la librería `requests` (`pip install requests`) y definir:

```python
import requests

SERVER_URL = "http://TU_IP_TAILSCALE:8001"
HEADERS = {"X-API-Key": "CAMBIAR_API_KEY"}

# Ejemplo: cambiar nivel y oro
requests.patch(f"{SERVER_URL}/characters/Luis", json={"level": 80, "money_gold": 2500}, headers=HEADERS)

# Ejemplo: spawnear un NPC
requests.post(f"{SERVER_URL}/npc", json={"personaje": "Luis", "entry": 12345}, headers=HEADERS)
```

---

## 11. Siguientes pasos recomendados

1. **Compartir el enlace de Tailscale**: Enviar el enlace de máquina compartida al compañero o docente.
2. **Conexión de clientes Windows**: Que el compañero configure su `realmlist.wtf` con `TU_IP_TAILSCALE:3724` e inicie sesión con la cuenta `LUCI` creada por web.
3. **Pruebas de scripts en clase**: Que los alumnos ejecuten sus scripts de Python en VS Code apuntando a `http://TU_IP_TAILSCALE:8001`.
4. **Cambio de credenciales**: Reemplazar contraseñas de desarrollo por contraseñas seguras antes de la entrega final.
5. **Opcional**: Integrar módulo `mod-auctionsim`.

### 11.1 Restricción a Tailscale (Aplicada con éxito)

La restricción de seguridad ya fue aplicada y está activa en el sistema:
- `DOCKER_BIND_IP=TU_IP_TAILSCALE` configurado en `.env`.
- Los puertos `3724` y `8085` escuchan únicamente en `TU_IP_TAILSCALE`.
- Se verificó con `ss -ltnp` que ninguna interfaz externa ni `0.0.0.0` ni IPv6 expone los puertos del juego.

---

## 12. Seguridad antes de invitar

- Cambia `CAMBIAR_GM_PASSWORD` por una contraseña fuerte.
- Cambia `CAMBIAR_API_KEY`.
- Cambia `CAMBIAR_MYSQL_API_PASSWORD` si vas a compartir el proyecto.
- Si cambias la contraseña de `luis`, actualiza `SOAP_PASS` en `api/.env` y reinicia la API.
- No des la cuenta GM al amigo; crea una cuenta gmlevel 0.
- No compartas la API key con quien solo va a jugar.
- No actives Tailscale Funnel.
- Si invitas a varias personas, usa ACLs para permitir solo `3724` y `8085`.
- Antes de subir el proyecto a GitHub, quita las credenciales del `README.md` y de este informe.
- La contraseña de GitHub que se escribió en el chat debe cambiarse y conviene activar 2FA.
- Haz un respaldo antes de cada cambio importante:

```bash
cd /home/luis/preyecro_docker
./backup.sh
```

### 12.1 Cambiar la contraseña de la cuenta GM

Desde la consola del worldserver:

```bash
docker attach ac-worldserver
account set password luis NUEVA_CLAVE NUEVA_CLAVE
```

O por SOAP/API:

```bash
curl -X POST \
  -H "X-API-Key: CAMBIAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command":"account set password luis NUEVA_CLAVE NUEVA_CLAVE"}' \
  http://TU_IP_TAILSCALE:8001/gm
```

Después actualiza `SOAP_PASS` en `api/.env` y reinicia la API.

### 12.2 Cambiar la API key

1. Edita `api/.env`:

```env
API_KEY=NUEVA_CLAVE_API
```

2. Reinicia la API:

```bash
kill $(pgrep -f 'uvicorn main:app')
cd /home/luis/preyecro_docker
./start.sh
```

3. Actualiza el README y los scripts que usen la clave.

### 12.3 Cambiar la contraseña del usuario MySQL de la API

```sql
ALTER USER 'acore_api'@'%' IDENTIFIED BY 'NUEVA_CLAVE_DB';
FLUSH PRIVILEGES;
```

Luego actualiza `DB_PASSWORD` en `api/.env` y reinicia la API.

---

## 13. Apéndice: endpoints, puertos y consultas

### 13.1 Endpoints de la API

| Método | Ruta | Función | Requiere API key |
|---|---|---|---|
| GET | `/` | Información básica | No |
| GET | `/docs` | Swagger UI | No |
| GET | `/status` | Estado de contenedores y servidor | Sí |
| POST | `/restart/{service}` | Reinicia `worldserver` o `authserver` | Sí |
| POST | `/gm` | Ejecuta comando GM por SOAP | Sí |
| GET | `/accounts` | Lista cuentas | Sí |
| POST | `/accounts` | Crea cuenta | Sí |
| DELETE | `/accounts/{username}` | Elimina cuenta y personajes | Sí |
| GET | `/characters` | Lista personajes | Sí |
| PATCH | `/characters/{name}` | Cambia nivel y/o oro | Sí |
| POST | `/npc` | Spawnea un NPC en las coordenadas de un personaje | Sí |
| GET | `/registro` | Formulario HTML de auto-registro web | No |
| POST | `/registro` | Endpoint de registro web con código `CAMBIAR_CODIGO_REGISTRO` | No |
| GET | `/realmlist` | Consulta realmlist | Sí |
| PUT | `/realmlist` | Cambia IP/puerto del reino | Sí |
| POST | `/query` | Ejecuta un `SELECT` de solo lectura | Sí |
| GET | `/audit` | Historial de cambios | Sí |

### 13.2 Puertos

| Puerto | Servicio | Estado actual | Configuración |
|---|---|---|---|
| `3724` | Login (auth) | `TU_IP_TAILSCALE` | Restringido solo a Tailscale |
| `8085` | Mundo (world) | `TU_IP_TAILSCALE` | Restringido solo a Tailscale |
| `8001` | API REST / Web | `TU_IP_TAILSCALE` | Restringido solo a Tailscale (con API key) |
| `7878` | SOAP | `127.0.0.1` | Localhost (seguro) |
| `3307` | MySQL | `127.0.0.1` | Localhost (seguro) |

### 13.3 Tabla `realmlist`

Valores actuales esperados:

```
id: 1
name: AzerothCore
address: TU_IP_TAILSCALE
localAddress: 127.0.0.1
port: 8085
gamebuild: 12340
```

Si cambia la IP de Tailscale, actualiza `address` y reinicia el authserver.

### 13.4 Tabla `account_access`

La cuenta `luis` debe tener:

```
id: 1
gmlevel: 3
RealmID: -1
```

`RealmID = -1` significa que el nivel GM aplica a todos los reinos.

### 13.5 Auditoría

La tabla `acore_auth.admin_audit` guarda:

- Creación y eliminación de cuentas.
- Reinicios de servicios.
- Comandos GM.
- Cambios de personaje.
- Cambios de realmlist.
- Consultas.

Cada registro tiene `fecha`, `usuario`, `accion` y `detalle`.

---

**Fin del informe.**

