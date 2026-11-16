"""Capa de presentación del módulo inventory."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.inventory.application.services import InventoryService
from src.modules.inventory.presentation.dtos import InventarioOut, ItemOut

router = APIRouter(prefix="/inventory", tags=["Inventario"])


def get_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(db)


@router.get("/items", response_model=List[ItemOut])
def listar_items(service: InventoryService = Depends(get_service)):
    return service.listar_items()


@router.get(
    "/characters/{id_personaje}",
    response_model=List[InventarioOut],
)
def listar_inventario(
    id_personaje: int,
    service: InventoryService = Depends(get_service),
):
    return service.listar_inventario(id_personaje)
