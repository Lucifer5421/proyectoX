"""Casos de uso del módulo auction (subastas).

Orquesta los módulos auth (personajes/oro), inventory (ítems), finance
(depósito, comisión y transacción) y mail (entrega por correo). No conoce
FastAPI ni SQL directo.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from src.modules.auction.application.dtos import (
    CompraDirectaIn,
    PublicarSubastaIn,
    PujaIn,
)
from src.modules.auction.domain.exceptions import (
    CompraDirectaNoDisponible,
    PujaInsuficiente,
    SubastaCerrada,
    SubastaNoEncontrada,
)
from src.modules.auction.domain.models import (
    EstadoPuja,
    EstadoSubasta,
    Puja,
    Subasta,
)
from src.modules.auction.infrastructure.repository_impl import (
    PujaRepositoryImpl,
    SubastaRepositoryImpl,
)
from src.modules.auth.application.services import AuthService
from src.modules.auth.domain.exceptions import FondosInsuficientes
from src.modules.finance.application.services import FinanceService
from src.modules.finance.domain.models import TipoTransaccion
from src.modules.inventory.application.services import InventoryService
from src.modules.inventory.domain.exceptions import ItemNoDisponible
from src.modules.mail.application.services import MailService
from src.modules.mail.domain.models import Correo


class AuctionService:
    def __init__(self, session: Session):
        self.session = session
        self.auth = AuthService(session)
        self.inventory = InventoryService(session)
        self.finance = FinanceService(session)
        self.mail = MailService(session)
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
        minimo = subasta.puja_actual + subasta.INCREMENTO_MINIMO
        if data.monto < minimo:
            raise PujaInsuficiente(
                f"La puja debe ser al menos {minimo}."
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

        self.mail.crear_correo(
            Correo(
                id_destinatario=data.id_comprador,
                asunto=(
                    f"Compra directa: item {subasta.id_item} "
                    f"— pagado {monto}"
                ),
                id_item=subasta.id_item,
                cantidad=subasta.cantidad,
                oro=monto,
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
            self.mail.crear_correo(
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

        self.mail.crear_correo(
            Correo(
                id_destinatario=ganadora.id_comprador,
                asunto=(
                    f"Subasta ganada: item {subasta.id_item} "
                    f"— pagado {ganadora.monto}"
                ),
                id_item=subasta.id_item,
                cantidad=subasta.cantidad,
                oro=ganadora.monto,
            )
        )
        return ganadora

    # ------------------------------------------------------------------
    # Cancelación
    # ------------------------------------------------------------------
    def cancelar_subasta(
        self, id_subasta: int, id_vendedor: int
    ) -> Subasta:
        """Cancela una subasta propia, reembolsa y devuelve el ítem."""
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(
                f"La subasta {id_subasta} no existe."
            )
        if subasta.id_vendedor != id_vendedor:
            raise ValueError("Solo el vendedor puede cancelar la subasta.")

        subasta.cancelar()
        self.subastas.actualizar(subasta)

        for puja in self.pujas.listar_por_subasta(id_subasta):
            if puja.estado == EstadoPuja.ACTIVA:
                self.auth.acreditar_oro(puja.id_comprador, puja.monto)
                self.pujas.actualizar_estado(
                    puja.id_puja, EstadoPuja.SUPERADA.value
                )

        self.inventory.agregar_item(
            id_vendedor, subasta.id_item, subasta.cantidad
        )
        return subasta

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def listar_subastas(
        self,
        q: Optional[str] = None,
        id_vendedor: Optional[int] = None,
        id_comprador: Optional[int] = None,
        id_personaje: Optional[int] = None,
        usable: bool = False,
        sort: Optional[str] = None,
    ) -> List[Subasta]:
        """Lista activas con búsqueda, filtros y orden de la guía de WoW."""
        subastas = self.subastas.listar_activas()
        items = {
            item.id_item: item
            for item in self.inventory.listar_items()
        }

        if q:
            texto = q.casefold()
            subastas = [
                s
                for s in subastas
                if texto in items[s.id_item].nombre.casefold()
            ]

        if id_vendedor is not None:
            subastas = [
                s for s in subastas if s.id_vendedor == id_vendedor
            ]

        if id_comprador is not None:
            subastas = [
                s
                for s in subastas
                if any(p.id_comprador == id_comprador for p in s.pujas)
            ]

        if usable:
            if id_personaje is None:
                raise ValueError(
                    "id_personaje es obligatorio para filtrar por utilizables."
                )
            nivel = self.auth.obtener_personaje(id_personaje).nivel
            subastas = [
                s
                for s in subastas
                if items[s.id_item].nivel_requerido <= nivel
            ]

        claves = {
            "precio_asc": lambda s: s.puja_actual,
            "precio_desc": lambda s: -s.puja_actual,
            "rareza": lambda s: items[s.id_item].rareza,
            "nivel": lambda s: items[s.id_item].nivel_requerido,
            "tiempo": lambda s: s.fecha_fin,
            "vendedor": lambda s: s.id_vendedor,
        }
        if sort:
            if sort not in claves:
                raise ValueError(f"Orden desconocido: {sort}")
            subastas = sorted(subastas, key=claves[sort])

        return subastas

    def obtener_subasta(self, id_subasta: int) -> Subasta:
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(
                f"La subasta {id_subasta} no existe."
            )
        return subasta

    def listar_pujas(
        self, id_subasta: int, id_comprador: Optional[int] = None
    ) -> List[Puja]:
        pujas = self.pujas.listar_por_subasta(id_subasta)
        if id_comprador is not None:
            pujas = [
                p
                for p in pujas
                if p.id_comprador == id_comprador
            ]
        return pujas

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
