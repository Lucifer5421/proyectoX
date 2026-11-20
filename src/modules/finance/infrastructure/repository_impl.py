# ============================================================================
# MÓDULO: finance  |  CAPA: infrastructure  |  ARCHIVO: repository_impl.py
# QUÉ HACE: Repositorios con SQLAlchemy ORM: convierten las entidades ORM
#           (models_db.py) en entidades de dominio y consultan PostgreSQL.
#           No contienen SQL crudo; eso está en init.sql.
# DETALLE: clases: DepositoRepositoryImpl, ComisionRepositoryImpl, TransaccionRepositoryImpl
# ============================================================================
"""Repositorios con SQLAlchemy ORM: convierten las entidades ORM (models_db.py)
en entidades de dominio y consultan PostgreSQL. No contienen SQL crudo."""

from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.finance.domain.models import (
    Comision,
    Deposito,
    TipoTransaccion,
    Transaccion,
)
from src.modules.finance.domain.repositories import (
    ComisionRepository,
    DepositoRepository,
    TransaccionRepository,
)
from src.modules.finance.infrastructure import models_db as db


def _deposito(row: db.DepositoModel) -> Deposito:
    """Convierte una fila ORM en la entidad pura del dominio."""
    return Deposito(
        id_deposito=row.id_deposito,
        id_subasta=row.id_subasta,
        monto=row.monto,
        pagado=row.pagado,
        fecha=row.fecha,
    )


def _comision(row: db.ComisionModel) -> Comision:
    """Convierte una fila ORM en la entidad pura del dominio."""
    return Comision(
        id_comision=row.id_comision,
        id_subasta=row.id_subasta,
        porcentaje=row.porcentaje,
        monto=row.monto,
        fecha=row.fecha,
    )


def _transaccion(row: db.TransaccionModel) -> Transaccion:
    """Convierte una fila ORM en la entidad pura del dominio."""
    return Transaccion(
        id_transaccion=row.id_transaccion,
        id_subasta=row.id_subasta,
        id_comprador=row.id_comprador,
        monto=row.monto,
        tipo=TipoTransaccion(row.tipo),
        fecha=row.fecha,
    )


class DepositoRepositoryImpl(DepositoRepository):
    """Persistencia de depósitos sobre PostgreSQL."""

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
    """Persistencia de comisiones sobre PostgreSQL."""

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
    """Persistencia de transacciones sobre PostgreSQL."""

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
