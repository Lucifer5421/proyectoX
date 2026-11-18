"""Entidades del módulo de inventarios.

Solo Python: no conoce SQLAlchemy, FastAPI ni PostgreSQL.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Item:
    nombre: str
    rareza: str = "comun"
    nivel_requerido: int = 1
    precio_base: Decimal = Decimal("0")
    id_item: Optional[int] = None


@dataclass
class Inventario:
    id_personaje: int
    id_item: int
    cantidad: int = 1
    id_inventario: Optional[int] = None

    def __post_init__(self):
        if self.cantidad < 1:
            raise ValueError("La cantidad debe ser mayor o igual a 1.")
