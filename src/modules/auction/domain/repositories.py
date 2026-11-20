# ============================================================================
# MÓDULO: auction  |  CAPA: domain  |  ARCHIVO: repositories.py
# QUÉ HACE: Contratos de repositorio del módulo auction (subastas).
# DETALLE: clases: SubastaRepository, PujaRepository
# ============================================================================
"""Contratos de repositorio del módulo auction (subastas)."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.auction.domain.models import Puja, Subasta


class SubastaRepository(ABC):
    @abstractmethod
    def crear(self, subasta: Subasta) -> Subasta:
        ...

    @abstractmethod
    def obtener(self, id_subasta: int) -> Optional[Subasta]:
        ...

    @abstractmethod
    def listar_activas(self) -> List[Subasta]:
        ...

    @abstractmethod
    def actualizar(self, subasta: Subasta) -> Subasta:
        ...


class PujaRepository(ABC):
    @abstractmethod
    def crear(self, puja: Puja) -> Puja:
        ...

    @abstractmethod
    def listar_por_subasta(self, id_subasta: int) -> List[Puja]:
        ...

    @abstractmethod
    def actualizar_estado(self, id_puja: int, estado: str) -> None:
        ...
