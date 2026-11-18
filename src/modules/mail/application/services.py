"""Casos de uso del módulo mail.

Gestiona la entrega de ítems y oro al destinatario de una subasta. No
conoce FastAPI: el router solo traduce HTTP a estas operaciones.
"""

from typing import List

from sqlalchemy.orm import Session

from src.modules.mail.domain.models import Correo
from src.modules.mail.infrastructure.repository_impl import (
    CorreoRepositoryImpl,
)


class MailService:
    """Servicio de aplicación del correo del personaje."""

    def __init__(self, session: Session):
        self.session = session
        self.correos = CorreoRepositoryImpl(session)

    def crear_correo(self, correo: Correo) -> Correo:
        """Registra un correo pendiente de entrega."""
        return self.correos.crear(correo)

    def listar_correo(self, id_personaje: int) -> List[Correo]:
        """Devuelve el correo de un personaje."""
        return self.correos.listar_por_destinatario(id_personaje)
