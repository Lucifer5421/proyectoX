"""Comprueba la estructura modular y el DDL del modelo lógico 2.1.

No necesita base de datos: valida la presencia de archivos, los nombres de
los módulos, el orden de importación y que `init.sql` sea DDL puro.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Módulos del dominio de subastas, alineados con modelo_subastas(2.1).drawio.
MODULOS = ("auth", "inventory", "auction", "finance", "mail")
MODULOS_CON_API = ("auth", "inventory", "auction", "mail")
CAPAS_COMUNES = (
    "application/services.py",
    "domain/exceptions.py",
    "domain/models.py",
    "domain/repositories.py",
    "infrastructure/external_adapters.py",
    "infrastructure/models_db.py",
    "infrastructure/repository_impl.py",
)
CAPAS_CON_API = (
    "application/dtos.py",
    "presentation/router.py",
)
TXT_AUTH = (
    "application/casos_uso-orquestacion.txt",
    "domain/reglas_negocio.txt",
    "infrastructure/implementacion_tecnica.txt",
    "presentation/capa_exposicion.txt",
)

# Tabla del modelo 2.1 -> módulo responsable.
TABLAS_POR_MODULO = {
    "auth": ("jugador", "personaje"),
    "inventory": ("item", "inventario"),
    "auction": ("subasta", "puja"),
    "finance": ("deposito", "comision", "transaccion"),
    "mail": ("correo",),
}


def test_init_sql_esta_en_la_raiz():
    assert (RAIZ / "init.sql").is_file()


def test_modulos_del_modelo_2_1_existen():
    modulos = RAIZ / "src" / "modules"
    for modulo in MODULOS:
        assert (modulos / modulo).is_dir(), f"Falta el módulo {modulo}"


def test_cada_modulo_tiene_las_capas_comunes():
    for modulo in MODULOS:
        base = RAIZ / "src" / "modules" / modulo
        for capa in CAPAS_COMUNES:
            assert (base / capa).is_file(), f"Falta {modulo}/{capa}"


def test_modulos_con_api_tienen_dtos_y_router():
    for modulo in MODULOS_CON_API:
        base = RAIZ / "src" / "modules" / modulo
        for capa in CAPAS_CON_API:
            assert (base / capa).is_file(), f"Falta {modulo}/{capa}"


def test_finance_es_interno_y_no_expone_api():
    base = RAIZ / "src" / "modules" / "finance"
    assert not (base / "presentation").exists()
    assert not (base / "application" / "dtos.py").exists()


def test_auth_tiene_los_cuatro_txt():
    base = RAIZ / "src" / "modules" / "auth"
    for archivo in TXT_AUTH:
        assert (base / archivo).is_file(), f"Falta auth/{archivo}"


def test_solo_auth_tiene_los_txt():
    for modulo in MODULOS:
        if modulo == "auth":
            continue
        base = RAIZ / "src" / "modules" / modulo
        for archivo in TXT_AUTH:
            assert not (base / archivo).exists(), (
                f"{modulo}/{archivo} no pertenece a este proyecto"
            )


def test_init_py_solo_en_la_raiz_de_los_modulos_correctos():
    assert not (RAIZ / "src" / "__init__.py").exists()
    assert not (RAIZ / "src" / "core" / "__init__.py").exists()
    assert not (RAIZ / "src" / "modules" / "__init__.py").exists()
    assert not (
        RAIZ / "src" / "modules" / "auth" / "__init__.py"
    ).exists()

    for modulo in ("inventory", "auction", "finance", "mail"):
        base = RAIZ / "src" / "modules" / modulo
        assert (base / "__init__.py").is_file()

    for modulo in MODULOS:
        base = RAIZ / "src" / "modules" / modulo
        for capa in (
            "application",
            "domain",
            "infrastructure",
            "presentation",
        ):
            assert not (base / capa / "__init__.py").exists()


def test_no_quedan_modulos_ni_archivos_heredados():
    modulos = RAIZ / "src" / "modules"
    for viejo in ("restaurant", "order", "payment", "tracking"):
        assert not (modulos / viejo).exists(), f"Sobra el módulo {viejo}"

    for modulo in MODULOS:
        base = modulos / modulo
        assert not (base / "models.py").exists()
        assert not (base / "services.py").exists()
        assert not (base / "application" / "datos.py").exists()
        assert not (base / "presentation" / "schemas.py").exists()
        assert not (base / "presentation" / "routers.py").exists()
        assert not (
            base / "infrastructure" / "repositories_impl.py"
        ).exists()
        assert not (
            base / "infrastructure" / "external_adapter.py"
        ).exists()


def test_main_importa_modelos_en_orden_de_llaves_foraneas():
    main = (RAIZ / "src" / "main.py").read_text(encoding="utf-8")
    orden = ("auth", "inventory", "auction", "finance", "mail")
    posiciones = [
        main.index(f"src.modules.{modulo}.infrastructure.models_db")
        for modulo in orden
    ]
    assert posiciones == sorted(posiciones)


def test_main_registra_los_modulos_con_api():
    main = (RAIZ / "src" / "main.py").read_text(encoding="utf-8")
    for modulo in MODULOS_CON_API:
        assert f"src.modules.{modulo}.presentation.router" in main
    assert "src.modules.finance.presentation.router" not in main


def test_init_sql_es_ddl_puro():
    contenido = (RAIZ / "init.sql").read_text(encoding="utf-8")
    sentencias_dml = re.findall(
        r"(?im)^\s*(INSERT|UPDATE|DELETE|SELECT)\b", contenido
    )
    assert not sentencias_dml, (
        "init.sql no debe contener DML: "
        f"{sentencias_dml}"
    )


def test_init_sql_y_01_schema_sql_coinciden():
    init = (RAIZ / "init.sql").read_text(encoding="utf-8")
    schema = (RAIZ / "sql" / "01_schema.sql").read_text(encoding="utf-8")
    assert init == schema


def test_init_sql_crea_las_diez_tablas_del_modelo_2_1():
    contenido = (RAIZ / "init.sql").read_text(encoding="utf-8").lower()
    tablas = [
        tabla
        for modulo in TABLAS_POR_MODULO.values()
        for tabla in modulo
    ]
    assert len(tablas) == 10
    for tabla in tablas:
        assert re.search(
            rf"create table if not exists {tabla}\b", contenido
        ), f"Falta la tabla {tabla}"


def test_init_sql_comenta_el_modulo_de_cada_tabla():
    contenido = (RAIZ / "init.sql").read_text(encoding="utf-8")
    for modulo, tablas in TABLAS_POR_MODULO.items():
        assert f"MÓDULO {modulo}" in contenido, (
            f"Falta el bloque del módulo {modulo}"
        )
        for tabla in tablas:
            assert f"{modulo} · {tabla.upper()}" in contenido, (
                f"Falta el comentario de {modulo} · {tabla}"
            )


def test_dominio_no_conoce_infraestructura():
    for modulo in MODULOS:
        base = RAIZ / "src" / "modules" / modulo / "domain"
        for archivo in base.glob("*.py"):
            texto = archivo.read_text(encoding="utf-8")
            for prohibido in ("sqlalchemy", "fastapi", "psycopg"):
                assert not re.search(
                    rf"(?im)^\s*(from|import)\s+{prohibido}\b", texto
                ), f"{archivo} no debe importar {prohibido}"
