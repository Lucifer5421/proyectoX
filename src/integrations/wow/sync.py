"""Sincroniza datos reales de AzerothCore hacia el PostgreSQL de subastas.

Lee de MySQL (`acore_auth`, `acore_characters`, `acore_world`) y escribe
solamente en las tablas `jugador`, `personaje`, `item` e `inventario` de
proyectoX. **Nunca escribe en las bases `acore_*`.**

Uso:
    python -m src.integrations.wow.sync --dry-run
    python -m src.integrations.wow.sync
    python -m src.integrations.wow.sync --skip-gold
"""

import argparse
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.integrations.wow.config import database_url_for_sync, load_settings
from src.integrations.wow.mapping import (
    inventario_desde_fila,
    item_desde_fila,
    personaje_desde_fila,
)
from src.modules.auth.infrastructure.external_adapters import WowAuthAdapter
from src.modules.auth.infrastructure.models_db import (
    JugadorModel,
    PersonajeModel,
)
from src.modules.restaurant.infrastructure.external_adapters import (
    WowInventoryAdapter,
)
from src.modules.restaurant.infrastructure.models_db import (
    InventarioModel,
    ItemModel,
)


@dataclass
class SyncPlan:
    jugadores: List[Dict[str, Any]] = field(default_factory=list)
    personajes: List[Dict[str, Any]] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)
    inventarios: List[Dict[str, Any]] = field(default_factory=list)


def build_plan(characters, inventory) -> SyncPlan:
    """Construye el plan de sincronización a partir de filas de WoW."""
    plan = SyncPlan()

    for row in characters:
        personaje = personaje_desde_fila(row)
        plan.personajes.append(personaje)
        if not any(
            j["wow_account_id"] == personaje["wow_account_id"]
            for j in plan.jugadores
        ):
            cuenta = personaje["cuenta"]
            plan.jugadores.append(
                {
                    "wow_account_id": personaje["wow_account_id"],
                    "nombre": cuenta,
                    # Nombre del primer personaje de la cuenta: sirve para
                    # enganchar los jugadores de la demo (Luis, Aracely).
                    "personaje_nombre": personaje["nombre"],
                    "email": f"{cuenta.lower()}@wow.local",
                    "oro": Decimal("0"),
                }
            )

    for jugador in plan.jugadores:
        jugador["oro"] = sum(
            (
                p["oro"]
                for p in plan.personajes
                if p["wow_account_id"] == jugador["wow_account_id"]
            ),
            Decimal("0"),
        )

    for row in inventory:
        plan.inventarios.append(inventario_desde_fila(row))
        item = item_desde_fila(row)
        if not any(i["wow_entry"] == item["wow_entry"] for i in plan.items):
            plan.items.append(item)

    return plan


def _find_jugador(session, data):
    """Busca un jugador por cuenta WoW, nombre de cuenta o de personaje."""
    row = session.scalar(
        select(JugadorModel).where(
            JugadorModel.wow_account_id == data["wow_account_id"]
        )
    )
    if row is None:
        row = session.scalar(
            select(JugadorModel).where(JugadorModel.nombre == data["nombre"])
        )
    if row is None:
        row = session.scalar(
            select(JugadorModel).where(
                JugadorModel.nombre == data["personaje_nombre"]
            )
        )
    if row is None:
        row = session.scalar(
            select(JugadorModel).where(JugadorModel.email == data["email"])
        )
    return row


def _upsert_jugador(session, data):
    row = _find_jugador(session, data)
    if row is None:
        row = JugadorModel(
            nombre=data["nombre"],
            email=data["email"],
            wow_account_id=data["wow_account_id"],
        )
        session.add(row)
        session.flush()
        return row, "creado"

    row.wow_account_id = data["wow_account_id"]
    return row, "actualizado"


def _upsert_personaje(session, data, jugador, skip_gold: bool):
    row = session.scalar(
        select(PersonajeModel).where(
            PersonajeModel.wow_guid == data["wow_guid"]
        )
    )
    if row is None:
        row = session.scalar(
            select(PersonajeModel).where(
                PersonajeModel.nombre == data["nombre"]
            )
        )
    if row is None:
        row = PersonajeModel(
            id_jugador=jugador.id_jugador,
            nombre=data["nombre"],
            nivel=data["nivel"],
            clase=data["clase"],
            oro=data["oro"],
            wow_guid=data["wow_guid"],
        )
        session.add(row)
        session.flush()
        return row, "creado"

    row.id_jugador = jugador.id_jugador
    row.nivel = data["nivel"]
    row.clase = data["clase"]
    row.wow_guid = data["wow_guid"]
    if not skip_gold:
        row.oro = data["oro"]
    return row, "actualizado"


