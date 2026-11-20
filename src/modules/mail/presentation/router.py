# ============================================================================
# MÓDULO: mail  |  CAPA: presentation  |  ARCHIVO: router.py
# QUÉ HACE: Capa de presentación (API REST) del módulo mail.
# DETALLE: endpoints: GET /{id_personaje}
# ============================================================================
"""Capa de presentación (API REST) del módulo mail."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.mail.application.dtos import CorreoOut
from src.modules.mail.application.services import MailService

router = APIRouter(prefix="/mail", tags=["Correo"])


def get_service(db: Session = Depends(get_db)) -> MailService:
    return MailService(db)


@router.get("/{id_personaje}", response_model=List[CorreoOut])
def listar_correo(
    id_personaje: int,
    service: MailService = Depends(get_service),
):
    return service.listar_correo(id_personaje)
