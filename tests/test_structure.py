"""Comprueba que los módulos respeten la estructura DDD exigida.

No necesita base de datos: solo valida la presencia de archivos y la
ausencia de nombres heredados del proyecto de delivery.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MODULOS = ("auth", "inventory", "auction", "finance")
CAPAS = (
    "domain/exceptions.py",
    "domain/models.py",
    "domain/repositories.py",
    "application/datos.py",
    "application/services.py",
    "infrastructure/external_adapter.py",
    "infrastructure/models_db.py",
    "infrastructure/repositories_impl.py",
    "presentation/routers.py",
    "presentation/schemas.py",
)


def test_init_sql_esta_en_la_raiz():
    assert (RAIZ / "init.sql").is_file()


def test_modulos_tienen_las_capas_requeridas():
    for modulo in MODULOS:
        base = RAIZ / "src" / "modules" / modulo
        assert base.is_dir(), f"Falta el módulo {modulo}"
        for capa in CAPAS:
            assert (base / capa).is_file(), (
                f"Falta {modulo}/{capa}"
            )


def test_no_quedan_nombres_del_proyecto_de_delivery():
    modulos = RAIZ / "src" / "modules"
    assert not (modulos / "restaurant").exists()
    for modulo in MODULOS:
        base = modulos / modulo
        assert not (base / "presentation" / "dtos.py").exists()
        assert not (base / "presentation" / "router.py").exists()
        assert not (
            base / "infrastructure" / "repository_impl.py"
        ).exists()


def test_main_registra_los_cuatro_modulos():
    main = (RAIZ / "src" / "main.py").read_text(encoding="utf-8")
    for modulo in MODULOS:
        assert f"src.modules.{modulo}.presentation.routers" in main
