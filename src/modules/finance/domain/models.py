"""Entidades del módulo finance: depósito, comisión y transacción.

Solo Python: no conoce SQLAlchemy, FastAPI ni PostgreSQL.

Modelo lógico 2.1:
  - SUBASTA (1) ── (1) DEPOSITO
  - SUBASTA (1) ── (1) COMISION
  - SUBASTA (1) ── (1) TRANSACCION
  - PERSONAJE (1) ──< (N) TRANSACCION (comprador)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


def _utcnow() -> datetime:
    """UTC sin zona horaria, compatible con TIMESTAMP de PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TipoTransaccion(str, Enum):
    """Tipos permitidos por el modelo 2.1 para `transaccion.tipo`."""

    PUJA_GANADORA = "puja_ganadora"
    COMPRA_DIRECTA = "compra_directa"


@dataclass
class Deposito:
    """Garantía que paga el vendedor al publicar una subasta.

    El modelo 2.1 lo relaciona 1:1 con `subasta`.
    """

    id_subasta: int
    monto: Decimal
    pagado: bool = False
    fecha: datetime = field(default_factory=_utcnow)
    id_deposito: Optional[int] = None

    def __post_init__(self):
        if self.monto < 0:
            raise ValueError("El monto del depósito no puede ser negativo.")


@dataclass
class Comision:
    """Comisión que cobra la casa de subastas al cerrar la venta.

    El modelo 2.1 lo relaciona 1:1 con `subasta`.
    """

    id_subasta: int
    porcentaje: Decimal
    monto: Decimal
    fecha: datetime = field(default_factory=_utcnow)
    id_comision: Optional[int] = None

    def __post_init__(self):
        if self.porcentaje < 0 or self.porcentaje > 100:
            raise ValueError("El porcentaje debe estar entre 0 y 100.")
        if self.monto < 0:
            raise ValueError("El monto de la comisión no puede ser negativo.")


@dataclass
class Transaccion:
    """Registro económico del cierre de una subasta.

    El modelo 2.1 lo relaciona 1:1 con `subasta` y N:1 con el personaje
    comprador.
    """

    id_subasta: int
    id_comprador: int
    monto: Decimal
    tipo: TipoTransaccion
    fecha: datetime = field(default_factory=_utcnow)
    id_transaccion: Optional[int] = None

    def __post_init__(self):
        if self.monto < 0:
            raise ValueError("El monto de la transacción no puede ser negativo.")
