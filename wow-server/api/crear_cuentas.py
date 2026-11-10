#!/usr/bin/env python3
"""Crea cuentas en lote para el servidor AzerothCore.

El archivo de entrada es un JSON con una lista de cuentas:

[
  {"username": "profesor", "password": "Profe2026", "gmlevel": 3},
  {"username": "alumno1",  "password": "auto",      "gmlevel": 0}
]

Uso:
    wow-server/api/venv/bin/python api/crear_cuentas.py
    wow-server/api/venv/bin/python api/crear_cuentas.py --file api/cuentas.json
    wow-server/api/venv/bin/python api/crear_cuentas.py --dry-run
"""

import argparse
import json
import os
import re
import secrets
import string
import sys

import requests

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001").rstrip("/")
API_KEY = os.getenv("API_KEY", "CAMBIAR_API_KEY")

HEADERS = {
    "X-API-Key": API_KEY,
    "X-Admin-User": "python",
}

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
PASSWORD_RE = re.compile(r"^[A-Za-z0-9]{6,16}$")


def generar_password(longitud: int = 10) -> str:
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(longitud))


def main():
    parser = argparse.ArgumentParser(
        description="Crea cuentas de juego desde un archivo JSON"
    )
    parser.add_argument(
        "--file",
        default=os.getenv(
            "CUENTAS_FILE",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuentas.json"),
        ),
        help="Ruta del JSON con las cuentas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra lo que haria sin crear nada",
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"No existe el archivo: {args.file}")
        print("Copia el ejemplo y edítalo:")
        print("  cp api/cuentas.ejemplo.json api/cuentas.json")
        print("  nano api/cuentas.json")
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as archivo:
        cuentas = json.load(archivo)

    if not isinstance(cuentas, list):
        print("El JSON debe ser una lista de objetos.")
        sys.exit(1)

    resultados = []

    for numero, item in enumerate(cuentas, start=1):
        username = str(item.get("username", "")).strip()
        password = str(item.get("password", "")).strip()
        gmlevel = int(item.get("gmlevel", 0))

        if password.lower() in ("auto", ""):
            password = generar_password()

        if not USERNAME_RE.fullmatch(username):
            print(f"[{numero}] Usuario invalido: {username!r} (3-16 letras/numeros/_)")
            resultados.append((username, "-", gmlevel, "usuario invalido"))
            continue

        if not PASSWORD_RE.fullmatch(password):
            print(f"[{numero}] Clave invalida para {username}: debe ser 6-16 alfanumerica")
            resultados.append((username, password, gmlevel, "clave invalida"))
            continue

        if args.dry_run:
            print(f"[dry-run] {username} / {password} / gmlevel={gmlevel}")
            resultados.append((username, password, gmlevel, "dry-run"))
            continue

        try:
            respuesta = requests.post(
                f"{API_URL}/accounts",
                headers=HEADERS,
                json={
                    "username": username,
                    "password": password,
                    "gmlevel": gmlevel,
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            print(f"[{numero}] Error de conexion con la API: {exc}")
            resultados.append((username, password, gmlevel, "sin conexion"))
            continue

        if respuesta.status_code == 201:
            estado = "creada"
            print(f"[{numero}] Cuenta creada: {username} (gmlevel={gmlevel})")
        elif respuesta.status_code == 409:
            estado = "ya existia"
            print(f"[{numero}] La cuenta {username} ya existia; no se cambio.")
        else:
            estado = f"error {respuesta.status_code}"
            try:
                detalle = respuesta.json().get("detail", respuesta.text)
            except ValueError:
                detalle = respuesta.text
            print(f"[{numero}] Error creando {username}: {detalle}")

        resultados.append((username, password, gmlevel, estado))

    if not args.dry_run:
        print("\nResumen de cuentas:")
        print(f"{'Usuario':<16} {'Clave':<16} {'GM':<4} Estado")
        print("-" * 60)
        for username, password, gmlevel, estado in resultados:
            print(f"{username:<16} {password:<16} {gmlevel:<4} {estado}")


if __name__ == "__main__":
    main()
