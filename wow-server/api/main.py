"""
API REST de administracion para el servidor AzerothCore WoW.

Cubre los objetivos del proyecto:
  - Estado de los contenedores y del worldserver
  - Reinicio remoto de servicios
  - Comandos GM por SOAP
  - Gestion de cuentas (listar, crear, eliminar)
  - Modificacion de personajes (nivel y dinero)
  - Configuracion del realmlist (IP de Tailscale)
  - Consultas SQL de solo lectura
  - Auditoria de todos los cambios

Ejecutar:
  cd ~/preyecro_docker/api
  ./venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
"""

import html
import os
import re
from collections import defaultdict, deque
from datetime import datetime
from time import sleep, time
from typing import Optional
from xml.sax.saxutils import escape

import pymysql
import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "acore_api")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
SOAP_URL = os.getenv("SOAP_URL", "http://127.0.0.1:7878/")
SOAP_USER = os.getenv("SOAP_USER", "gm")
SOAP_PASS = os.getenv("SOAP_PASS", "")
DOCKER_SOCKET = os.getenv("DOCKER_SOCKET", "unix:///var/run/docker.sock")
API_KEY = os.getenv("API_KEY", "cambiar-esta-clave")

REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "1") == "1"
REGISTRATION_CODE = os.getenv("REGISTRATION_CODE", "CAMBIAR_CODIGO_REGISTRO")
REGISTRATION_MAX = int(os.getenv("REGISTRATION_MAX", "5"))
REGISTRATION_WINDOW = int(os.getenv("REGISTRATION_WINDOW", "3600"))
_REGISTROS_POR_IP = defaultdict(deque)

app = FastAPI(
    title="AzerothCore Admin API",
    description="Administracion remota del servidor WoW (AzerothCore + Docker + Tailscale)",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def db(database: str = "acore_auth"):
    """Conexion a MySQL dentro del contenedor ac-database."""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )


def verify_key(x_api_key: Optional[str] = Header(default=None)):
    """Protege la API con una clave en el header X-API-Key."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key invalida")


def audit(conn, accion: str, detalle: str, usuario: str = "api"):
    """Guarda un registro en acore_auth.admin_audit."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO acore_auth.admin_audit (usuario, accion, detalle) VALUES (%s, %s, %s)",
            (usuario, accion, detalle),
        )


def limitar_registro(ip: str) -> None:
    """Evita que una misma IP cree cuentas en masa."""
    ahora = time()
    cola = _REGISTROS_POR_IP[ip]
    while cola and ahora - cola[0] > REGISTRATION_WINDOW:
        cola.popleft()
    if len(cola) >= REGISTRATION_MAX:
        raise HTTPException(
            status_code=429,
            detail="Demasiados registros desde esta IP. Intenta mas tarde.",
        )
    cola.append(ahora)


def esperar_cuenta(username: str, intentos: int = 20, pausa: float = 0.2):
    """Espera a que el worldserver confirme la cuenta en la base de datos."""
    for _ in range(intentos):
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, username FROM acore_auth.account WHERE username = %s", (username,))
            row = cur.fetchone()
            if row:
                return row
        sleep(pausa)
    return None


def soap(command: str) -> str:
    """Ejecuta un comando en el worldserver por SOAP."""
    body = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ns1="urn:AC">'
        "<SOAP-ENV:Body><ns1:executeCommand>"
        f"<command>{escape(command)}</command>"
        "</ns1:executeCommand></SOAP-ENV:Body></SOAP-ENV:Envelope>"
    )
    try:
        r = requests.post(
            SOAP_URL,
            data=body.encode("utf-8"),
            auth=(SOAP_USER, SOAP_PASS),
            headers={"Content-Type": "text/xml; charset=utf-8"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo conectar a SOAP: {exc}") from exc

    if r.status_code == 401:
        raise HTTPException(status_code=502, detail="SOAP rechazo las credenciales GM")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"SOAP respondio HTTP {r.status_code}")

    match = re.search(r"<result>(.*?)</result>", r.text, re.S)
    return html.unescape(match.group(1)).strip() if match else r.text.strip()


def docker_client():
    import docker

    return docker.DockerClient(base_url=DOCKER_SOCKET, timeout=30)


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
class AccountIn(BaseModel):
    username: str = Field(min_length=3, max_length=16, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=16, pattern=r"^[A-Za-z0-9]+$")
    gmlevel: int = Field(default=0, ge=0, le=3)


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=16, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=16, pattern=r"^[A-Za-z0-9]+$")
    confirm: str = Field(min_length=6, max_length=16)
    code: str = Field(default="", max_length=64)


