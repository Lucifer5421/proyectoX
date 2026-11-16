"""Contratos de repositorio del módulo finance."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List

from src.modules.finance.domain.models import Correo, Transaccion


class DepositoRepository(ABC):
    @abstractmethod
    def crear(
        self, id_subasta: int, monto: Decimal, pagado: bool = True
    ) -> None:
        ...


class ComisionRepository(ABC):
    @abstractmethod
    def crear(
        self, id_subasta: int, porcentaje: Decimal, monto: Decimal
    ) -> None:
        ...


class TransaccionRepository(ABC):
    @abstractmethod
    def crear(self, transaccion: Transaccion) -> Transaccion:
        ...


class CorreoRepository(ABC):
    @abstractmethod
    def crear(self, correo: Correo) -> Correo:
        ...

    @abstractmethod
    def listar_por_destinatario(self, id_destinatario: int) -> List[Correo]:
        ...
