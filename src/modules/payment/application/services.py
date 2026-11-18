"""Casos de uso del módulo payment (finanzas).

Registra depósitos, comisiones, transacciones y correo. No conoce FastAPI.
"""

from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from src.modules.payment.domain.models import (
    Correo,
    TipoTransaccion,
    Transaccion,
)
from src.modules.payment.infrastructure.repository_impl import (
    ComisionRepositoryImpl,
    CorreoRepositoryImpl,
    DepositoRepositoryImpl,
    TransaccionRepositoryImpl,
)


class FinanceService:
    def __init__(self, session: Session):
        self.session = session
        self.depositos = DepositoRepositoryImpl(session)
        self.comisiones = ComisionRepositoryImpl(session)
        self.transacciones = TransaccionRepositoryImpl(session)
        self.correos = CorreoRepositoryImpl(session)

    def crear_deposito(
        self, id_subasta: int, monto: Decimal
    ) -> None:
        self.depositos.crear(id_subasta, monto)

    def crear_comision(
        self,
        id_subasta: int,
        porcentaje: Decimal,
        monto: Decimal,
    ) -> None:
        self.comisiones.crear(id_subasta, porcentaje, monto)

    def registrar_transaccion(
        self,
        id_subasta: int,
        id_comprador: int,
        monto: Decimal,
        tipo: TipoTransaccion,
    ) -> Transaccion:
        return self.transacciones.crear(
            Transaccion(
                id_subasta=id_subasta,
                id_comprador=id_comprador,
                monto=monto,
                tipo=tipo,
            )
        )

    def crear_correo(self, correo: Correo) -> Correo:
        return self.correos.crear(correo)

    def listar_correo(self, id_personaje: int) -> List[Correo]:
        return self.correos.listar_por_destinatario(id_personaje)
