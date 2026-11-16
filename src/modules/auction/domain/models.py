"""Entidades y reglas de negocio puras del módulo de subastas.

Esta capa NO conoce SQLAlchemy, FastAPI ni PostgreSQL. Solo Python.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional


def _utcnow() -> datetime:
    """UTC sin zona horaria, compatible con TIMESTAMP de PostgreSQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class EstadoSubasta(str, Enum):
    ACTIVA = "activa"
    VENDIDA = "vendida"
    EXPIRADA = "expirada"
    CANCELADA = "cancelada"


class EstadoPuja(str, Enum):
    ACTIVA = "activa"
    SUPERADA = "superada"
    GANADORA = "ganadora"


@dataclass
class Puja:
    id_subasta: int
    id_comprador: int
    monto: Decimal
    estado: EstadoPuja = EstadoPuja.ACTIVA
    fecha: datetime = field(default_factory=_utcnow)
    id_puja: Optional[int] = None


@dataclass
class Subasta:
    """Entidad central del módulo.

    Reglas implementadas:
      - Duración permitida: 2, 8 o 24 horas.
      - Depósito del 5% del precio de salida al publicar.
      - Comisión del 5% sobre el monto final de la venta.
      - Una puja debe superar la puja actual.
      - La compra directa cierra la subasta inmediatamente.
      - Al cerrar, gana la puja más alta.
    """

    id_vendedor: int
    id_item: int
    precio_salida: Decimal
    duracion_horas: int = 24
    precio_compra_directa: Optional[Decimal] = None
    cantidad: int = 1
    estado: EstadoSubasta = EstadoSubasta.ACTIVA
    fecha_inicio: datetime = field(default_factory=_utcnow)
    fecha_fin: Optional[datetime] = None
    id_subasta: Optional[int] = None
    pujas: List[Puja] = field(default_factory=list)

    DEPOSITO_PORCENTAJE = Decimal("0.05")
    COMISION_PORCENTAJE = Decimal("0.05")

    def __post_init__(self):
        if self.duracion_horas not in (2, 8, 24):
            raise ValueError("La duración debe ser 2, 8 o 24 horas.")
        if self.fecha_fin is None:
            self.fecha_fin = self.fecha_inicio + timedelta(
                hours=self.duracion_horas
            )

    @property
    def puja_actual(self) -> Decimal:
        """Monto de referencia de la subasta.

        - Si está vendida, el monto de la puja ganadora (compra directa o
          cierre), para que la respuesta de la API no muestre el precio de
          salida como si no se hubiera vendido.
        - Si está activa, la puja activa más alta.
        - Si no hay pujas, el precio de salida.
        """
        if self.estado == EstadoSubasta.VENDIDA:
            ganadoras = [
                p.monto
                for p in self.pujas
                if p.estado == EstadoPuja.GANADORA
            ]
            if ganadoras:
                return max(ganadoras)

        activas = [
            p.monto for p in self.pujas if p.estado == EstadoPuja.ACTIVA
        ]
        return max(activas) if activas else self.precio_salida

    @property
    def deposito(self) -> Decimal:
        return (
            self.precio_salida * self.DEPOSITO_PORCENTAJE
        ).quantize(Decimal("0.01"))

    @property
    def comision(self) -> Decimal:
        return (self.puja_actual * self.COMISION_PORCENTAJE).quantize(
            Decimal("0.01")
        )

    def pujar(self, monto: Decimal, comprador: int) -> Puja:
        if self.estado != EstadoSubasta.ACTIVA:
            raise ValueError("La subasta no está activa.")
        if comprador == self.id_vendedor:
            raise ValueError(
                "El vendedor no puede pujar en su propia subasta."
            )
        if monto <= self.puja_actual:
            raise ValueError("La puja debe superar la puja actual.")
        for p in self.pujas:
            if p.estado == EstadoPuja.ACTIVA:
                p.estado = EstadoPuja.SUPERADA
        nueva = Puja(
            id_subasta=self.id_subasta or 0,
            id_comprador=comprador,
            monto=monto,
        )
        self.pujas.append(nueva)
        return nueva

    def comprar_directo(self, comprador: int) -> Puja:
        if self.estado != EstadoSubasta.ACTIVA:
            raise ValueError("La subasta no está activa.")
        if comprador == self.id_vendedor:
            raise ValueError(
                "El vendedor no puede comprar su propia subasta."
            )
        if self.precio_compra_directa is None:
            raise ValueError(
                "Esta subasta no tiene precio de compra directa."
            )
        compra = Puja(
            id_subasta=self.id_subasta or 0,
            id_comprador=comprador,
            monto=self.precio_compra_directa,
            estado=EstadoPuja.GANADORA,
        )
        self.pujas.append(compra)
        self.estado = EstadoSubasta.VENDIDA
        return compra

    def cerrar(self) -> Optional[Puja]:
        if self.estado != EstadoSubasta.ACTIVA:
            raise ValueError("La subasta no está activa.")
        if _utcnow() < self.fecha_fin:
            raise ValueError("La subasta todavía no ha terminado.")
        if not self.pujas:
            self.estado = EstadoSubasta.EXPIRADA
            return None
        ganadora = max(self.pujas, key=lambda p: p.monto)
        ganadora.estado = EstadoPuja.GANADORA
        self.estado = EstadoSubasta.VENDIDA
        return ganadora

    def expirar(self) -> None:
        if self.estado == EstadoSubasta.ACTIVA:
            self.estado = EstadoSubasta.EXPIRADA
