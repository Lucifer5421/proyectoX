"""Contratos de datos (DTO) de salida del módulo restaurant (catálogo e inventario)."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_item: int
    nombre: str
    rareza: str
    nivel_requerido: int
    precio_base: Decimal


class InventarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_inventario: int
    id_personaje: int
    id_item: int
    cantidad: int
