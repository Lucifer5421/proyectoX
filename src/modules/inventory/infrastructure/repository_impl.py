# ============================================================================
# MÓDULO: inventory  |  CAPA: infrastructure  |  ARCHIVO: repository_impl.py
# QUÉ HACE: Repositorios con SQLAlchemy ORM: convierten las entidades ORM
#           (models_db.py) en entidades de dominio y consultan PostgreSQL.
#           No contienen SQL crudo; eso está en init.sql.
# DETALLE: clases: ItemRepositoryImpl, InventarioRepositoryImpl
# ============================================================================
"""Repositorios con SQLAlchemy ORM: convierten las entidades ORM (models_db.py)
en entidades de dominio y consultan PostgreSQL. No contienen SQL crudo."""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.inventory.domain.models import Inventario, Item
from src.modules.inventory.domain.repositories import (
    InventarioRepository,
    ItemRepository,
)
from src.modules.inventory.infrastructure import models_db as db


def _item(row: db.ItemModel) -> Item:
    return Item(
        id_item=row.id_item,
        nombre=row.nombre,
        rareza=row.rareza or "comun",
        nivel_requerido=row.nivel_requerido or 1,
        precio_base=row.precio_base or Decimal("0"),
    )


def _inventario(row: db.InventarioModel) -> Inventario:
    return Inventario(
        id_inventario=row.id_inventario,
        id_personaje=row.id_personaje,
        id_item=row.id_item,
        cantidad=row.cantidad,
    )


class ItemRepositoryImpl(ItemRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id_item: int) -> Optional[Item]:
        row = self.session.get(db.ItemModel, id_item)
        return _item(row) if row else None

    def listar(self) -> List[Item]:
        rows = (
            self.session.query(db.ItemModel)
            .order_by(db.ItemModel.id_item.asc())
            .all()
        )
        return [_item(row) for row in rows]


class InventarioRepositoryImpl(InventarioRepository):
    def __init__(self, session: Session):
        self.session = session

    def _fila(
        self, id_personaje: int, id_item: int
    ) -> Optional[db.InventarioModel]:
        return (
            self.session.query(db.InventarioModel)
            .filter_by(id_personaje=id_personaje, id_item=id_item)
            .first()
        )

    def obtener(
        self, id_personaje: int, id_item: int
    ) -> Optional[Inventario]:
        row = self._fila(id_personaje, id_item)
        return _inventario(row) if row else None

    def listar_por_personaje(self, id_personaje: int) -> List[Inventario]:
        rows = (
            self.session.query(db.InventarioModel)
            .filter_by(id_personaje=id_personaje)
            .order_by(db.InventarioModel.id_item.asc())
            .all()
        )
        return [_inventario(row) for row in rows]

    def tiene_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> bool:
        row = self._fila(id_personaje, id_item)
        return bool(row and row.cantidad >= cantidad)

    def quitar_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> bool:
        row = self._fila(id_personaje, id_item)
        if not row or row.cantidad < cantidad:
            return False
        row.cantidad -= cantidad
        if row.cantidad == 0:
            self.session.delete(row)
        self.session.commit()
        return True

    def agregar_item(
        self, id_personaje: int, id_item: int, cantidad: int = 1
    ) -> Inventario:
        row = self._fila(id_personaje, id_item)
        if row:
            row.cantidad += cantidad
        else:
            row = db.InventarioModel(
                id_personaje=id_personaje,
                id_item=id_item,
                cantidad=cantidad,
            )
            self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _inventario(row)
