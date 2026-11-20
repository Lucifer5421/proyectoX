# ============================================================================
# MÓDULO: auth  |  CAPA: domain  |  ARCHIVO: repositories.py
# QUÉ HACE: Contratos de repositorio del módulo auth.
# DETALLE: clases: JugadorRepository, PersonajeRepository
# ============================================================================
"""Contratos de repositorio del módulo auth."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from src.modules.auth.domain.models import Jugador, Personaje


class JugadorRepository(ABC):
    @abstractmethod
    def obtener(self, id_jugador: int) -> Optional[Jugador]:
        ...

    @abstractmethod
    def listar(self) -> List[Jugador]:
        ...


class PersonajeRepository(ABC):
    @abstractmethod
    def obtener(self, id_personaje: int) -> Optional[Personaje]:
        ...

    @abstractmethod
    def listar(self) -> List[Personaje]:
        ...

    @abstractmethod
    def actualizar_oro(self, id_personaje: int, oro: Decimal) -> None:
        ...
