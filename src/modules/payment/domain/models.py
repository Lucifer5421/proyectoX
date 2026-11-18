"""Entidades de depósitos, comisiones, transacciones y correo.

Solo Python: no conoce SQLAlchemy, FastAPI ni PostgreSQL.
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
    PUJA_GANADORA = "puja_ganadora"
    COMPRA_DIRECTA = "compra_directa"


class EstadoCorreo(str, Enum):
    PENDIENTE = "pendiente"
    LEIDO = "leido"
    COBRADO = "cobrado"
    DEVUELTO = "devuelto"


@dataclass
class Deposito:
    id_subasta: int
    monto: Decimal
    pagado: bool = False
    fecha: datetime = field(default_factory=_utcnow)
    id_deposito: Optional[int] = None


@dataclass
class Comision:
    id_subasta: int
    porcentaje: Decimal
    monto: Decimal
    fecha: datetime = field(default_factory=_utcnow)
    id_comision: Optional[int] = None


@dataclass
class Transaccion:
    id_subasta: int
    id_comprador: int
    monto: Decimal
    tipo: TipoTransaccion
    fecha: datetime = field(default_factory=_utcnow)
    id_transaccion: Optional[int] = None


@dataclass
class Correo:
    id_destinatario: int
    asunto: str
    id_item: Optional[int] = None
    cantidad: int = 0
    oro: Decimal = Decimal("0")
    estado: EstadoCorreo = EstadoCorreo.PENDIENTE
    fecha: datetime = field(default_factory=_utcnow)
    id_correo: Optional[int] = None
