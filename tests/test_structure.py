"""Comprueba que proyectoX replique la estructura de delivery-monolith.

No necesita base de datos: solo valida la presencia de archivos, los nombres
de las capas y el orden de importación de los módulos.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MODULOS = ("auth", "order", "payment", "restaurant", "tracking")
MODULOS_CON_RUTAS = ("auth", "restaurant", "order", "payment")
CAPAS = (
    "application/dtos.py",
    "application/services.py",
    "domain/exceptions.py",
    "domain/models.py",
    "domain/repositories.py",
    "infrastructure/external_adapters.py",
    "infrastructure/models_db.py",
    "infrastructure/repository_impl.py",
    "presentation/router.py",
)
TXT_AUTH = (
    "application/casos_uso-orquestacion.txt",
    "domain/reglas_negocio.txt",
    "infrastructure/implementacion_tecnica.txt",
    "presentation/capa_exposicion.txt",
)


def test_init_sql_esta_en_la_raiz():
    assert (RAIZ / "init.sql").is_file()


def test_modulos_tienen_la_estructura_de_delivery():
    for modulo in MODULOS:
        base = RAIZ / "src" / "modules" / modulo
        assert base.is_dir(), f"Falta el módulo {modulo}"
        for capa in CAPAS:
            assert (base / capa).is_file(), (
                f"Falta {modulo}/{capa}"
            )


def test_auth_tiene_los_cuatro_txt_de_delivery():
    base = RAIZ / "src" / "modules" / "auth"
    for archivo in TXT_AUTH:
        assert (base / archivo).is_file(), f"Falta auth/{archivo}"


def test_solo_auth_tiene_los_txt_de_delivery():
    for modulo in MODULOS:
        if modulo == "auth":
            continue
        base = RAIZ / "src" / "modules" / modulo
        for archivo in TXT_AUTH:
            assert not (base / archivo).exists(), (
                f"{modulo}/{archivo} no existe en delivery"
            )


def test_init_py_solo_en_la_raiz_de_los_modulos_correctos():
    assert not (RAIZ / "src" / "__init__.py").exists()
    assert not (RAIZ / "src" / "core" / "__init__.py").exists()
    assert not (RAIZ / "src" / "modules" / "__init__.py").exists()
    assert not (
        RAIZ / "src" / "modules" / "auth" / "__init__.py"
    ).exists()

    for modulo in ("order", "payment", "restaurant", "tracking"):
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


def test_order_conserva_los_archivos_raiz_de_delivery_vacios():
    base = RAIZ / "src" / "modules" / "order"
    for nombre in ("models.py", "services.py"):
        archivo = base / nombre
        assert archivo.is_file()
        assert archivo.read_text(encoding="utf-8") == ""


def test_tracking_queda_vacio():
    base = RAIZ / "src" / "modules" / "tracking"
    for archivo in base.rglob("*"):
        if not archivo.is_file():
            continue
        if "__pycache__" in archivo.parts:
            continue
        assert archivo.read_text(encoding="utf-8") == "", (
            f"{archivo} debe quedar vacío: no hay tracking en proyectoX"
        )


def test_no_quedan_nombres_anteriores():
    modulos = RAIZ / "src" / "modules"
    for viejo in ("auction", "finance", "inventory"):
        assert not (modulos / viejo).exists()

    for modulo in MODULOS:
        base = modulos / modulo
        assert not (base / "application" / "datos.py").exists()
        assert not (base / "presentation" / "schemas.py").exists()
        assert not (base / "presentation" / "routers.py").exists()
        assert not (
            base / "infrastructure" / "repositories_impl.py"
        ).exists()
        assert not (
            base / "infrastructure" / "external_adapter.py"
        ).exists()


def test_main_importa_modelos_en_el_orden_de_delivery():
    main = (RAIZ / "src" / "main.py").read_text(encoding="utf-8")
    orden = ("auth", "restaurant", "tracking", "order", "payment")
    posiciones = [
        main.index(f"src.modules.{modulo}.infrastructure.models_db")
        for modulo in orden
    ]
    assert posiciones == sorted(posiciones)


def test_main_registra_los_modulos_con_rutas():
    main = (RAIZ / "src" / "main.py").read_text(encoding="utf-8")
    for modulo in MODULOS_CON_RUTAS:
        assert f"src.modules.{modulo}.presentation.router" in main
    assert "src.modules.tracking.presentation.router" not in main
