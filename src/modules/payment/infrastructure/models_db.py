"""Modelos ORM del módulo payment (finanzas): depósito, comisión, transacción y correo."""

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


class CorreoModel(Base):
    __tablename__ = "correo"

    id_correo = Column(Integer, primary_key=True, index=True)
    id_destinatario = Column(
        Integer,
        ForeignKey("personaje.id_personaje", ondelete="CASCADE"),
        nullable=False,
    )
    id_item = Column(
        Integer,
        ForeignKey("item.id_item", ondelete="SET NULL"),
        nullable=True,
    )
    cantidad = Column(Integer, default=0)
    oro = Column(Numeric(12, 2), default=0)
    asunto = Column(String(150), nullable=False)
    estado = Column(String(20), nullable=False, default="pendiente")
    fecha = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'leido', 'cobrado', 'devuelto')",
            name="ck_estado_correo",
        ),
    )
