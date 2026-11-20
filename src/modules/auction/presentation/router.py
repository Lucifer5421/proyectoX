"""Capa de presentación (API REST) del módulo de subastas."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.auction.application.services import AuctionService
from src.modules.auction.application.dtos import (
    CancelarIn,
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
def listar_subastas(
    q: Optional[str] = None,
    id_vendedor: Optional[int] = None,
    id_comprador: Optional[int] = None,
    id_personaje: Optional[int] = None,
    usable: bool = False,
    sort: Optional[str] = None,
    service: AuctionService = Depends(get_service),
):
    try:
        return service.listar_subastas(
            q=q,
            id_vendedor=id_vendedor,
            id_comprador=id_comprador,
            id_personaje=id_personaje,
            usable=usable,
            sort=sort,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
    id_comprador: Optional[int] = None,
    service: AuctionService = Depends(get_service),
):
    return service.listar_pujas(id_subasta, id_comprador)


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


@router.post("/{id_subasta}/cancel", response_model=SubastaOut)
def cancelar_subasta(
    id_subasta: int,
    data: CancelarIn,
    service: AuctionService = Depends(get_service),
):
    try:
        return service.cancelar_subasta(id_subasta, data.id_vendedor)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
