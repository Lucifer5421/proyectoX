#!/usr/bin/env python3
"""Cliente de ejemplo para la API de AzerothCore.

Uso:
    wow-server/api/venv/bin/python api/ejemplo_cliente.py
    wow-server/api/venv/bin/python api/ejemplo_cliente.py oro NombreDelPersonaje
    wow-server/api/venv/bin/python api/ejemplo_cliente.py subir NombreDelPersonaje 80 2000
    wow-server/api/venv/bin/python api/ejemplo_cliente.py auditoria
    wow-server/api/venv/bin/python api/ejemplo_cliente.py gm "server info"
"""

import argparse
import json
import os
import sys

import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001").rstrip("/")
API_KEY = os.getenv("API_KEY", "CAMBIAR_API_KEY")

HEADERS = {
    "X-API-Key": API_KEY,
    "X-Admin-User": "python",
}


def call(method: str, path: str, **kwargs):
    url = f"{API_URL}{path}"
    try:
        response = requests.request(
            method, url, headers=HEADERS, timeout=30, **kwargs
        )
    except requests.RequestException as exc:
        print(f"ERROR de conexion: {exc}")
        sys.exit(1)

    try:
        data = response.json()
    except ValueError:
        data = response.text

    if not response.ok:
        print(f"ERROR HTTP {response.status_code}: {data}")
        sys.exit(1)

    return data


def show(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def buscar_personaje(nombre: str):
    personajes = call("GET", "/characters")
    for personaje in personajes:
        if personaje["name"].lower() == nombre.lower():
            return personaje
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Cliente de ejemplo para la API de AzerothCore"
    )
    sub = parser.add_subparsers(dest="accion")

    sub.add_parser("estado", help="Estado del servidor")
    sub.add_parser("cuentas", help="Lista de cuentas")
    sub.add_parser("personajes", help="Lista de personajes")

    auditoria = sub.add_parser("auditoria", help="Ultimos registros de auditoria")
    auditoria.add_argument("--limit", type=int, default=10)

    oro = sub.add_parser("oro", help="Muestra el oro de un personaje")
    oro.add_argument("nombre")

    subir = sub.add_parser("subir", help="Cambia nivel y oro de un personaje")
    subir.add_argument("nombre")
    subir.add_argument("nivel", type=int)
    subir.add_argument("oro", type=float)

    gm = sub.add_parser("gm", help="Ejecuta un comando GM por SOAP")
    gm.add_argument("comando")

    npc = sub.add_parser("npc", help="Crea un NPC en la posicion de un personaje")
    npc.add_argument("personaje")
    npc.add_argument("entry", type=int)

    crear = sub.add_parser("crear", help="Crea una cuenta")
    crear.add_argument("usuario")
    crear.add_argument("clave")
    crear.add_argument("--gmlevel", type=int, default=0)

    args = parser.parse_args()

    if args.accion == "estado":
        show(call("GET", "/status"))

    elif args.accion == "cuentas":
        show(call("GET", "/accounts"))

    elif args.accion == "personajes":
        show(call("GET", "/characters"))

    elif args.accion == "auditoria":
        show(call("GET", f"/audit?limit={args.limit}"))

    elif args.accion == "oro":
        personaje = buscar_personaje(args.nombre)
        if not personaje:
            print(f"No existe el personaje {args.nombre}")
            sys.exit(1)
        print(
            f"{personaje['name']}: nivel {personaje['level']}, "
            f"{personaje['money_gold']:.2f} de oro "
            f"({personaje['money']} de cobre)"
        )

    elif args.accion == "subir":
        show(
            call(
                "PATCH",
                f"/characters/{args.nombre}",
                json={"level": args.nivel, "money_gold": args.oro},
            )
        )

    elif args.accion == "gm":
        show(call("POST", "/gm", json={"command": args.comando}))

    elif args.accion == "npc":
        show(
            call(
                "POST",
                "/npc",
                json={
                    "personaje": args.personaje,
                    "entry": args.entry,
                },
            )
        )

    elif args.accion == "crear":
        show(
            call(
                "POST",
                "/accounts",
                json={
                    "username": args.usuario,
                    "password": args.clave,
                    "gmlevel": args.gmlevel,
                },
            )
        )

    else:
        show(
            {
                "estado": call("GET", "/status"),
                "cuentas": call("GET", "/accounts"),
                "personajes": call("GET", "/characters"),
            }
        )


if __name__ == "__main__":
    main()
