# ============================================================================
# MÓDULO: mail  |  CAPA: application  |  ARCHIVO: dtos.py
# QUÉ HACE: Contratos de datos (DTO) de salida del módulo mail.
# DETALLE: clases: CorreoOut
# ============================================================================
"""Contratos de datos (DTO) de salida del módulo mail."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CorreoOut(BaseModel):
    """Respuesta de la API para un correo del personaje."""

    model_config = ConfigDict(from_attributes=True)

    id_correo: int
    id_destinatario: int
    asunto: str
    id_item: Optional[int]
    cantidad: int
    oro: Decimal
    estado: str
    fecha: datetime
