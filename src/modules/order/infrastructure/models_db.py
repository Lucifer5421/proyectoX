"""Modelos ORM del módulo order (subastas): subasta y puja."""

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import relationship

from src.core.database import Base


class SubastaModel(Base):
    __tablename__ = "subasta"

    id_subasta = Column(Integer, primary_key=True, index=True)
    id_vendedor = Column(
        Integer,
        ForeignKey("personaje.id_personaje", ondelete="CASCADE"),
        nullable=False,
    )
    id_item = Column(
        Integer,
        ForeignKey("item.id_item", ondelete="CASCADE"),
        nullable=False,
    )
    cantidad = Column(Integer, nullable=False, default=1)
    precio_salida = Column(Numeric(10, 2), nullable=False)
    precio_compra_directa = Column(Numeric(10, 2))
    duracion_horas = Column(Integer, nullable=False, default=24)
    estado = Column(String(20), nullable=False, default="activa")
    fecha_inicio = Column(TIMESTAMP, server_default=func.now())
    fecha_fin = Column(TIMESTAMP, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "duracion_horas IN (2, 8, 24)",
            name="ck_duracion_subasta",
        ),
        CheckConstraint(
            "estado IN ('activa', 'vendida', 'expirada', 'cancelada')",
            name="ck_estado_subasta",
        ),
    )

    pujas = relationship(
        "PujaModel",
        back_populates="subasta",
        cascade="all, delete-orphan",
    )


class PujaModel(Base):
    __tablename__ = "puja"

    id_puja = Column(Integer, primary_key=True, index=True)
    id_subasta = Column(
        Integer,
        ForeignKey("subasta.id_subasta", ondelete="CASCADE"),
        nullable=False,
    )
    id_comprador = Column(
        Integer,
        ForeignKey("personaje.id_personaje", ondelete="CASCADE"),
        nullable=False,
    )
    monto = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), nullable=False, default="activa")
    fecha = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "estado IN ('activa', 'superada', 'ganadora')",
            name="ck_estado_puja",
        ),
    )

    subasta = relationship("SubastaModel", back_populates="pujas")
