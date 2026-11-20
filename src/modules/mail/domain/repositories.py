# ============================================================================
# MÓDULO: mail  |  CAPA: domain  |  ARCHIVO: repositories.py
# QUÉ HACE: Contratos de repositorio del módulo mail.
# DETALLE: clases: CorreoRepository
# ============================================================================
"""Contratos de repositorio del módulo mail."""

from abc import ABC, abstractmethod
from typing import List

from src.modules.mail.domain.models import Correo


class CorreoRepository(ABC):
    """Contrato de persistencia para los correos del personaje."""

    @abstractmethod
    def crear(self, correo: Correo) -> Correo:
        """Persiste un correo nuevo y devuelve la entidad con su ID."""
        ...

    @abstractmethod
    def listar_por_destinatario(self, id_destinatario: int) -> List[Correo]:
        """Devuelve el correo de un personaje, del más reciente al más viejo."""
        ...
