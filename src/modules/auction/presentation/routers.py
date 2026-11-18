"""Capa de presentación (API REST) del módulo de subastas."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.auction.application.services import AuctionService
from src.modules.auction.presentation.schemas import (
    CompraDirectaIn,
    PublicarSubastaIn,
    PujaIn,
    PujaOut,
    SubastaOut,
)

router = APIRouter(prefix="/auctions", tags=["Subastas"])


def get_service(db: Session = Depends(get_db)) -> AuctionService:
    return AuctionService(db)


# ---------------------------------------------------------------------------
# Subastas
# ---------------------------------------------------------------------------
@router.post("/", response_model=SubastaOut, status_code=201)
def publicar_subasta(
    data: PublicarSubastaIn,
    service: AuctionService = Depends(get_service),
):
    try:
        return service.publicar_subasta(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/", response_model=List[SubastaOut])
def listar_subastas(service: AuctionService = Depends(get_service)):
    return service.listar_subastas()


@router.get("/{id_subasta}", response_model=SubastaOut)
def obtener_subasta(
    id_subasta: int,
    service: AuctionService = Depends(get_service),
):
    try:
        return service.obtener_subasta(id_subasta)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{id_subasta}/bids", response_model=PujaOut, status_code=201)
def pujar(
    id_subasta: int,
    data: PujaIn,
    service: AuctionService = Depends(get_service),
):
    try:
        return service.pujar(id_subasta, data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{id_subasta}/bids", response_model=List[PujaOut])
def listar_pujas(
    id_subasta: int,
    service: AuctionService = Depends(get_service),
):
    return service.listar_pujas(id_subasta)


@router.post("/{id_subasta}/buy", response_model=PujaOut)
def comprar_directo(
    id_subasta: int,
    data: CompraDirectaIn,
    service: AuctionService = Depends(get_service),
):
    try:
        return service.comprar_directo(id_subasta, data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{id_subasta}/close", response_model=Optional[PujaOut])
def cerrar_subasta(
    id_subasta: int,
    service: AuctionService = Depends(get_service),
):
    try:
        return service.cerrar_subasta(id_subasta)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
