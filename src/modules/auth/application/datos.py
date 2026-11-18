"""Contratos de datos (DTO) de salida del módulo auth."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class JugadorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_jugador: int
    nombre: str
    email: str
    fecha_registro: Optional[datetime]


class PersonajeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_personaje: int
    id_jugador: int
    nombre: str
    nivel: int
    clase: str
    oro: Decimal