class CharacterPatch(BaseModel):
    level: Optional[int] = Field(default=None, ge=1, le=80)
    money_gold: Optional[int] = Field(default=None, ge=0, le=200000)


class GMCommand(BaseModel):
    command: str = Field(min_length=1, max_length=500)


class RealmIn(BaseModel):
    address: str = Field(min_length=7, max_length=64)
    port: int = Field(default=8085, ge=1, le=65535)


class QueryIn(BaseModel):
    database: str = Field(default="acore_characters", pattern=r"^acore_(auth|characters|world)$")
    sql: str = Field(min_length=6, max_length=2000)


class NPCIn(BaseModel):
    personaje: str = Field(min_length=2, max_length=12)
    entry: int = Field(ge=1)
    comment: Optional[str] = Field(default="Creado desde API Python", max_length=255)


REGISTRO_HTML = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crear cuenta - Servidor de WoW</title>
<style>
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #0b1020; color: #e8eefc; font-family: system-ui, Segoe UI, Roboto, sans-serif; }
.card { width: min(520px, 92vw); background: #141b31; border: 1px solid #2a365c; border-radius: 18px; padding: 28px; box-shadow: 0 20px 60px #0008; }
h1 { margin: 0 0 6px; font-size: 1.6rem; }
p { color: #aab7d6; line-height: 1.5; }
label { display: block; margin: 14px 0 6px; font-weight: 600; }
input { width: 100%; padding: 12px 14px; border-radius: 10px; border: 1px solid #33426e; background: #0e1529; color: #e8eefc; font-size: 1rem; }
input:focus { outline: 2px solid #4f7cff; border-color: transparent; }
button { width: 100%; margin-top: 18px; padding: 13px; border: 0; border-radius: 10px; background: #4f7cff; color: white; font-weight: 700; font-size: 1rem; cursor: pointer; }
button:disabled { opacity: .6; cursor: wait; }
.small { font-size: .85rem; color: #8f9cbd; }
.out { margin-top: 16px; padding: 12px; border-radius: 10px; white-space: pre-line; display: none; }
.out.ok { display: block; background: #0f2a1d; border: 1px solid #2f8f5b; color: #b9f5d0; }
.out.err { display: block; background: #2a1114; border: 1px solid #8f2f3b; color: #ffc2c9; }
code { background: #0e1529; padding: 2px 6px; border-radius: 6px; }
</style>
</head>
<body>
<main class="card">
<h1>Crear cuenta</h1>
<p>Servidor AzerothCore 3.3.5a de WoW. Crea tu cuenta y luego entra al juego a crear tu personaje.</p>
<form id="form">
<label for="username">Usuario</label>
<input id="username" name="username" autocomplete="username" required minlength="3" maxlength="16" pattern="[A-Za-z0-9_]+" placeholder="ej: alumno1">
<div class="small">3-16 letras, numeros o guion bajo.</div>
<label for="password">Contrasena</label>
<input id="password" name="password" type="password" autocomplete="new-password" required minlength="6" maxlength="16" pattern="[A-Za-z0-9]+" placeholder="6-16 letras o numeros">
<label for="confirm">Repetir contrasena</label>
<input id="confirm" name="confirm" type="password" autocomplete="new-password" required minlength="6" maxlength="16">
<label for="code">Codigo de la clase</label>
<input id="code" name="code" required placeholder="Pídelo al administrador">
<button id="btn" type="submit">Crear cuenta</button>
</form>
<div id="out" class="out"></div>
<p class="small">Realmlist: <code>TU_IP_TAILSCALE:3724</code><br>Necesitas Tailscale conectado y el cliente WoW 3.3.5a.</p>
</main>
<script>
const form = document.getElementById('form');
const out = document.getElementById('out');
const btn = document.getElementById('btn');
function detalle(d) {
  if (Array.isArray(d)) return d.map(x => x.msg || JSON.stringify(x)).join('; ');
  return d || 'Error desconocido';
}
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  out.className = 'out';
  out.textContent = '';
  btn.disabled = true;
  btn.textContent = 'Creando...';
  const datos = {
    username: document.getElementById('username').value.trim(),
    password: document.getElementById('password').value,
    confirm: document.getElementById('confirm').value,
    code: document.getElementById('code').value.trim()
  };
  try {
    const r = await fetch('/registro', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(datos)
    });
    const j = await r.json().catch(() => ({}));
    if (r.ok) {
      out.className = 'out ok';
      out.textContent = `Cuenta creada: ${j.username}\\n\\nAbre WoW 3.3.5a, realmlist ${j.realmlist}\\nEntra con tu usuario y contrasena, y crea tu personaje.`;
      form.reset();
    } else {
      out.className = 'out err';
      out.textContent = detalle(j.detail);
    }
  } catch (err) {
    out.className = 'out err';
    out.textContent = 'No se pudo conectar con el servidor: ' + err;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Crear cuenta';
  }
});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "servicio": "AzerothCore Admin API",
        "version": "1.0.0",
        "documentacion": "/docs",
        "registro": "/registro",
    }


@app.get("/registro", response_class=HTMLResponse)
def registro_form():
    if not REGISTRATION_ENABLED:
        raise HTTPException(status_code=404, detail="El registro esta desactivado")
    return HTMLResponse(REGISTRO_HTML)


@app.post("/registro")
def registro(payload: RegisterIn, request: Request):
    if not REGISTRATION_ENABLED:
        raise HTTPException(status_code=404, detail="El registro esta desactivado")

    ip = request.client.host if request.client else "desconocida"
    limitar_registro(ip)

    if payload.password != payload.confirm:
        raise HTTPException(status_code=400, detail="Las contrasenas no coinciden")

    if payload.code.strip().upper() != REGISTRATION_CODE.upper():
        raise HTTPException(status_code=403, detail="Codigo de clase incorrecto")

    username = payload.username.upper()

    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM acore_auth.account WHERE username = %s", (username,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Ese usuario ya existe. Prueba con otro.")

    try:
        soap(f"account create {username} {payload.password}")
    except HTTPException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo crear la cuenta: {exc.detail}",
        ) from exc

    if not esperar_cuenta(username):
        raise HTTPException(status_code=502, detail="El servidor no confirmo la creacion de la cuenta")

    with db() as conn:
        audit(conn, "registro", f"{username} ip={ip}", usuario="registro")

    return {
        "ok": True,
        "username": username,
        "realmlist": "TU_IP_TAILSCALE:3724",
        "mensaje": "Cuenta creada. Ya puedes entrar al juego.",
    }


@app.get("/status", dependencies=[Depends(verify_key)])
def status():
    contenedores = []
    try:
        client = docker_client()
        for c in client.containers.list(all=True):
            if not c.name.startswith("ac-"):
                continue
            contenedores.append(
                {
                    "nombre": c.name,
                    "estado": c.status,
                    "imagen": c.image.tags[0] if c.image.tags else c.image.short_id,
                }
            )
    except Exception as exc:  # noqa: BLE001
        contenedores = [{"error": f"No se pudo consultar Docker: {exc}"}]

    try:
        info = soap("server info")
    except HTTPException as exc:
        info = f"SOAP no disponible: {exc.detail}"

    return {
        "contenedores": contenedores,
        "worldserver": info,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }


@app.post("/restart/{service}", dependencies=[Depends(verify_key)])
def restart_service(service: str, usuario: str = Header(default="api", alias="X-Admin-User")):
    servicios = {
        "worldserver": "ac-worldserver",
        "authserver": "ac-authserver",
    }
    if service not in servicios:
        raise HTTPException(status_code=400, detail=f"Servicio no permitido. Usa: {list(servicios)}")

    try:
        client = docker_client()
        container = client.containers.get(servicios[service])
        container.restart(timeout=30)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"No se pudo reiniciar: {exc}") from exc

    with db() as conn:
        audit(conn, "restart", f"Reinicio de {service}", usuario)

    return {"ok": True, "servicio": service, "contenedor": servicios[service], "estado": "reiniciado"}


@app.post("/gm", dependencies=[Depends(verify_key)])
def gm_command(payload: GMCommand, usuario: str = Header(default="api", alias="X-Admin-User")):
    resultado = soap(payload.command)
    with db() as conn:
        audit(conn, "gm", payload.command, usuario)
    return {"comando": payload.command, "resultado": resultado}


@app.get("/accounts", dependencies=[Depends(verify_key)])
def list_accounts():
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.id, a.username, a.last_login, a.last_ip,
                   COALESCE(aa.gmlevel, 0) AS gmlevel,
                   (SELECT COUNT(*) FROM acore_characters.characters c WHERE c.account = a.id) AS personajes
            FROM acore_auth.account a
            LEFT JOIN acore_auth.account_access aa ON aa.id = a.id
            ORDER BY a.id
            """
        )
        return cur.fetchall()


@app.post("/accounts", dependencies=[Depends(verify_key)], status_code=201)
def create_account(payload: AccountIn, usuario: str = Header(default="api", alias="X-Admin-User")):
    username = payload.username.upper()

    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM acore_auth.account WHERE username = %s", (username,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail=f"La cuenta {username} ya existe")

    soap(f"account create {username} {payload.password}")
    if payload.gmlevel > 0:
        soap(f"account set gmlevel {username} {payload.gmlevel} -1")

    if not esperar_cuenta(username):
        raise HTTPException(status_code=502, detail="SOAP no confirmo la creacion de la cuenta")

    with db() as conn:
        audit(conn, "account_create", f"{username} gmlevel={payload.gmlevel}", usuario)

    return {"ok": True, "username": username, "gmlevel": payload.gmlevel}


@app.delete("/accounts/{username}", dependencies=[Depends(verify_key)])
def delete_account(username: str, usuario: str = Header(default="api", alias="X-Admin-User")):
    username = username.upper()
    if username == "LUIS":
        raise HTTPException(status_code=400, detail="No se puede eliminar la cuenta administradora principal")

    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM acore_auth.account WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"No existe la cuenta {username}")

        account_id = row["id"]
        cur.execute("DELETE FROM acore_characters.characters WHERE account = %s", (account_id,))
        personajes = cur.rowcount
        cur.execute("DELETE FROM acore_auth.account_access WHERE id = %s", (account_id,))
        cur.execute("DELETE FROM acore_auth.account WHERE id = %s", (account_id,))
        audit(conn, "account_delete", f"{username} (id={account_id}, personajes={personajes})", usuario)

    return {"ok": True, "username": username, "personajes_eliminados": personajes}


@app.get("/characters", dependencies=[Depends(verify_key)])
def list_characters():
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT guid, account, name, level, money,
                   ROUND(money / 10000, 2) AS money_gold,
                   online, race, class, gender
            FROM acore_characters.characters
            ORDER BY guid
            """
        )
        return cur.fetchall()


@app.patch("/characters/{name}", dependencies=[Depends(verify_key)])
def patch_character(
    name: str,
    payload: CharacterPatch,
    usuario: str = Header(default="api", alias="X-Admin-User"),
):
    if payload.level is None and payload.money_gold is None:
        raise HTTPException(status_code=400, detail="Indica level y/o money_gold")

    campos = []
    valores = []
    if payload.level is not None:
        campos.append("level = %s")
        valores.append(payload.level)
    if payload.money_gold is not None:
        campos.append("money = %s")
        valores.append(payload.money_gold * 10000)

    with db("acore_characters") as conn, conn.cursor() as cur:
        cur.execute("SELECT guid, name, level, money, online FROM acore_characters.characters WHERE name = %s", (name,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"No existe el personaje {name}")

        valores.append(name)
        cur.execute(f"UPDATE acore_characters.characters SET {', '.join(campos)} WHERE name = %s", valores)

        cur.execute("SELECT guid, name, level, money, ROUND(money / 10000, 2) AS money_gold, online FROM acore_characters.characters WHERE name = %s", (name,))
        actualizado = cur.fetchone()
        audit(conn, "character_patch", f"{name}: level={payload.level} money_gold={payload.money_gold}", usuario)

    return {"ok": True, "personaje": actualizado, "nota": "Si el personaje esta en linea, los cambios se aplican al guardar/desconectar."}


@app.post("/npc", dependencies=[Depends(verify_key)])
def create_npc(payload: NPCIn, usuario: str = Header(default="api", alias="X-Admin-User")):
    with db("acore_characters") as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT guid, name, map, position_x, position_y, position_z, orientation
            FROM acore_characters.characters
            WHERE LOWER(name) = LOWER(%s)
            """,
            (payload.personaje,),
        )
        personaje = cur.fetchone()
        if not personaje:
            raise HTTPException(status_code=404, detail=f"No existe el personaje {payload.personaje}")

    with db("acore_world") as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT entry, name FROM acore_world.creature_template WHERE entry = %s",
            (payload.entry,),
        )
        plantilla = cur.fetchone()
        if not plantilla:
            raise HTTPException(status_code=404, detail=f"No existe el NPC con entry {payload.entry}")

        cur.execute(
            """
            INSERT INTO acore_world.creature
                (id, map, position_x, position_y, position_z, orientation,
                 spawntimesecs, wander_distance, MovementType, Comment)
            VALUES
                (%s, %s, %s, %s, %s, %s, 120, 0, 0, %s)
            """,
            (
                payload.entry,
                personaje["map"],
                personaje["position_x"],
                personaje["position_y"],
                personaje["position_z"],
                personaje["orientation"],
                payload.comment,
            ),
        )
        guid = cur.lastrowid

    try:
        soap_res = soap(f".npc load {guid}")
    except Exception as exc:
        with db("acore_world") as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM acore_world.creature WHERE guid = %s", (guid,))
        raise HTTPException(status_code=502, detail=f"Error cargando NPC por SOAP: {exc}")

    with db("acore_auth") as conn:
        audit(conn, "npc_create", f"{plantilla['name']} entry={payload.entry} guid={guid} personaje={personaje['name']}", usuario)

    return {
        "ok": True,
        "guid": guid,
        "entry": payload.entry,
        "npc": plantilla["name"],
        "personaje": personaje["name"],
        "posicion": {
            "map": personaje["map"],
            "x": round(personaje["position_x"], 2),
            "y": round(personaje["position_y"], 2),
            "z": round(personaje["position_z"], 2)
        }
    }


@app.get("/realmlist", dependencies=[Depends(verify_key)])
def get_realmlist():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name, address, localAddress, port, gamebuild FROM acore_auth.realmlist")
        return cur.fetchall()


@app.put("/realmlist", dependencies=[Depends(verify_key)])
def set_realmlist(payload: RealmIn, usuario: str = Header(default="api", alias="X-Admin-User")):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE acore_auth.realmlist SET address = %s, localAddress = %s, port = %s WHERE id = 1",
            (payload.address, "127.0.0.1", payload.port),
        )
        audit(conn, "realmlist", f"{payload.address}:{payload.port}", usuario)
        cur.execute("SELECT id, name, address, localAddress, port FROM acore_auth.realmlist WHERE id = 1")
        return cur.fetchone()


@app.post("/query", dependencies=[Depends(verify_key)])
def run_query(payload: QueryIn, usuario: str = Header(default="api", alias="X-Admin-User")):
    sql = payload.sql.strip()
    if not sql.lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Solo se permiten consultas SELECT")
    if ";" in sql.rstrip(";"):
        raise HTTPException(status_code=400, detail="Solo se permite una sentencia")

    with db(payload.database) as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
        audit(conn, "query", f"{payload.database}: {sql[:200]}", usuario)
        return {"database": payload.database, "filas": len(rows), "resultado": rows}


@app.get("/audit", dependencies=[Depends(verify_key)])
def get_audit(limit: int = 100):
    limit = max(1, min(limit, 500))
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, fecha, usuario, accion, detalle FROM acore_auth.admin_audit ORDER BY id DESC LIMIT %s",
            (limit,),
        )
        return cur.fetchall()
