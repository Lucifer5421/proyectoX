#!/usr/bin/env python3
"""Crea un NPC en la posición actual de un personaje.

El comando .npc add del juego no se puede ejecutar por SOAP porque necesita
una sesión de jugador. Este script hace lo mismo por base de datos:

1. Lee la posición del personaje.
2. Inserta el spawn en acore_world.creature.
3. Ejecuta .npc load <guid> por SOAP para cargarlo en el mundo.

Uso:
    wow-server/api/venv/bin/python api/crear_npc.py --personaje NombreDelPersonaje --entry 12345
    wow-server/api/venv/bin/python api/crear_npc.py --personaje NombreDelPersonaje --entry 12345 --dry-run
"""

import argparse
import os
import re
import sys
from xml.sax.saxutils import escape

import pymysql
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "acore_api")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

SOAP_URL = os.getenv("SOAP_URL", "http://127.0.0.1:7878/")
SOAP_USER = os.getenv("SOAP_USER", "gm")
SOAP_PASS = os.getenv("SOAP_PASS", "")


def soap(command: str):
    """Ejecuta un comando por SOAP y devuelve (status, texto)."""
    body = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ns1="urn:AC">'
        "<SOAP-ENV:Body><ns1:executeCommand>"
        f"<command>{escape(command)}</command>"
        "</ns1:executeCommand></SOAP-ENV:Body></SOAP-ENV:Envelope>"
    )
    respuesta = requests.post(
        SOAP_URL,
        data=body.encode("utf-8"),
        auth=(SOAP_USER, SOAP_PASS),
        headers={"Content-Type": "text/xml; charset=utf-8"},
        timeout=20,
    )
    return respuesta.status_code, respuesta.text


def texto_soap(texto: str) -> str:
    resultado = re.search(r"<result>(.*?)</result>", texto, re.S)
    if resultado:
        return resultado.group(1).strip()
    fallo = re.search(r"<faultstring>(.*?)</faultstring>", texto, re.S)
    if fallo:
        return fallo.group(1).strip()
    return texto.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Crea un NPC en la posición de un personaje"
    )
    parser.add_argument("--personaje", "-p", required=True, help="Nombre del personaje")
    parser.add_argument("--entry", "-e", required=True, type=int, help="ID de creature_template")
    parser.add_argument(
        "--comment",
        default="Creado desde Python",
        help="Comentario que se guarda en la tabla creature",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra lo que haria sin insertar nada",
    )
    args = parser.parse_args()

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="acore_world",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    except pymysql.MySQLError as exc:
        print(f"No se pudo conectar a MySQL: {exc}")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT guid, name, map, position_x, position_y, position_z, orientation
                FROM acore_characters.characters
                WHERE LOWER(name) = LOWER(%s)
                """,
                (args.personaje,),
            )
            personaje = cur.fetchone()
            if not personaje:
                print(f"No existe el personaje {args.personaje}")
                sys.exit(1)

            cur.execute(
                "SELECT entry, name FROM acore_world.creature_template WHERE entry = %s",
                (args.entry,),
            )
            plantilla = cur.fetchone()
            if not plantilla:
                print(f"No existe la entrada {args.entry} en creature_template")
                sys.exit(1)

            print(
                f"Personaje: {personaje['name']} "
                f"(map {personaje['map']}, "
                f"x={personaje['position_x']:.2f}, "
                f"y={personaje['position_y']:.2f}, "
                f"z={personaje['position_z']:.2f})"
            )
            print(f"NPC: {plantilla['name']} (entry {plantilla['entry']})")

            if args.dry_run:
                print("dry-run: no se inserto nada.")
                return

            cur.execute(
                """
                INSERT INTO acore_world.creature
                    (id, map, position_x, position_y, position_z, orientation,
                     spawntimesecs, wander_distance, MovementType, Comment)
                VALUES
                    (%s, %s, %s, %s, %s, %s, 120, 0, 0, %s)
                """,
                (
                    args.entry,
                    personaje["map"],
                    personaje["position_x"],
                    personaje["position_y"],
                    personaje["position_z"],
                    personaje["orientation"],
                    args.comment,
                ),
            )
            guid = cur.lastrowid
            conn.commit()

        status, texto = soap(f".npc load {guid}")
        detalle = texto_soap(texto)

        if status == 200:
            print(f"NPC cargado correctamente. GUID: {guid}")
        elif status == 500 and "already loaded" in detalle.lower():
            print(f"El NPC ya estaba cargado. GUID: {guid}")
        else:
            print(f"Error al cargar el NPC (HTTP {status}): {detalle}")
            with conn.cursor() as cur:
                cur.execute("DELETE FROM acore_world.creature WHERE guid = %s", (guid,))
            conn.commit()
            print("Se elimino el spawn de la base para no dejar basura.")
            sys.exit(1)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO acore_auth.admin_audit (usuario, accion, detalle)
                VALUES (%s, %s, %s)
                """,
                (
                    "python",
                    "npc_create",
                    f"{plantilla['name']} entry={args.entry} guid={guid} "
                    f"personaje={personaje['name']}",
                ),
            )
            conn.commit()

        print(f"Para borrarlo en el juego: selecciona el NPC y usa .npc delete {guid}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
