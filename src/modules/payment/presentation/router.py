"""Capa de presentación del módulo payment (finanzas)."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.payment.application.services import FinanceService
from src.modules.payment.application.dtos import CorreoOut

router = APIRouter(prefix="/mail", tags=["Correo"])


def get_service(db: Session = Depends(get_db)) -> FinanceService:
    return FinanceService(db)


@router.get("/{id_personaje}", response_model=List[CorreoOut])
def listar_correo(
    id_personaje: int,
    service: FinanceService = Depends(get_service),
):
    return service.listar_correo(id_personaje)
