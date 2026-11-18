"""Excepciones de negocio del módulo restaurant (catálogo e inventario)."""


class InventoryError(Exception):
    """Error base del dominio de inventario."""


class ItemNoDisponible(InventoryError):
    pass


class InventarioNoEncontrado(InventoryError):
    pass
