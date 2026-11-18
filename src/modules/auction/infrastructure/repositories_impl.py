"""Implementaciones SQLAlchemy de los repositorios de auction."""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.auction.domain.models import (
    EstadoPuja,
    EstadoSubasta,
    Puja,
    Subasta,
)
from src.modules.auction.domain.repositories import (
    PujaRepository,
    SubastaRepository,
)
from src.modules.auction.infrastructure import models_db as db


def _puja(row: db.PujaModel) -> Puja:
    return Puja(
        id_puja=row.id_puja,
        id_subasta=row.id_subasta,
        id_comprador=row.id_comprador,
        monto=row.monto,
        estado=EstadoPuja(row.estado),
        fecha=row.fecha,
    )


def _subasta(row: db.SubastaModel) -> Subasta:
    return Subasta(
        id_subasta=row.id_subasta,
        id_vendedor=row.id_vendedor,
        id_item=row.id_item,
        cantidad=row.cantidad,
        precio_salida=row.precio_salida,
        precio_compra_directa=row.precio_compra_directa,
        duracion_horas=row.duracion_horas,
        estado=EstadoSubasta(row.estado),
        fecha_inicio=row.fecha_inicio,
        fecha_fin=row.fecha_fin,
        pujas=[_puja(p) for p in row.pujas],
    )


class SubastaRepositoryImpl(SubastaRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(self, subasta: Subasta) -> Subasta:
        row = db.SubastaModel(
            id_vendedor=subasta.id_vendedor,
            id_item=subasta.id_item,
            cantidad=subasta.cantidad,
            precio_salida=subasta.precio_salida,
            precio_compra_directa=subasta.precio_compra_directa,
            duracion_horas=subasta.duracion_horas,
            estado=subasta.estado.value,
            fecha_inicio=subasta.fecha_inicio,
            fecha_fin=subasta.fecha_fin,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        subasta.id_subasta = row.id_subasta
        return subasta

    def obtener(self, id_subasta: int) -> Optional[Subasta]:
        row = self.session.get(db.SubastaModel, id_subasta)
        return _subasta(row) if row else None

    def listar_activas(self) -> List[Subasta]:
        rows = (
            self.session.query(db.SubastaModel)
            .filter_by(estado=EstadoSubasta.ACTIVA.value)
            .order_by(db.SubastaModel.fecha_fin.asc())
            .all()
        )
        return [_subasta(row) for row in rows]

    def actualizar(self, subasta: Subasta) -> Subasta:
        row = self.session.get(db.SubastaModel, subasta.id_subasta)
        if row:
            row.estado = subasta.estado.value
            row.fecha_fin = subasta.fecha_fin
            row.precio_salida = subasta.precio_salida
            row.precio_compra_directa = subasta.precio_compra_directa
            self.session.commit()
        return subasta


class PujaRepositoryImpl(PujaRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(self, puja: Puja) -> Puja:
        row = db.PujaModel(
            id_subasta=puja.id_subasta,
            id_comprador=puja.id_comprador,
            monto=puja.monto,
            estado=puja.estado.value,
            fecha=puja.fecha,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        puja.id_puja = row.id_puja
        return puja

    def listar_por_subasta(self, id_subasta: int) -> List[Puja]:
        rows = (
            self.session.query(db.PujaModel)
            .filter_by(id_subasta=id_subasta)
            .order_by(db.PujaModel.monto.desc())
            .all()
        )
        return [_puja(row) for row in rows]

    def actualizar_estado(self, id_puja: int, estado: str) -> None:
        row = self.session.get(db.PujaModel, id_puja)
        if row:
            row.estado = estado
            self.session.commit()
