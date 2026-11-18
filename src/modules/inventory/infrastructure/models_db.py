"""Modelos ORM del módulo inventory (catálogo e inventario): item e inventario."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)

from src.core.database import Base


class ItemModel(Base):
    __tablename__ = "item"

    id_item = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    rareza = Column(String(30), default="comun")
    nivel_requerido = Column(Integer, default=1)
    precio_base = Column(Numeric(10, 2), default=0)
    # entry de acore_world.item_template (columna técnica de integración).
    wow_entry = Column(Integer, unique=True, nullable=True, index=True)


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

    __table_args__ = (
        UniqueConstraint(
            "id_personaje",
            "id_item",
            name="uq_inventario_personaje_item",
        ),
        CheckConstraint(
            "cantidad > 0",
            name="ck_inventario_cantidad",
        ),
    )
