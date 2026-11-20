# ============================================================================
# MÓDULO: auth  |  CAPA: infrastructure  |  ARCHIVO: models_db.py
# QUÉ HACE: Modelos ORM del módulo auth: jugador y personaje.
# DETALLE: clases: JugadorModel, PersonajeModel
# ============================================================================
"""Modelos ORM del módulo auth: jugador y personaje."""

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


class JugadorModel(Base):
    __tablename__ = "jugador"

    id_jugador = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(64), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    fecha_registro = Column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    # Cuenta de AzerothCore asociada (columna técnica de integración).
    wow_account_id = Column(Integer, unique=True, nullable=True, index=True)

    personajes = relationship(
        "PersonajeModel",
        back_populates="jugador",
        cascade="all, delete-orphan",
    )


class PersonajeModel(Base):
    __tablename__ = "personaje"

    id_personaje = Column(Integer, primary_key=True, index=True)
    id_jugador = Column(
        Integer,
        ForeignKey("jugador.id_jugador", ondelete="CASCADE"),
        nullable=False,
    )
    nombre = Column(String(64), unique=True, nullable=False)
    nivel = Column(Integer, nullable=False, default=1)
    clase = Column(String(30))
    oro = Column(Numeric(12, 2), nullable=False, default=0)
    # GUID del personaje en acore_characters.characters.
    wow_guid = Column(Integer, unique=True, nullable=True, index=True)

    __table_args__ = (
        CheckConstraint(
            "nivel >= 1 AND oro >= 0",
            name="ck_personaje_nivel_oro",
        ),
    )

    jugador = relationship("JugadorModel", back_populates="personajes")
