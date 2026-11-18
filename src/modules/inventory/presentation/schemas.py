"""Esquemas Pydantic de la API del módulo inventory.

Los contratos de datos viven en `application/datos.py`; la capa de
presentación los reexporta para mantener una única fuente de verdad.
"""

from src.modules.inventory.application.datos import InventarioOut, ItemOut

__all__ = ["InventarioOut", "ItemOut"]
