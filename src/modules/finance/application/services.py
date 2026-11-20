# ============================================================================
# MÓDULO: finance  |  CAPA: application  |  ARCHIVO: services.py
# QUÉ HACE: Casos de uso del módulo finance.
# DETALLE: clases: FinanceService
# ============================================================================
"""Casos de uso del módulo finance.

Registra depósitos, comisiones y transacciones de una subasta. El correo
pertenece al módulo `mail`. No conoce FastAPI.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.finance.domain.models import (
    TipoTransaccion,
    Transaccion,
)
from src.modules.finance.infrastructure.repository_impl import (
    ComisionRepositoryImpl,
    DepositoRepositoryImpl,
    TransaccionRepositoryImpl,
)


class FinanceService:
    """Servicio de aplicación de las finanzas de la subasta."""

    def __init__(self, session: Session):
        self.session = session
        self.depositos = DepositoRepositoryImpl(session)
        self.comisiones = ComisionRepositoryImpl(session)
        self.transacciones = TransaccionRepositoryImpl(session)

    def crear_deposito(
        self, id_subasta: int, monto: Decimal
    ) -> None:
        """Registra el depósito pagado al publicar la subasta."""
        self.depositos.crear(id_subasta, monto)

    def crear_comision(
        self,
        id_subasta: int,
        porcentaje: Decimal,
        monto: Decimal,
    ) -> None:
        """Registra la comisión generada por la venta."""
        self.comisiones.crear(id_subasta, porcentaje, monto)

    def registrar_transaccion(
        self,
        id_subasta: int,
        id_comprador: int,
        monto: Decimal,
        tipo: TipoTransaccion,
    ) -> Transaccion:
        """Registra la transacción que cierra económicamente la subasta."""
        return self.transacciones.crear(
            Transaccion(
                id_subasta=id_subasta,
                id_comprador=id_comprador,
                monto=monto,
                tipo=tipo,
            )
        )
