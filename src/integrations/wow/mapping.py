# ============================================================================
# MÓDULO: integraciones/wow  |  CAPA: integración  |  ARCHIVO: mapping.py
# QUÉ HACE: Mapeos puros entre AzerothCore y el modelo de subastas.
# DETALLE: funciones: clase_nombre, rareza_nombre, cobre_a_oro, personaje_desde_fila, item_desde_fila, inventario_desd...
# ============================================================================
"""Mapeos puros entre AzerothCore y el modelo de subastas.

No tocan base de datos: reciben filas (dicts) y devuelven dicts listos para
el sincronizador. Así se pueden probar sin MySQL ni PostgreSQL.
"""

from decimal import Decimal
from typing import Any, Dict

COPPER_PER_GOLD = Decimal("10000")

CLASS_NAMES = {
    1: "Guerrero",
    2: "Paladín",
    3: "Cazador",
    4: "Pícaro",
    5: "Sacerdote",
    6: "Caballero de la Muerte",
    7: "Chamán",
    8: "Mago",
    9: "Brujo",
    11: "Druida",
}

RARITY_NAMES = {
    0: "comun",
    1: "comun",
    2: "poco_comun",
    3: "raro",
    4: "epico",
    5: "legendario",
}


def clase_nombre(class_id: int) -> str:
    return CLASS_NAMES.get(int(class_id), f"Clase {class_id}")


def rareza_nombre(quality: int) -> str:
    return RARITY_NAMES.get(int(quality), "comun")


def cobre_a_oro(copper: Any) -> Decimal:
    """Convierte cobre de WoW a oro con dos decimales."""
    return (Decimal(int(copper or 0)) / COPPER_PER_GOLD).quantize(
        Decimal("0.01")
    )


def personaje_desde_fila(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "wow_guid": int(row["guid"]),
        "wow_account_id": int(row["account"]),
        "cuenta": str(row["username"]),
        "nombre": str(row["name"]),
        "nivel": int(row["level"]),
        "clase": clase_nombre(row["class"]),
        "oro": cobre_a_oro(row["money"]),
    }


def item_desde_fila(row: Dict[str, Any]) -> Dict[str, Any]:
    entry = int(row["item_entry"])
    nombre = row.get("item_name") or f"Item {entry}"
    return {
        "wow_entry": entry,
        "nombre": str(nombre)[:100],
        "rareza": rareza_nombre(row.get("quality", 0)),
        "nivel_requerido": int(row.get("required_level") or 1),
        "precio_base": cobre_a_oro(row.get("buy_price", 0)),
    }


def inventario_desde_fila(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "wow_guid": int(row["character_guid"]),
        "wow_entry": int(row["item_entry"]),
        "cantidad": int(row.get("cantidad") or 0),
    }
