"""Implementaciones SQLAlchemy de los repositorios de payment (finanzas)."""

from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from src.modules.payment.domain.models import (
    Comision,
    Correo,
    Deposito,
    EstadoCorreo,
    TipoTransaccion,
    Transaccion,
)
from src.modules.payment.domain.repositories import (
    ComisionRepository,
    CorreoRepository,
    DepositoRepository,
    TransaccionRepository,
)
from src.modules.payment.infrastructure import models_db as db


def _deposito(row: db.DepositoModel) -> Deposito:
    return Deposito(
        id_deposito=row.id_deposito,
        id_subasta=row.id_subasta,
        monto=row.monto,
        pagado=row.pagado,
        fecha=row.fecha,
    )


def _comision(row: db.ComisionModel) -> Comision:
    return Comision(
        id_comision=row.id_comision,
        id_subasta=row.id_subasta,
        porcentaje=row.porcentaje,
        monto=row.monto,
        fecha=row.fecha,
    )


def _transaccion(row: db.TransaccionModel) -> Transaccion:
    return Transaccion(
        id_transaccion=row.id_transaccion,
        id_subasta=row.id_subasta,
        id_comprador=row.id_comprador,
        monto=row.monto,
        tipo=TipoTransaccion(row.tipo),
        fecha=row.fecha,
    )


def _correo(row: db.CorreoModel) -> Correo:
    return Correo(
        id_correo=row.id_correo,
        id_destinatario=row.id_destinatario,
        asunto=row.asunto,
        id_item=row.id_item,
        cantidad=row.cantidad or 0,
        oro=row.oro or Decimal("0"),
        estado=EstadoCorreo(row.estado),
        fecha=row.fecha,
    )


class DepositoRepositoryImpl(DepositoRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(
        self, id_subasta: int, monto: Decimal, pagado: bool = True
    ) -> None:
        row = db.DepositoModel(
            id_subasta=id_subasta,
            monto=monto,
            pagado=pagado,
        )
        self.session.add(row)
        self.session.commit()


class ComisionRepositoryImpl(ComisionRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(
        self, id_subasta: int, porcentaje: Decimal, monto: Decimal
    ) -> None:
        row = db.ComisionModel(
            id_subasta=id_subasta,
            porcentaje=porcentaje,
            monto=monto,
        )
        self.session.add(row)
        self.session.commit()


class TransaccionRepositoryImpl(TransaccionRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(self, transaccion: Transaccion) -> Transaccion:
        row = db.TransaccionModel(
            id_subasta=transaccion.id_subasta,
            id_comprador=transaccion.id_comprador,
            monto=transaccion.monto,
            tipo=transaccion.tipo.value,
            fecha=transaccion.fecha,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        transaccion.id_transaccion = row.id_transaccion
        return transaccion


class CorreoRepositoryImpl(CorreoRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(self, correo: Correo) -> Correo:
        row = db.CorreoModel(
            id_destinatario=correo.id_destinatario,
            id_item=correo.id_item,
            cantidad=correo.cantidad,
            oro=correo.oro,
            asunto=correo.asunto,
            estado=correo.estado.value,
            fecha=correo.fecha,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        correo.id_correo = row.id_correo
        return correo

    def listar_por_destinatario(
        self, id_destinatario: int
    ) -> List[Correo]:
        rows = (
            self.session.query(db.CorreoModel)
            .filter_by(id_destinatario=id_destinatario)
            .order_by(db.CorreoModel.fecha.desc())
            .all()
        )
        return [_correo(row) for row in rows]
