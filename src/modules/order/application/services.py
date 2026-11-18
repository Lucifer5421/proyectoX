"""Casos de uso del módulo de subastas.

Orquesta los módulos auth (personajes/oro), restaurant (ítems) y payment
(depósito, comisión, transacción y correo). No conoce FastAPI ni SQL directo.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.order.application.dtos import (
    CompraDirectaIn,
    PublicarSubastaIn,
    PujaIn,
)
from src.modules.order.domain.exceptions import (
    CompraDirectaNoDisponible,
    PujaInsuficiente,
    SubastaCerrada,
    SubastaNoEncontrada,
)
from src.modules.order.domain.models import (
    EstadoPuja,
    EstadoSubasta,
    Puja,
    Subasta,
)
from src.modules.order.infrastructure.repository_impl import (
    PujaRepositoryImpl,
    SubastaRepositoryImpl,
)
from src.modules.auth.application.services import AuthService
from src.modules.auth.domain.exceptions import FondosInsuficientes
from src.modules.payment.application.services import FinanceService
from src.modules.payment.domain.models import Correo, TipoTransaccion
from src.modules.restaurant.application.services import InventoryService
from src.modules.restaurant.domain.exceptions import ItemNoDisponible


class AuctionService:
    def __init__(self, session: Session):
        self.session = session
        self.auth = AuthService(session)
        self.inventory = InventoryService(session)
        self.finance = FinanceService(session)
        self.subastas = SubastaRepositoryImpl(session)
        self.pujas = PujaRepositoryImpl(session)

    # ------------------------------------------------------------------
    # Publicar
    # ------------------------------------------------------------------
    def publicar_subasta(self, data: PublicarSubastaIn) -> Subasta:
        vendedor = self.auth.obtener_personaje(data.id_vendedor)
        self.inventory.obtener_item(data.id_item)

        if not self.inventory.tiene_item(
            data.id_vendedor, data.id_item, data.cantidad
        ):
            raise ItemNoDisponible(
                "El vendedor no tiene la cantidad solicitada de ese item."
            )

        subasta = Subasta(
            id_vendedor=data.id_vendedor,
            id_item=data.id_item,
            cantidad=data.cantidad,
            precio_salida=data.precio_salida,
            precio_compra_directa=data.precio_compra_directa,
            duracion_horas=data.duracion_horas,
        )

        deposito = subasta.deposito
        if vendedor.oro < deposito:
            raise FondosInsuficientes(
                f"El vendedor necesita {deposito} de oro para el depósito."
            )

        # El item queda retenido por la casa de subastas.
        if not self.inventory.quitar_item(
            data.id_vendedor, data.id_item, data.cantidad
        ):
            raise ItemNoDisponible(
                "No se pudo retirar el item del inventario."
            )

        # Cobrar depósito.
        self.auth.debitar_oro(data.id_vendedor, deposito)

        subasta = self.subastas.crear(subasta)
        self.finance.crear_deposito(subasta.id_subasta, deposito)
        return subasta

    # ------------------------------------------------------------------
    # Pujar
    # ------------------------------------------------------------------
    def pujar(self, id_subasta: int, data: PujaIn) -> Puja:
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(
                f"La subasta {id_subasta} no existe."
            )
        if subasta.estado != EstadoSubasta.ACTIVA:
            raise SubastaCerrada("La subasta no está activa.")

        comprador = self.auth.obtener_personaje(data.id_comprador)
        if data.monto <= subasta.puja_actual:
            raise PujaInsuficiente(
                f"La puja debe superar {subasta.puja_actual}."
            )

        pujas_activas = self.pujas.listar_por_subasta(id_subasta)
        # Si el comprador ya tenía una puja activa, ese oro está retenido y
        # se le devolverá antes de cobrar la nueva puja. Se suma al saldo
        # disponible para no rechazar una subida de su propia puja.
        reembolso_propio = sum(
            (
                p.monto
                for p in pujas_activas
                if p.estado == EstadoPuja.ACTIVA
                and p.id_comprador == data.id_comprador
            ),
            Decimal("0"),
        )
        if comprador.oro + reembolso_propio < data.monto:
            raise FondosInsuficientes(
                "El comprador no tiene oro suficiente."
            )

        # Reembolsar a los postores que quedan superados.
        for p in pujas_activas:
            if p.estado == EstadoPuja.ACTIVA:
                self.auth.acreditar_oro(p.id_comprador, p.monto)
                self.pujas.actualizar_estado(
                    p.id_puja, EstadoPuja.SUPERADA.value
                )

        # Releer el comprador: si era el postor anterior, su oro cambió
        # con el reembolso y el objeto local quedaría desactualizado.
        comprador = self.auth.obtener_personaje(data.id_comprador)
        if comprador.oro < data.monto:
            raise FondosInsuficientes(
                "El comprador no tiene oro suficiente."
            )

        # Retener el oro de la nueva puja.
        self.auth.debitar_oro(data.id_comprador, data.monto)

        nueva = Puja(
            id_subasta=id_subasta,
            id_comprador=data.id_comprador,
            monto=data.monto,
        )
        return self.pujas.crear(nueva)

    # ------------------------------------------------------------------
    # Compra directa
    # ------------------------------------------------------------------
    def comprar_directo(
        self, id_subasta: int, data: CompraDirectaIn
    ) -> Puja:
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(
                f"La subasta {id_subasta} no existe."
            )
        if subasta.estado != EstadoSubasta.ACTIVA:
            raise SubastaCerrada("La subasta no está activa.")
        if subasta.precio_compra_directa is None:
            raise CompraDirectaNoDisponible(
                "Esta subasta no tiene precio de compra directa."
            )

        comprador = self.auth.obtener_personaje(data.id_comprador)
        pujas_activas = self.pujas.listar_por_subasta(id_subasta)
        reembolso_propio = sum(
            (
                p.monto
                for p in pujas_activas
                if p.estado == EstadoPuja.ACTIVA
                and p.id_comprador == data.id_comprador
            ),
            Decimal("0"),
        )
        if (
            comprador.oro + reembolso_propio
            < subasta.precio_compra_directa
        ):
            raise FondosInsuficientes(
                "El comprador no tiene oro suficiente."
            )

        # Reembolsar pujas activas.
        for p in pujas_activas:
            if p.estado == EstadoPuja.ACTIVA:
                self.auth.acreditar_oro(p.id_comprador, p.monto)
                self.pujas.actualizar_estado(
                    p.id_puja, EstadoPuja.SUPERADA.value
                )

        # Releer el comprador por el posible reembolso.
        comprador = self.auth.obtener_personaje(data.id_comprador)
        if comprador.oro < subasta.precio_compra_directa:
            raise FondosInsuficientes(
                "El comprador no tiene oro suficiente."
            )

        monto = subasta.precio_compra_directa

        # Cobrar al comprador.
        self.auth.debitar_oro(data.id_comprador, monto)

        # Cerrar subasta.
        subasta.estado = EstadoSubasta.VENDIDA
        self.subastas.actualizar(subasta)

        puja = Puja(
            id_subasta=id_subasta,
            id_comprador=data.id_comprador,
            monto=monto,
            estado=EstadoPuja.GANADORA,
        )
        puja = self.pujas.crear(puja)

        self._liquidar_venta(
            subasta=subasta,
            id_comprador=data.id_comprador,
            monto=monto,
            tipo=TipoTransaccion.COMPRA_DIRECTA,
        )

        self.finance.crear_correo(
            Correo(
                id_destinatario=data.id_comprador,
                asunto=f"Compra directa: item {subasta.id_item}",
                id_item=subasta.id_item,
                cantidad=subasta.cantidad,
            )
        )
        return puja

    # ------------------------------------------------------------------
    # Cierre / expiración
    # ------------------------------------------------------------------
    def cerrar_subasta(self, id_subasta: int) -> Optional[Puja]:
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(
                f"La subasta {id_subasta} no existe."
            )
        if subasta.estado != EstadoSubasta.ACTIVA:
            raise SubastaCerrada("La subasta no está activa.")
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        if ahora < subasta.fecha_fin:
            raise ValueError("La subasta todavía no ha terminado.")

        pujas = self.pujas.listar_por_subasta(id_subasta)

        if not pujas:
            subasta.estado = EstadoSubasta.EXPIRADA
            self.subastas.actualizar(subasta)
            self.finance.crear_correo(
                Correo(
                    id_destinatario=subasta.id_vendedor,
                    asunto=f"Subasta expirada: item {subasta.id_item}",
                    id_item=subasta.id_item,
                    cantidad=subasta.cantidad,
                )
            )
            return None

        ganadora = max(pujas, key=lambda p: p.monto)
        ganadora.estado = EstadoPuja.GANADORA
        self.pujas.actualizar_estado(
            ganadora.id_puja, EstadoPuja.GANADORA.value
        )

        # Reembolsar cualquier puja activa que no sea la ganadora.
        for p in pujas:
            if (
                p.id_puja != ganadora.id_puja
                and p.estado == EstadoPuja.ACTIVA
            ):
                p.estado = EstadoPuja.SUPERADA
                self.auth.acreditar_oro(p.id_comprador, p.monto)
                self.pujas.actualizar_estado(
                    p.id_puja, EstadoPuja.SUPERADA.value
                )

        subasta.estado = EstadoSubasta.VENDIDA
        self.subastas.actualizar(subasta)

        self._liquidar_venta(
            subasta=subasta,
            id_comprador=ganadora.id_comprador,
            monto=ganadora.monto,
            tipo=TipoTransaccion.PUJA_GANADORA,
        )

        self.finance.crear_correo(
            Correo(
                id_destinatario=ganadora.id_comprador,
                asunto=f"Subasta ganada: item {subasta.id_item}",
                id_item=subasta.id_item,
                cantidad=subasta.cantidad,
            )
        )
        return ganadora

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def listar_subastas(self) -> List[Subasta]:
        return self.subastas.listar_activas()

    def obtener_subasta(self, id_subasta: int) -> Subasta:
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(
                f"La subasta {id_subasta} no existe."
            )
        return subasta

    def listar_pujas(self, id_subasta: int) -> List[Puja]:
        return self.pujas.listar_por_subasta(id_subasta)

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------
    def _liquidar_venta(
        self,
        subasta: Subasta,
        id_comprador: int,
        monto: Decimal,
        tipo: TipoTransaccion,
    ) -> None:
        """Paga al vendedor, registra comisión y transacción.

        El oro del comprador ya fue retenido al pujar/comprar.
        """
        comision = (monto * Subasta.COMISION_PORCENTAJE).quantize(
            Decimal("0.01")
        )
        self.auth.acreditar_oro(
            subasta.id_vendedor, monto - comision
        )

        self.finance.crear_comision(
            subasta.id_subasta,
            Subasta.COMISION_PORCENTAJE * 100,
            comision,
        )
        self.finance.registrar_transaccion(
            id_subasta=subasta.id_subasta,
            id_comprador=id_comprador,
            monto=monto,
            tipo=tipo,
        )
