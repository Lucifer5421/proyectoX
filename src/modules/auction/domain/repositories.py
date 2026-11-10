"""Contratos (interfaces) de repositorio.

La capa de aplicación depende de estas interfaces, no de SQLAlchemy.
Las implementaciones concretas viven en infrastructure/repository_impl.py.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from src.modules.auction.domain.models import (
    Correo,
    Item,
    Jugador,
    Personaje,
    Puja,
    Subasta,
    Transaccion,
)


class JugadorRepository(ABC):
    @abstractmethod
    def obtener(self, id_jugador: int) -> Optional[Jugador]:
        ...

    @abstractmethod
    def actualizar_oro(self, id_jugador: int, oro: Decimal) -> None:
        ...


class PersonajeRepository(ABC):
    @abstractmethod
    def obtener(self, id_personaje: int) -> Optional[Personaje]:
        ...

    @abstractmethod
    def actualizar_oro(self, id_personaje: int, oro: Decimal) -> None:
        ...

    @abstractmethod
    def tiene_item(self, id_personaje: int, id_item: int, cantidad: int = 1) -> bool:
        ...

    @abstractmethod
    def quitar_item(self, id_personaje: int, id_item: int, cantidad: int = 1) -> bool:
        ...


class ItemRepository(ABC):
    @abstractmethod
    def obtener(self, id_item: int) -> Optional[Item]:
        ...

    @abstractmethod
    def listar(self) -> List[Item]:
        ...


class SubastaRepository(ABC):
    @abstractmethod
    def crear(self, subasta: Subasta) -> Subasta:
        ...

    @abstractmethod
    def obtener(self, id_subasta: int) -> Optional[Subasta]:
        ...

    @abstractmethod
    def listar_activas(self) -> List[Subasta]:
        ...

    @abstractmethod
    def actualizar(self, subasta: Subasta) -> Subasta:
        ...

    @abstractmethod
    def crear_deposito(self, id_subasta: int, monto: Decimal) -> None:
        ...

    @abstractmethod
    def crear_comision(self, id_subasta: int, porcentaje: Decimal, monto: Decimal) -> None:
        ...


class PujaRepository(ABC):
    @abstractmethod
    def crear(self, puja: Puja) -> Puja:
        ...

    @abstractmethod
    def listar_por_subasta(self, id_subasta: int) -> List[Puja]:
        ...

    @abstractmethod
    def actualizar_estado(self, id_puja: int, estado: str) -> None:
        ...


class CorreoRepository(ABC):
    @abstractmethod
    def crear(self, correo: Correo) -> Correo:
        ...

    @abstractmethod
    def listar_por_destinatario(self, id_destinatario: int) -> List[Correo]:
        ...


class TransaccionRepository(ABC):
    @abstractmethod
    def crear(self, transaccion: Transaccion) -> Transaccion:
        ...
