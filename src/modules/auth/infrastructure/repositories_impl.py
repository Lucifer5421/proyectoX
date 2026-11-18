"""Implementaciones SQLAlchemy de los repositorios de auth."""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.auth.domain.models import Jugador, Personaje
from src.modules.auth.domain.repositories import (
    JugadorRepository,
    PersonajeRepository,
)
from src.modules.auth.infrastructure import models_db as db


def _jugador(row: db.JugadorModel) -> Jugador:
    return Jugador(
        id_jugador=row.id_jugador,
        nombre=row.nombre,
        email=row.email,
        fecha_registro=row.fecha_registro,
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


class JugadorRepositoryImpl(JugadorRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id_jugador: int) -> Optional[Jugador]:
        row = self.session.get(db.JugadorModel, id_jugador)
        return _jugador(row) if row else None

    def listar(self) -> List[Jugador]:
        rows = (
            self.session.query(db.JugadorModel)
            .order_by(db.JugadorModel.id_jugador.asc())
            .all()
        )
        return [_jugador(row) for row in rows]


class PersonajeRepositoryImpl(PersonajeRepository):
    def __init__(self, session: Session):
        self.session = session

    def obtener(self, id_personaje: int) -> Optional[Personaje]:
        row = self.session.get(db.PersonajeModel, id_personaje)
        return _personaje(row) if row else None

    def listar(self) -> List[Personaje]:
        rows = (
            self.session.query(db.PersonajeModel)
            .order_by(db.PersonajeModel.id_personaje.asc())
            .all()
        )
        return [_personaje(row) for row in rows]

    def actualizar_oro(self, id_personaje: int, oro: Decimal) -> None:
        row = self.session.get(db.PersonajeModel, id_personaje)
        if row:
            row.oro = oro
            self.session.commit()
