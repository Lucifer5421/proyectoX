# ============================================================================
# MÓDULO: mail  |  CAPA: domain  |  ARCHIVO: models.py
# QUÉ HACE: Entidades del módulo mail: correo del personaje.
# DETALLE: clases: EstadoCorreo, Correo
# ============================================================================
"""Entidades del módulo mail: correo del personaje.

Solo Python: no conoce SQLAlchemy, FastAPI ni PostgreSQL.

Modelo lógico 2.1:
  - PERSONAJE (1) ──< (N) CORREO  (id_destinatario)
  - ITEM (1) ──< (N) CORREO       (id_item opcional)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


def _utcnow() -> datetime:
    """UTC sin zona horaria, compatible con TIMESTAMP de PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EstadoCorreo(str, Enum):
    """Estados permitidos por el modelo 2.1 para `correo.estado`."""

    PENDIENTE = "pendiente"
    LEIDO = "leido"
    COBRADO = "cobrado"
    DEVUELTO = "devuelto"


@dataclass
class Correo:
    """Entrega de un ítem u oro al destinatario de una subasta.

    El correo es el mecanismo con el que la casa de subastas entrega el
    ítem al ganador o devuelve el ítem al vendedor cuando la subasta
    expira. `id_item` es opcional porque un correo puede contener solo oro.
    """

    id_destinatario: int
    asunto: str
    id_item: Optional[int] = None
    cantidad: int = 0
    oro: Decimal = Decimal("0")
    estado: EstadoCorreo = EstadoCorreo.PENDIENTE
    fecha: datetime = field(default_factory=_utcnow)
    id_correo: Optional[int] = None

    def __post_init__(self):
        """Valida las reglas del modelo antes de persistir el correo."""
        if not self.asunto or not self.asunto.strip():
            raise ValueError("El asunto del correo es obligatorio.")
        if self.cantidad < 0:
            raise ValueError("La cantidad del correo no puede ser negativa.")
        if self.oro < 0:
            raise ValueError("El oro del correo no puede ser negativo.")
