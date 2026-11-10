"""Implementaciones concretas de los repositorios con SQLAlchemy."""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.auction.domain.models import (
    Correo,
    EstadoCorreo,
    EstadoPuja,
    EstadoSubasta,
    Item,
    Jugador,
    Personaje,
    Puja,
    Subasta,
    TipoTransaccion,
    Transaccion,
)
from src.modules.auction.domain.repositories import (
    CorreoRepository,
    ItemRepository,
    JugadorRepository,
    PersonajeRepository,
    PujaRepository,
    SubastaRepository,
    TransaccionRepository,
)
from src.modules.auction.infrastructure import models_db as db


# ---------------------------------------------------------------------------
# Mapeadores ORM -> Dominio
# ---------------------------------------------------------------------------
def _jugador(row: db.JugadorModel) -> Jugador:
    return Jugador(
        id_jugador=row.id_jugador,
        nombre=row.nombre,
        email=row.email,
        oro=row.oro,
    )


def _personaje(row: db.PersonajeModel) -> Personaje:
    return Personaje(
        id_personaje=row.id_personaje,
        id_jugador=row.id_jugador,
        nombre=row.nombre,
        nivel=row.nivel,
        clase=row.clase or "",
        oro=row.oro,
    )


def _item(row: db.ItemModel) -> Item:
    return Item(
        id_item=row.id_item,
        nombre=row.nombre,
        rareza=row.rareza or "comun",
        nivel_requerido=row.nivel_requerido or 1,
        precio_base=row.precio_base or Decimal("0"),
    )


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


def _correo(row: db.CorreoModel) -> Correo:
    return Correo(
        id_correo=row.id_correo,
        id_destinatario=row.id_destinatario,
        asunto=row.asunto,
        id_item=row.id_item,
        cantidad=row.cantidad or 0,
        oro=row.oro or Decimal("0"),
        estado=EstadoCorreo(row.estado),
        fecha=row.fecha,
    )


def _transaccion(row: db.TransaccionModel) -> Transaccion:
    return Transaccion(
        id_transaccion=row.id_transaccion,
        id_subasta=row.id_subasta,
        id_comprador=row.id_comprador,
        id_vendedor=row.id_vendedor,
        monto=row.monto,
        tipo=TipoTransaccion(row.tipo),
        fecha=row.fecha,
    )


# ---------------------------------------------------------------------------
# Repositorios
# ---------------------------------------------------------------------------
class JugadorRepositoryImpl(JugadorRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id_jugador: int) -> Optional[Jugador]:
        row = self.session.get(db.JugadorModel, id_jugador)
        return _jugador(row) if row else None

    def actualizar_oro(self, id_jugador: int, oro: Decimal) -> None:
        row = self.session.get(db.JugadorModel, id_jugador)
        if row:
            row.oro = oro
            self.session.commit()


class PersonajeRepositoryImpl(PersonajeRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id_personaje: int) -> Optional[Personaje]:
        row = self.session.get(db.PersonajeModel, id_personaje)
        return _personaje(row) if row else None

    def actualizar_oro(self, id_personaje: int, oro: Decimal) -> None:
        row = self.session.get(db.PersonajeModel, id_personaje)
        if row:
            row.oro = oro
            self.session.commit()

    def tiene_item(self, id_personaje: int, id_item: int, cantidad: int = 1) -> bool:
        row = (
            self.session.query(db.InventarioModel)
            .filter_by(id_personaje=id_personaje, id_item=id_item)
            .first()
        )
        return bool(row and row.cantidad >= cantidad)

    def quitar_item(self, id_personaje: int, id_item: int, cantidad: int = 1) -> bool:
        row = (
            self.session.query(db.InventarioModel)
            .filter_by(id_personaje=id_personaje, id_item=id_item)
            .first()
        )
        if not row or row.cantidad < cantidad:
            return False
        row.cantidad -= cantidad
        if row.cantidad == 0:
            self.session.delete(row)
        self.session.commit()
        return True


class ItemRepositoryImpl(ItemRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id_item: int) -> Optional[Item]:
        row = self.session.get(db.ItemModel, id_item)
        return _item(row) if row else None

    def listar(self) -> List[Item]:
        rows = self.session.query(db.ItemModel).all()
        return [_item(r) for r in rows]


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
        return [_subasta(r) for r in rows]

    def actualizar(self, subasta: Subasta) -> Subasta:
        row = self.session.get(db.SubastaModel, subasta.id_subasta)
        if row:
            row.estado = subasta.estado.value
            row.fecha_fin = subasta.fecha_fin
            row.precio_salida = subasta.precio_salida
            row.precio_compra_directa = subasta.precio_compra_directa
            self.session.commit()
        return subasta

    def crear_deposito(self, id_subasta: int, monto: Decimal) -> None:
        row = db.DepositoModel(
            id_subasta=id_subasta,
            monto=monto,
            pagado=True,
        )
        self.session.add(row)
        self.session.commit()

    def crear_comision(
        self, id_subasta: int, porcentaje: Decimal, monto: Decimal
    ) -> None:
        row = db.ComisionModel(
            id_subasta=id_subasta,
            porcentaje=porcentaje,
            monto=monto,
        )
        self.session.add(row)
        self.session.commit()


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
        return [_puja(r) for r in rows]

    def actualizar_estado(self, id_puja: int, estado: str) -> None:
        row = self.session.get(db.PujaModel, id_puja)
        if row:
            row.estado = estado
            self.session.commit()


class CorreoRepositoryImpl(CorreoRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(self, correo: Correo) -> Correo:
        row = db.CorreoModel(
            id_destinatario=correo.id_destinatario,
            id_item=correo.id_item,
            cantidad=correo.cantidad,
            oro=correo.oro,
            asunto=correo.asunto,
            estado=correo.estado.value,
            fecha=correo.fecha,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        correo.id_correo = row.id_correo
        return correo

    def listar_por_destinatario(self, id_destinatario: int) -> List[Correo]:
        rows = (
            self.session.query(db.CorreoModel)
            .filter_by(id_destinatario=id_destinatario)
            .order_by(db.CorreoModel.fecha.desc())
            .all()
        )
        return [_correo(r) for r in rows]


class TransaccionRepositoryImpl(TransaccionRepository):
    def __init__(self, session: Session):
        self.session = session

    def crear(self, transaccion: Transaccion) -> Transaccion:
        row = db.TransaccionModel(
            id_subasta=transaccion.id_subasta,
            id_comprador=transaccion.id_comprador,
            id_vendedor=transaccion.id_vendedor,
            monto=transaccion.monto,
            tipo=transaccion.tipo.value,
            fecha=transaccion.fecha,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        transaccion.id_transaccion = row.id_transaccion
        return transaccion
