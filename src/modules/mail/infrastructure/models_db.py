# ============================================================================
# MÓDULO: mail  |  CAPA: infrastructure  |  ARCHIVO: models_db.py
# QUÉ HACE: Modelos ORM del módulo mail: correo.
# DETALLE: clases: CorreoModel
# ============================================================================
"""Modelos ORM del módulo mail: correo.

Solo entidades SQLAlchemy. Las reglas de negocio viven en
`src/modules/mail/domain/models.py`.
"""

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

from src.core.database import Base


class CorreoModel(Base):
    """Tabla `correo`: entrega de un ítem u oro a un personaje.

    Relaciones del modelo 2.1:
      - `id_destinatario` -> `personaje.id_personaje` (N:1, obligatoria).
      - `id_item` -> `item.id_item` (N:1, opcional; SET NULL al borrar).
    """

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
