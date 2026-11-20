"""Pruebas unitarias de las reglas de negocio del dominio de subastas."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.modules.auction.domain.models import (
    EstadoPuja,
    EstadoSubasta,
    Subasta,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_duracion_invalida():
    with pytest.raises(ValueError):
        Subasta(
            id_vendedor=1,
            id_item=1,
            precio_salida=Decimal("100"),
            duracion_horas=5,
        )


def test_puja_debe_superar_la_actual():
    subasta = Subasta(
        id_vendedor=1, id_item=1, precio_salida=Decimal("100")
    )
    with pytest.raises(ValueError):
        subasta.pujar(Decimal("100"), comprador=2)

    puja = subasta.pujar(Decimal("110"), comprador=2)
    assert puja.monto == Decimal("110")
    assert subasta.puja_actual == Decimal("110")


def test_puja_supera_la_anterior():
    subasta = Subasta(
        id_vendedor=1, id_item=1, precio_salida=Decimal("100")
    )
    primera = subasta.pujar(Decimal("110"), comprador=2)
    segunda = subasta.pujar(Decimal("120"), comprador=3)

    assert primera.estado == EstadoPuja.SUPERADA
    assert segunda.estado == EstadoPuja.ACTIVA
    assert subasta.puja_actual == Decimal("120")


def test_compra_directa_cierra_subasta():
    subasta = Subasta(
        id_vendedor=1,
        id_item=1,
        precio_salida=Decimal("100"),
        precio_compra_directa=Decimal("250"),
    )
    puja = subasta.comprar_directo(comprador=2)

    assert puja.monto == Decimal("250")
    assert puja.estado == EstadoPuja.GANADORA
    assert subasta.estado == EstadoSubasta.VENDIDA
    assert subasta.puja_actual == Decimal("250")


def test_puja_actual_refleja_compra_directa_con_pujas_previas():
    subasta = Subasta(
        id_vendedor=1,
        id_item=1,
        precio_salida=Decimal("100"),
        precio_compra_directa=Decimal("250"),
    )
    subasta.pujar(Decimal("150"), comprador=3)
    assert subasta.puja_actual == Decimal("150")

    subasta.comprar_directo(comprador=2)

    assert subasta.estado == EstadoSubasta.VENDIDA
    assert subasta.puja_actual == Decimal("250")


def test_compra_directa_no_disponible():
    subasta = Subasta(
        id_vendedor=1, id_item=1, precio_salida=Decimal("100")
    )
    with pytest.raises(ValueError):
        subasta.comprar_directo(comprador=2)


def test_deposito_y_comision():
    subasta = Subasta(
        id_vendedor=1, id_item=1, precio_salida=Decimal("100")
    )
    assert subasta.deposito == Decimal("5.00")

    subasta.pujar(Decimal("200"), comprador=2)
    assert subasta.comision == Decimal("10.00")


def test_cerrar_sin_pujas_expira():
    subasta = Subasta(
        id_vendedor=1,
        id_item=1,
        precio_salida=Decimal("100"),
        duracion_horas=2,
    )
    subasta.fecha_fin = _utcnow() - timedelta(hours=1)

    assert subasta.cerrar() is None
    assert subasta.estado == EstadoSubasta.EXPIRADA


def test_cerrar_con_pujas_gana_la_mas_alta():
    subasta = Subasta(
        id_vendedor=1,
        id_item=1,
        precio_salida=Decimal("100"),
        duracion_horas=2,
    )
    subasta.pujar(Decimal("110"), comprador=2)
    subasta.pujar(Decimal("120"), comprador=3)
    subasta.fecha_fin = _utcnow() - timedelta(hours=1)

    ganadora = subasta.cerrar()

    assert ganadora is not None
    assert ganadora.monto == Decimal("120")
    assert ganadora.id_comprador == 3
    assert subasta.estado == EstadoSubasta.VENDIDA
    assert subasta.puja_actual == Decimal("120")


def test_incremento_minimo_de_un_cobre():
    subasta = Subasta(
        id_vendedor=1, id_item=1, precio_salida=Decimal("100")
    )
    with pytest.raises(ValueError):
        subasta.pujar(Decimal("100.00"), comprador=2)

    puja = subasta.pujar(Decimal("100.01"), comprador=2)
    assert puja.monto == Decimal("100.01")


def test_ganador_actual_y_tiempo_restante():
    subasta = Subasta(
        id_vendedor=1,
        id_item=1,
        precio_salida=Decimal("100"),
        duracion_horas=2,
    )
    assert subasta.ganador_actual is None
    assert 0 < subasta.tiempo_restante <= 7200

    subasta.pujar(Decimal("110"), comprador=2)
    assert subasta.ganador_actual == 2

    subasta.fecha_fin = _utcnow() - timedelta(minutes=1)
    assert subasta.tiempo_restante == 0


def test_cancelar_subasta():
    subasta = Subasta(
        id_vendedor=1, id_item=1, precio_salida=Decimal("100")
    )
    subasta.cancelar()

    assert subasta.estado == EstadoSubasta.CANCELADA
    with pytest.raises(ValueError):
        subasta.cancelar()
