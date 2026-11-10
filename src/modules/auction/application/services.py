"""Casos de uso del módulo de subastas.

Orquesta el dominio y los repositorios. No conoce FastAPI ni SQL directo.
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
    FondosInsuficientes,
    ItemNoDisponible,
    PersonajeNoEncontrado,
    PujaInsuficiente,
    SubastaCerrada,
    SubastaNoEncontrada,
)
from src.modules.auction.domain.models import (
    Correo,
    EstadoPuja,
    EstadoSubasta,
    Puja,
    Subasta,
    TipoTransaccion,
    Transaccion,
)
from src.modules.auction.infrastructure.repository_impl import (
    CorreoRepositoryImpl,
    ItemRepositoryImpl,
    JugadorRepositoryImpl,
    PersonajeRepositoryImpl,
    PujaRepositoryImpl,
    SubastaRepositoryImpl,
    TransaccionRepositoryImpl,
)


class AuctionService:
    def __init__(self, session: Session):
        self.session = session
        self.jugadores = JugadorRepositoryImpl(session)
        self.personajes = PersonajeRepositoryImpl(session)
        self.items = ItemRepositoryImpl(session)
        self.subastas = SubastaRepositoryImpl(session)
        self.pujas = PujaRepositoryImpl(session)
        self.correos = CorreoRepositoryImpl(session)
        self.transacciones = TransaccionRepositoryImpl(session)

    # ------------------------------------------------------------------
    # Publicar
    # ------------------------------------------------------------------
    def publicar_subasta(self, data: PublicarSubastaIn) -> Subasta:
        vendedor = self.personajes.obtener(data.id_vendedor)
        if not vendedor:
            raise PersonajeNoEncontrado(
                f"El personaje {data.id_vendedor} no existe."
            )

        item = self.items.obtener(data.id_item)
        if not item:
            raise ItemNoDisponible(f"El item {data.id_item} no existe.")

        if not self.personajes.tiene_item(
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
        if not self.personajes.quitar_item(
            data.id_vendedor, data.id_item, data.cantidad
        ):
            raise ItemNoDisponible("No se pudo retirar el item del inventario.")

        # Cobrar depósito.
        vendedor.oro -= deposito
        self.personajes.actualizar_oro(vendedor.id_personaje, vendedor.oro)

        subasta = self.subastas.crear(subasta)
        self.subastas.crear_deposito(subasta.id_subasta, deposito)
        return subasta

    # ------------------------------------------------------------------
    # Pujar
    # ------------------------------------------------------------------
    def pujar(self, id_subasta: int, data: PujaIn) -> Puja:
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(f"La subasta {id_subasta} no existe.")
        if subasta.estado != EstadoSubasta.ACTIVA:
            raise SubastaCerrada("La subasta no está activa.")

        comprador = self.personajes.obtener(data.id_comprador)
        if not comprador:
            raise PersonajeNoEncontrado(
                f"El personaje {data.id_comprador} no existe."
            )

        if data.monto <= subasta.puja_actual:
            raise PujaInsuficiente(
                f"La puja debe superar {subasta.puja_actual}."
            )
        if comprador.oro < data.monto:
            raise FondosInsuficientes("El comprador no tiene oro suficiente.")

        # Reembolsar a los postores que quedan superados.
        for p in self.pujas.listar_por_subasta(id_subasta):
            if p.estado == EstadoPuja.ACTIVA:
                anterior = self.personajes.obtener(p.id_comprador)
                if anterior:
                    anterior.oro += p.monto
                    self.personajes.actualizar_oro(
                        anterior.id_personaje, anterior.oro
                    )
                self.pujas.actualizar_estado(
                    p.id_puja, EstadoPuja.SUPERADA.value
                )

        # Releer el comprador: si era el postor anterior, su oro cambió
        # con el reembolso y el objeto local quedaría desactualizado.
        comprador = self.personajes.obtener(data.id_comprador)
        if not comprador:
            raise PersonajeNoEncontrado(
                f"El personaje {data.id_comprador} no existe."
            )
        if comprador.oro < data.monto:
            raise FondosInsuficientes("El comprador no tiene oro suficiente.")

        # Retener el oro de la nueva puja.
        comprador.oro -= data.monto
        self.personajes.actualizar_oro(comprador.id_personaje, comprador.oro)

        nueva = Puja(
            id_subasta=id_subasta,
            id_comprador=data.id_comprador,
            monto=data.monto,
        )
        return self.pujas.crear(nueva)

    # ------------------------------------------------------------------
    # Compra directa
    # ------------------------------------------------------------------
    def comprar_directo(self, id_subasta: int, data: CompraDirectaIn) -> Puja:
        subasta = self.subastas.obtener(id_subasta)
        if not subasta:
            raise SubastaNoEncontrada(f"La subasta {id_subasta} no existe.")
        if subasta.estado != EstadoSubasta.ACTIVA:
            raise SubastaCerrada("La subasta no está activa.")
        if subasta.precio_compra_directa is None:
            raise CompraDirectaNoDisponible(
                "Esta subasta no tiene precio de compra directa."
            )

        comprador = self.personajes.obtener(data.id_comprador)
        if not comprador:
            raise PersonajeNoEncontrado(
                f"El personaje {data.id_comprador} no existe."
            )
        if comprador.oro < subasta.precio_compra_directa:
            raise FondosInsuficientes("El comprador no tiene oro suficiente.")

        # Reembolsar pujas activas.
        for p in self.pujas.listar_por_subasta(id_subasta):
            if p.estado == EstadoPuja.ACTIVA:
                anterior = self.personajes.obtener(p.id_comprador)
                if anterior:
                    anterior.oro += p.monto
                    self.personajes.actualizar_oro(
                        anterior.id_personaje, anterior.oro
                    )
                self.pujas.actualizar_estado(
                    p.id_puja, EstadoPuja.SUPERADA.value
                )

        # Releer el comprador: si era el postor anterior, su oro cambió
        # con el reembolso y el objeto local quedaría desactualizado.
        comprador = self.personajes.obtener(data.id_comprador)
        if not comprador:
            raise PersonajeNoEncontrado(
                f"El personaje {data.id_comprador} no existe."
            )
        if comprador.oro < subasta.precio_compra_directa:
            raise FondosInsuficientes("El comprador no tiene oro suficiente.")

        monto = subasta.precio_compra_directa

        # Cobrar al comprador.
        comprador.oro -= monto
        self.personajes.actualizar_oro(comprador.id_personaje, comprador.oro)

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

        self.correos.crear(
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
            raise SubastaNoEncontrada(f"La subasta {id_subasta} no existe.")
        if subasta.estado != EstadoSubasta.ACTIVA:
            raise SubastaCerrada("La subasta no está activa.")
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
        if ahora < subasta.fecha_fin:
            raise ValueError("La subasta todavía no ha terminado.")

        pujas = self.pujas.listar_por_subasta(id_subasta)

        if not pujas:
            subasta.estado = EstadoSubasta.EXPIRADA
            self.subastas.actualizar(subasta)
            self.correos.crear(
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
            if p.id_puja != ganadora.id_puja and p.estado == EstadoPuja.ACTIVA:
                p.estado = EstadoPuja.SUPERADA
                anterior = self.personajes.obtener(p.id_comprador)
                if anterior:
                    anterior.oro += p.monto
                    self.personajes.actualizar_oro(
                        anterior.id_personaje, anterior.oro
                    )
                self.pujas.actualizar_estado(
                    p.id_puja, EstadoPuja.SUPERADA.value
                )

        subasta.estado = EstadoSubasta.VENDIDA
        self.subastas.actualizar(subasta)

        self._liquidar_venta(
            subasta=subasta,
            id_comprador=ganadora.id_comprador,
            monto=ganadora.monto,
            tipo=TipoTransaccion.PUJA,
        )

        self.correos.crear(
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
            raise SubastaNoEncontrada(f"La subasta {id_subasta} no existe.")
        return subasta

    def listar_pujas(self, id_subasta: int) -> List[Puja]:
        return self.pujas.listar_por_subasta(id_subasta)

    def listar_correo(self, id_personaje: int) -> List[Correo]:
        return self.correos.listar_por_destinatario(id_personaje)

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
        vendedor = self.personajes.obtener(subasta.id_vendedor)
        if vendedor:
            vendedor.oro += monto - comision
            self.personajes.actualizar_oro(
                vendedor.id_personaje, vendedor.oro
            )

        self.subastas.crear_comision(
            subasta.id_subasta,
            Subasta.COMISION_PORCENTAJE * 100,
            comision,
        )
        self.transacciones.crear(
            Transaccion(
                id_subasta=subasta.id_subasta,
                id_comprador=id_comprador,
                id_vendedor=subasta.id_vendedor,
                monto=monto,
                tipo=tipo,
            )
        )
