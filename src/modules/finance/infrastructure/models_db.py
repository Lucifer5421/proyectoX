# ============================================================================
# MÓDULO: finance  |  CAPA: infrastructure  |  ARCHIVO: models_db.py
# QUÉ HACE: Modelos ORM de SQLAlchemy: mapean las tablas del modelo 2.1
#           a clases Python. Las tablas las crea init.sql; aquí solo se representan.
# DETALLE: clases: DepositoModel, ComisionModel, TransaccionModel
# ============================================================================
"""Modelos ORM de SQLAlchemy: mapean las tablas del modelo 2.1 a clases Python.
Las tablas las crea init.sql; aquí solo se representan.

Solo entidades SQLAlchemy. Las reglas de negocio viven en
`src/modules/finance/domain/models.py`.
"""

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)

from src.core.database import Base


class DepositoModel(Base):
    """Tabla `deposito`: garantía 1:1 de una subasta."""

    __tablename__ = "deposito"

    id_deposito = Column(Integer, primary_key=True, index=True)
    id_subasta = Column(
        Integer,
        ForeignKey("subasta.id_subasta", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    monto = Column(Numeric(10, 2), nullable=False)
    pagado = Column(Boolean, nullable=False, default=False)
    fecha = Column(TIMESTAMP, server_default=func.now())


class ComisionModel(Base):
    """Tabla `comision`: comisión 1:1 generada por una subasta."""

    __tablename__ = "comision"

    id_comision = Column(Integer, primary_key=True, index=True)
    id_subasta = Column(
        Integer,
        ForeignKey("subasta.id_subasta", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    porcentaje = Column(Numeric(5, 2), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    fecha = Column(TIMESTAMP, server_default=func.now())


class TransaccionModel(Base):
    """Tabla `transaccion`: cierre económico 1:1 de una subasta.

    `id_comprador` referencia al personaje que gana la subasta.
    """

    __tablename__ = "transaccion"

    id_transaccion = Column(Integer, primary_key=True, index=True)
    id_subasta = Column(
        Integer,
        ForeignKey("subasta.id_subasta", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    id_comprador = Column(
        Integer,
        ForeignKey("personaje.id_personaje", ondelete="CASCADE"),
        nullable=False,
    )
    monto = Column(Numeric(10, 2), nullable=False)
    tipo = Column(String(20), nullable=False)
    fecha = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('puja_ganadora', 'compra_directa')",
            name="ck_tipo_transaccion",
        ),
    )