def _upsert_item(session, data):
    row = session.scalar(
        select(ItemModel).where(ItemModel.wow_entry == data["wow_entry"])
    )
    if row is None:
        row = ItemModel(**data)
        session.add(row)
        session.flush()
        return row, "creado"

    row.nombre = data["nombre"]
    row.rareza = data["rareza"]
    row.nivel_requerido = data["nivel_requerido"]
    row.precio_base = data["precio_base"]
    return row, "actualizado"


def _upsert_inventario(session, personaje, item, cantidad: int):
    row = session.scalar(
        select(InventarioModel).where(
            InventarioModel.id_personaje == personaje.id_personaje,
            InventarioModel.id_item == item.id_item,
        )
    )
    if row is None:
        row = InventarioModel(
            id_personaje=personaje.id_personaje,
            id_item=item.id_item,
            cantidad=cantidad,
        )
        session.add(row)
        return row, "creado"

    row.cantidad = cantidad
    return row, "actualizado"


def apply_plan(session, plan: SyncPlan, skip_gold: bool = False) -> Dict[str, Any]:
    """Aplica el plan en PostgreSQL y devuelve un resumen por tabla."""
    resumen = {
        "jugadores": {"creados": 0, "actualizados": 0},
        "personajes": {"creados": 0, "actualizados": 0},
        "items": {"creados": 0, "actualizados": 0},
        "inventarios": {"creados": 0, "actualizados": 0},
    }

    jugadores = {}
    for data in plan.jugadores:
        row, accion = _upsert_jugador(session, data)
        jugadores[data["wow_account_id"]] = row
        clave = "creados" if accion == "creado" else "actualizados"
        resumen["jugadores"][clave] += 1

    personajes = {}
    for data in plan.personajes:
        jugador = jugadores[data["wow_account_id"]]
        row, accion = _upsert_personaje(
            session, data, jugador, skip_gold
        )
        personajes[data["wow_guid"]] = row
        clave = "creados" if accion == "creado" else "actualizados"
        resumen["personajes"][clave] += 1

    items = {}
    for data in plan.items:
        row, accion = _upsert_item(session, data)
        items[data["wow_entry"]] = row
        clave = "creados" if accion == "creado" else "actualizados"
        resumen["items"][clave] += 1

    for data in plan.inventarios:
        personaje = personajes[data["wow_guid"]]
        item = items[data["wow_entry"]]
        _, accion = _upsert_inventario(
            session, personaje, item, data["cantidad"]
        )
        clave = "creados" if accion == "creado" else "actualizados"
        resumen["inventarios"][clave] += 1

    session.commit()
    return resumen


def print_plan(plan: SyncPlan) -> None:
    print(f"Jugadores: {len(plan.jugadores)}")
    for j in plan.jugadores:
        print(
            f"  - cuenta {j['wow_account_id']} ({j['nombre']}): "
            f"{j['oro']} oro"
        )
    print(f"Personajes: {len(plan.personajes)}")
    for p in plan.personajes:
        print(
            f"  - {p['nombre']} (guid {p['wow_guid']}, "
            f"nivel {p['nivel']}, {p['clase']}): {p['oro']} oro"
        )
    print(f"Items: {len(plan.items)}")
    for i in plan.items:
        print(f"  - [{i['wow_entry']}] {i['nombre']} ({i['rareza']})")
    print(f"Inventario: {len(plan.inventarios)} filas")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sincroniza personajes, ítems y oro de AzerothCore hacia "
            "proyectoX (solo lectura en WoW)."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el plan sin escribir en PostgreSQL.",
    )
    parser.add_argument(
        "--skip-gold",
        action="store_true",
        help="Sincroniza personajes/ítems pero conserva el oro de la demo.",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    if not settings.configured:
        raise SystemExit(
            "Falta WOW_DB_PASSWORD. Copia wow-server/api/.env.example a "
            "wow-server/api/.env y configura DB_PASSWORD, o exporta "
            "WOW_DB_PASSWORD."
        )

    auth_client = WowAuthAdapter(settings)
    inventory_client = WowInventoryAdapter(settings)
    print(f"Leyendo AzerothCore en {settings.host}:{settings.port} ...")
    characters = auth_client.fetch_characters()
    inventory = inventory_client.fetch_inventory()
    plan = build_plan(characters, inventory)
    print_plan(plan)

    if args.dry_run:
        print("\nDry-run: no se escribió nada.")
        return

    engine = create_engine(database_url_for_sync(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        resumen = apply_plan(session, plan, skip_gold=args.skip_gold)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("\nSincronización aplicada:")
    for tabla, valores in resumen.items():
        print(f"  {tabla}: {valores}")


if __name__ == "__main__":
    main()
