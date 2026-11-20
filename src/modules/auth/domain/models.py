# ============================================================================
# MÓDULO: auth  |  CAPA: domain  |  ARCHIVO: models.py
# QUÉ HACE: Entidades del módulo auth: jugador y personaje.
# DETALLE: clases: Jugador, Personaje
# ============================================================================
"""Entidades del módulo auth: jugador y personaje.

Solo Python: no conoce SQLAlchemy, FastAPI ni PostgreSQL.

Modelo lógico 2.1:
  - JUGADOR (1) ──< (N) PERSONAJE
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Jugador:
    """Cuenta de jugador. El oro vive en el personaje, no en la cuenta."""

    nombre: str                              # nombre visible de la cuenta
    email: str                               # correo único (UK en el DDL)
    fecha_registro: Optional[datetime] = None  # alta de la cuenta
    id_jugador: Optional[int] = None          # PK asignada por PostgreSQL


@dataclass
class Personaje:
    """Personaje de un jugador; es el vendedor/comprador de las subastas."""

    nombre: str                               # nombre único del personaje
    id_jugador: int                           # FK -> jugador.id_jugador
    nivel: int = 1                            # nivel del personaje
    clase: str = ""                           # clase de WoW (Pícaro, Mago...)
    oro: Decimal = Decimal("0")               # oro disponible para pujar
    id_personaje: Optional[int] = None        # PK asignada por PostgreSQL

    def __post_init__(self):
        """Valida las reglas del modelo 2.1 antes de persistir."""
        if self.nivel < 1:
            raise ValueError("El nivel debe ser mayor o igual a 1.")
        if self.oro < 0:
            raise ValueError("El oro no puede ser negativo.")
