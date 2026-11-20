# ============================================================================
# MÓDULO: inventory  |  CAPA: domain  |  ARCHIVO: models.py
# QUÉ HACE: Entidades del módulo inventory: catálogo de ítems e inventario.
# DETALLE: clases: Item, Inventario
# ============================================================================
"""Entidades del módulo inventory: catálogo de ítems e inventario.

Solo Python: no conoce SQLAlchemy, FastAPI ni PostgreSQL.

Modelo lógico 2.1:
  - ITEM (1) ──< (N) INVENTARIO >── (N) PERSONAJE
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Item:
    """Ítem del catálogo que puede subastarse o enviarse por correo."""

    nombre: str                               # nombre visible del ítem
    rareza: str = "comun"                     # comun, poco_comun, raro...
    nivel_requerido: int = 1                  # nivel mínimo para usarlo
    precio_base: Decimal = Decimal("0")       # precio de referencia
    id_item: Optional[int] = None             # PK asignada por PostgreSQL


@dataclass
class Inventario:
    """Relación N:M entre un personaje y un ítem, con su cantidad."""

    id_personaje: int                         # FK -> personaje.id_personaje
    id_item: int                              # FK -> item.id_item
    cantidad: int = 1                         # unidades disponibles
    id_inventario: Optional[int] = None       # PK asignada por PostgreSQL

    def __post_init__(self):
        """Valida la regla `cantidad > 0` del modelo 2.1."""
        if self.cantidad < 1:
            raise ValueError("La cantidad debe ser mayor o igual a 1.")
