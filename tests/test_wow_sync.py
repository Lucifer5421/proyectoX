"""Pruebas puras del mapeo y plan de sincronización con AzerothCore.

No requieren MySQL ni PostgreSQL: usan filas de ejemplo con la misma forma
que devuelve `WowClient`.
"""

from decimal import Decimal

from src.integrations.wow.mapping import (
    clase_nombre,
    cobre_a_oro,
    inventario_desde_fila,
    item_desde_fila,
    rareza_nombre,
)
from src.integrations.wow.sync import build_plan

CHARACTERS = [
    {
        "guid": 1,
        "account": 1,
        "name": "Luis",
        "level": 80,
        "class": 4,
        "money": 20_000_000,
        "username": "LUIS",
    },
    {
        "guid": 2,
        "account": 6,
        "name": "Luci",
        "level": 1,
        "class": 7,
        "money": 0,
        "username": "LUCI",
    },
    {
        "guid": 3,
        "account": 7,
        "name": "Aracely",
        "level": 1,
        "class": 8,
        "money": 0,
        "username": "AC878522",
    },
]

INVENTORY = [
    {
        "character_guid": 1,
        "item_entry": 49,
        "cantidad": 1,
        "item_name": "Footpad's Shirt",
        "quality": 1,
        "required_level": 1,
        "buy_price": 1,
    },
    {
        "character_guid": 1,
        "item_entry": 2092,
        "cantidad": 1,
        "item_name": "Worn Dagger",
        "quality": 1,
        "required_level": 2,
        "buy_price": 36,
    },
    {
        "character_guid": 1,
        "item_entry": 6948,
        "cantidad": 1,
        "item_name": "Hearthstone",
        "quality": 1,
        "required_level": 1,
        "buy_price": 0,
    },
    {
        "character_guid": 2,
        "item_entry": 154,
        "cantidad": 1,
        "item_name": "Primitive Mantle",
        "quality": 1,
        "required_level": 1,
        "buy_price": 1,
    },
    {
        "character_guid": 2,
        "item_entry": 6948,
        "cantidad": 1,
        "item_name": "Hearthstone",
        "quality": 1,
        "required_level": 1,
        "buy_price": 0,
    },
    {
        "character_guid": 3,
        "item_entry": 20893,
        "cantidad": 1,
        "item_name": "Apprentice's Robe",
        "quality": 0,
        "required_level": 1,
        "buy_price": 5,
    },
    {
        "character_guid": 3,
        "item_entry": 6948,
        "cantidad": 1,
        "item_name": "Hearthstone",
        "quality": 1,
        "required_level": 1,
        "buy_price": 0,
    },
]


def test_clase_nombre():
    assert clase_nombre(4) == "Pícaro"
    assert clase_nombre(8) == "Mago"
    assert clase_nombre(99) == "Clase 99"


def test_rareza_nombre():
    assert rareza_nombre(0) == "comun"
    assert rareza_nombre(2) == "poco_comun"
    assert rareza_nombre(3) == "raro"
    assert rareza_nombre(5) == "legendario"
    assert rareza_nombre(99) == "comun"


def test_cobre_a_oro():
    assert cobre_a_oro(20_000_000) == Decimal("2000.00")
    assert cobre_a_oro(0) == Decimal("0.00")
    assert cobre_a_oro(None) == Decimal("0.00")


def test_item_desde_fila_trunca_nombre_largo():
    item = item_desde_fila(
        {
            "item_entry": 123,
            "item_name": "x" * 300,
            "quality": 3,
            "required_level": 10,
            "buy_price": 10_000,
        }
    )
    assert len(item["nombre"]) == 100
    assert item["rareza"] == "raro"
    assert item["precio_base"] == Decimal("1.00")


def test_inventario_desde_fila():
    inv = inventario_desde_fila(
        {"character_guid": 1, "item_entry": 49, "cantidad": 3}
    )
    assert inv == {"wow_guid": 1, "wow_entry": 49, "cantidad": 3}


def test_build_plan_cuentas_personajes_items_e_inventario():
    plan = build_plan(CHARACTERS, INVENTORY)

    assert len(plan.jugadores) == 3
    assert len(plan.personajes) == 3
    # 6948 (Hearthstone) se repite en las 3 cuentas: se deduplica.
    assert len(plan.items) == 5
    assert len(plan.inventarios) == 7

    luis = next(p for p in plan.personajes if p["nombre"] == "Luis")
    assert luis["wow_guid"] == 1
    assert luis["clase"] == "Pícaro"
    assert luis["oro"] == Decimal("2000.00")

    jugador_luis = next(
        j for j in plan.jugadores if j["wow_account_id"] == 1
    )
    assert jugador_luis["nombre"] == "LUIS"
    assert jugador_luis["oro"] == Decimal("2000.00")

    hearthstone = next(i for i in plan.items if i["wow_entry"] == 6948)
    assert hearthstone["nombre"] == "Hearthstone"
