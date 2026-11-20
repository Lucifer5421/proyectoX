"""Contratos de datos (DTO) de entrada y salida del módulo auction (subastas)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------
class PublicarSubastaIn(BaseModel):
    id_vendedor: int
    id_item: int
    precio_salida: Decimal = Field(gt=0)
    precio_compra_directa: Optional[Decimal] = Field(default=None, gt=0)
    duracion_horas: int = Field(default=24)
    cantidad: int = Field(default=1, ge=1)


class PujaIn(BaseModel):
    id_comprador: int
    monto: Decimal = Field(gt=0)


class CompraDirectaIn(BaseModel):
    id_comprador: int


class CancelarIn(BaseModel):
    id_vendedor: int


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------
class SubastaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_subasta: int
    id_vendedor: int
    id_item: int
    cantidad: int
    precio_salida: Decimal
    precio_compra_directa: Optional[Decimal]
    duracion_horas: int
    estado: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime]
    puja_actual: Decimal
    id_ganador_actual: Optional[int] = None
    tiempo_restante: Optional[int] = None


class PujaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_puja: int
    id_subasta: int
    id_comprador: int
    monto: Decimal
    estado: str
    fecha: datetime
