# ============================================================================
# MÓDULO: inventory  |  CAPA: domain  |  ARCHIVO: exceptions.py
# QUÉ HACE: Excepciones de negocio del módulo inventory (catálogo e inventario).
# DETALLE: clases: InventoryError, ItemNoDisponible, InventarioNoEncontrado
# ============================================================================
"""Excepciones de negocio del módulo inventory (catálogo e inventario)."""


class InventoryError(Exception):
    """Error base del dominio de inventario."""


class ItemNoDisponible(InventoryError):
    pass


class InventarioNoEncontrado(InventoryError):
    pass
