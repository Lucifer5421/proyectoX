"""Entidades del módulo de autenticación y cuentas de jugador.

Solo Python: no conoce SQLAlchemy, FastAPI ni PostgreSQL.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Jugador:
    """Cuenta de jugador. El oro vive en el personaje, no en la cuenta."""

    nombre: str
    email: str
    fecha_registro: Optional[datetime] = None
    id_jugador: Optional[int] = None


@dataclass
class Personaje:
    """Personaje de un jugador; es el vendedor/comprador de las subastas."""

    nombre: str
    id_jugador: int
    nivel: int = 1
    clase: str = ""
    oro: Decimal = Decimal("0")
    id_personaje: Optional[int] = None

    def __post_init__(self):
        if self.nivel < 1:
            raise ValueError("El nivel debe ser mayor o igual a 1.")
        if self.oro < 0:
            raise ValueError("El oro no puede ser negativo.")
