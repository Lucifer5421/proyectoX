# ============================================================================
# MÓDULO: mail  |  CAPA: infrastructure  |  ARCHIVO: repository_impl.py
# QUÉ HACE: Implementaciones SQLAlchemy de los repositorios de mail.
# DETALLE: clases: CorreoRepositoryImpl
# ============================================================================
"""Implementaciones SQLAlchemy de los repositorios de mail."""

from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from src.modules.mail.domain.models import (
    Correo,
    EstadoCorreo,
)
from src.modules.mail.domain.repositories import CorreoRepository
from src.modules.mail.infrastructure import models_db as db


def _correo(row: db.CorreoModel) -> Correo:
    """Convierte una fila ORM en la entidad pura del dominio."""
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


class CorreoRepositoryImpl(CorreoRepository):
    """Persistencia del correo sobre PostgreSQL."""

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

    def listar_por_destinatario(
        self, id_destinatario: int
    ) -> List[Correo]:
        rows = (
            self.session.query(db.CorreoModel)
            .filter_by(id_destinatario=id_destinatario)
            .order_by(db.CorreoModel.fecha.desc())
            .all()
        )
        return [_correo(row) for row in rows]
