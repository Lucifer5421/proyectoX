"""Excepciones de negocio del módulo inventory."""


class InventoryError(Exception):
    """Error base del dominio de inventario."""


class ItemNoDisponible(InventoryError):
    pass


class InventarioNoEncontrado(InventoryError):
    pass
