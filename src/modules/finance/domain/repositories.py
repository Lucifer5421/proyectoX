"""Contratos de repositorio del módulo finance."""

from abc import ABC, abstractmethod
from decimal import Decimal

from src.modules.finance.domain.models import Transaccion


class DepositoRepository(ABC):
    """Contrato de persistencia de los depósitos de subasta."""

    @abstractmethod
    def crear(
        self, id_subasta: int, monto: Decimal, pagado: bool = True
    ) -> None:
        ...


class ComisionRepository(ABC):
    """Contrato de persistencia de las comisiones de subasta."""

    @abstractmethod
    def crear(
        self, id_subasta: int, porcentaje: Decimal, monto: Decimal
    ) -> None:
        ...


class TransaccionRepository(ABC):
    """Contrato de persistencia de las transacciones económicas."""

    @abstractmethod
    def crear(self, transaccion: Transaccion) -> Transaccion:
        ...
