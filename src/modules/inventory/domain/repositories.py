"""Contratos de repositorio del módulo inventory."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.inventory.domain.models import Inventario, Item


class ItemRepository(ABC):
    @abstractmethod
    def obtener(self, id_item: int) -> Optional[Item]:
        ...

    @abstractmethod
    def listar(self) -> List[Item]:
        ...


class InventarioRepository(ABC):
    @abstractmethod
    def obtener(
        self, id_personaje: int, id_item: int
    ) -> Optional[Inventario]:
        ...

    @abstractmethod
    def listar_por_personaje(self, id_personaje: int) -> List[Inventario]:
        ...

    @abstractmethod
    def tiene_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> bool:
        ...

    @abstractmethod
    def quitar_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> bool:
        ...

    @abstractmethod
    def agregar_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> Inventario:
        ...
