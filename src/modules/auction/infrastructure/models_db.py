"""Modelos ORM (SQLAlchemy) del módulo de subastas.

Esta capa traduce las entidades de dominio a tablas PostgreSQL.
No contiene reglas de negocio: solo persistencia.
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
from sqlalchemy.orm import relationship

from src.core.database import Base


class JugadorModel(Base):
    __tablename__ = "jugador"

    id_jugador = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(64), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    oro = Column(Numeric(12, 2), nullable=False, default=0)

    personajes = relationship(
        "PersonajeModel", back_populates="jugador", cascade="all, delete-orphan"
    )


class PersonajeModel(Base):
    __tablename__ = "personaje"

    id_personaje = Column(Integer, primary_key=True, index=True)
    id_jugador = Column(
        Integer,
        ForeignKey("jugador.id_jugador", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = Column(String(64), nullable=False)
    nivel = Column(Integer, nullable=False, default=1)
    clase = Column(String(30))
    oro = Column(Numeric(12, 2), nullable=False, default=0)

    jugador = relationship("JugadorModel", back_populates="personajes")
    inventario = relationship(
        "InventarioModel", back_populates="personaje", cascade="all, delete-orphan"
    )
    subastas = relationship(
        "SubastaModel",
        back_populates="vendedor",
        foreign_keys="SubastaModel.id_vendedor",
    )
    pujas = relationship(
        "PujaModel",
        back_populates="comprador",
        foreign_keys="PujaModel.id_comprador",
    )
    correos = relationship(
        "CorreoModel",
        back_populates="destinatario",
        foreign_keys="CorreoModel.id_destinatario",
    )


class ItemModel(Base):
    __tablename__ = "item"

    id_item = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    rareza = Column(String(30), default="comun")
    nivel_requerido = Column(Integer, default=1)
    precio_base = Column(Numeric(10, 2), default=0)

    inventarios = relationship("InventarioModel", back_populates="item")
    subastas = relationship("SubastaModel", back_populates="item")
    correos = relationship("CorreoModel", back_populates="item")


class InventarioModel(Base):
    __tablename__ = "inventario"

    id_inventario = Column(Integer, primary_key=True, index=True)
    id_personaje = Column(
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

    personaje = relationship("PersonajeModel", back_populates="inventario")
    item = relationship("ItemModel", back_populates="inventarios")


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
            "duracion_horas IN (2, 8, 24)", name="ck_duracion_subasta"
        ),
    )

    vendedor = relationship(
        "PersonajeModel",
        back_populates="subastas",
        foreign_keys=[id_vendedor],
    )
    item = relationship("ItemModel", back_populates="subastas")
    pujas = relationship(
        "PujaModel", back_populates="subasta", cascade="all, delete-orphan"
    )
    deposito = relationship(
        "DepositoModel",
        back_populates="subasta",
        uselist=False,
        cascade="all, delete-orphan",
    )
    comision = relationship(
        "ComisionModel",
        back_populates="subasta",
        uselist=False,
        cascade="all, delete-orphan",
    )
    transaccion = relationship(
        "TransaccionModel",
        back_populates="subasta",
        uselist=False,
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

    subasta = relationship("SubastaModel", back_populates="pujas")
    comprador = relationship(
        "PersonajeModel",
        back_populates="pujas",
        foreign_keys=[id_comprador],
    )


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

    subasta = relationship("SubastaModel", back_populates="deposito")


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

    subasta = relationship("SubastaModel", back_populates="comision")


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
    id_vendedor = Column(
        Integer,
        ForeignKey("personaje.id_personaje", ondelete="CASCADE"),
        nullable=False,
    )
    monto = Column(Numeric(10, 2), nullable=False)
    tipo = Column(String(20), nullable=False)
    fecha = Column(TIMESTAMP, server_default=func.now())

    subasta = relationship("SubastaModel", back_populates="transaccion")
    comprador = relationship("PersonajeModel", foreign_keys=[id_comprador])
    vendedor = relationship("PersonajeModel", foreign_keys=[id_vendedor])


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

    destinatario = relationship(
        "PersonajeModel",
        back_populates="correos",
        foreign_keys=[id_destinatario],
    )
    item = relationship("ItemModel", back_populates="correos")
