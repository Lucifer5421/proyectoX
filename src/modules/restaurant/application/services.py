"""Casos de uso del módulo restaurant (catálogo e inventario).

Gestiona el catálogo de ítems y la relación N:M personaje-ítem.
"""

from typing import List

from sqlalchemy.orm import Session

from src.modules.restaurant.domain.exceptions import ItemNoDisponible
from src.modules.restaurant.domain.models import Inventario, Item
from src.modules.restaurant.infrastructure.repository_impl import (
    InventarioRepositoryImpl,
    ItemRepositoryImpl,
)


class InventoryService:
    def __init__(self, session: Session):
        self.session = session
        self.items = ItemRepositoryImpl(session)
        self.inventarios = InventarioRepositoryImpl(session)

    # ------------------------------------------------------------------
    # Catálogo
    # ------------------------------------------------------------------
    def obtener_item(self, id_item: int) -> Item:
        item = self.items.obtener(id_item)
        if not item:
            raise ItemNoDisponible(f"El item {id_item} no existe.")
        return item

    def listar_items(self) -> List[Item]:
        return self.items.listar()

    # ------------------------------------------------------------------
    # Inventario
    # ------------------------------------------------------------------
    def listar_inventario(self, id_personaje: int) -> List[Inventario]:
        return self.inventarios.listar_por_personaje(id_personaje)

    def tiene_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> bool:
        return self.inventarios.tiene_item(
            id_personaje, id_item, cantidad
        )

    def quitar_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> bool:
        return self.inventarios.quitar_item(
            id_personaje, id_item, cantidad
        )

    def agregar_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> Inventario:
        return self.inventarios.agregar_item(
            id_personaje, id_item, cantidad
        )
