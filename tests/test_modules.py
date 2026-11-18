"""Pruebas puras de los módulos auth, restaurant y payment.

No requieren PostgreSQL: validan entidades y reglas del modelo 2.1.
"""

from decimal import Decimal

import pytest

from src.modules.auth.domain.models import Jugador, Personaje
from src.modules.payment.domain.models import (
    Correo,
    EstadoCorreo,
    TipoTransaccion,
    Transaccion,
)
from src.modules.restaurant.domain.models import Inventario, Item


def test_jugador_no_guarda_oro():
    jugador = Jugador(nombre="Luis", email="luis@example.com")

    assert jugador.nombre == "Luis"
    assert not hasattr(jugador, "oro")


def test_personaje_valida_nivel_y_oro():
    personaje = Personaje(
        nombre="Luis",
        id_jugador=1,
        nivel=80,
        clase="Pícaro",
        oro=Decimal("2000.00"),
    )
    assert personaje.oro == Decimal("2000.00")

    with pytest.raises(ValueError):
        Personaje(nombre="Luis", id_jugador=1, nivel=0)

    with pytest.raises(ValueError):
        Personaje(
            nombre="Luis", id_jugador=1, oro=Decimal("-1")
        )


def test_item_e_inventario():
    item = Item(nombre="Hearthstone", rareza="comun")
    inventario = Inventario(id_personaje=1, id_item=1, cantidad=2)

    assert item.nombre == "Hearthstone"
    assert inventario.cantidad == 2

    with pytest.raises(ValueError):
        Inventario(id_personaje=1, id_item=1, cantidad=0)


def test_transaccion_usa_tipo_del_modelo():
    transaccion = Transaccion(
        id_subasta=1,
        id_comprador=2,
        monto=Decimal("30.00"),
        tipo=TipoTransaccion.PUJA_GANADORA,
    )

    assert transaccion.tipo.value == "puja_ganadora"
    assert TipoTransaccion.COMPRA_DIRECTA.value == "compra_directa"


def test_correo_estados_del_modelo():
    correo = Correo(
        id_destinatario=2,
        asunto="Subasta ganada: item 6",
        id_item=6,
        cantidad=1,
    )

    assert correo.estado == EstadoCorreo.PENDIENTE
    assert {estado.value for estado in EstadoCorreo} == {
        "pendiente",
        "leido",
        "cobrado",
        "devuelto",
    }
