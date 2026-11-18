"""Capa de presentación del módulo auth."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.auth.application.services import AuthService
from src.modules.auth.presentation.schemas import JugadorOut, PersonajeOut

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def get_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.get("/players", response_model=List[JugadorOut])
def listar_jugadores(service: AuthService = Depends(get_service)):
    return service.listar_jugadores()


@router.get("/characters", response_model=List[PersonajeOut])
def listar_personajes(service: AuthService = Depends(get_service)):
    return service.listar_personajes()


@router.get("/characters/{id_personaje}", response_model=PersonajeOut)
def obtener_personaje(
    id_personaje: int,
    service: AuthService = Depends(get_service),
):
    try:
        return service.obtener_personaje(id_personaje)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
