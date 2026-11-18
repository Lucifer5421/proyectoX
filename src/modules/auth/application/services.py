"""Casos de uso del módulo auth.

Gestiona cuentas, personajes y el oro de los personajes. No conoce FastAPI.
"""

from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from src.modules.auth.domain.exceptions import (
    FondosInsuficientes,
    JugadorNoEncontrado,
    PersonajeNoEncontrado,
)
from src.modules.auth.domain.models import Jugador, Personaje
from src.modules.auth.infrastructure.repositories_impl import (
    JugadorRepositoryImpl,
    PersonajeRepositoryImpl,
)


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.jugadores = JugadorRepositoryImpl(session)
        self.personajes = PersonajeRepositoryImpl(session)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def obtener_jugador(self, id_jugador: int) -> Jugador:
        jugador = self.jugadores.obtener(id_jugador)
        if not jugador:
            raise JugadorNoEncontrado(
                f"El jugador {id_jugador} no existe."
            )
        return jugador

    def listar_jugadores(self) -> List[Jugador]:
        return self.jugadores.listar()

    def obtener_personaje(self, id_personaje: int) -> Personaje:
        personaje = self.personajes.obtener(id_personaje)
        if not personaje:
            raise PersonajeNoEncontrado(
                f"El personaje {id_personaje} no existe."
            )
        return personaje

    def listar_personajes(self) -> List[Personaje]:
        return self.personajes.listar()

    # ------------------------------------------------------------------
    # Oro del personaje
    # ------------------------------------------------------------------
    def actualizar_oro(self, id_personaje: int, oro: Decimal) -> None:
        self.personajes.actualizar_oro(id_personaje, oro)

    def debitar_oro(self, id_personaje: int, monto: Decimal) -> Personaje:
        personaje = self.obtener_personaje(id_personaje)
        if personaje.oro < monto:
            raise FondosInsuficientes(
                "El personaje no tiene oro suficiente."
            )
        personaje.oro -= monto
        self.personajes.actualizar_oro(
            personaje.id_personaje, personaje.oro
        )
        return personaje

    def acreditar_oro(self, id_personaje: int, monto: Decimal) -> Personaje:
        personaje = self.obtener_personaje(id_personaje)
        personaje.oro += monto
        self.personajes.actualizar_oro(
            personaje.id_personaje, personaje.oro
        )
        return personaje
