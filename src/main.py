# ============================================================================
# MÓDULO: aplicación  |  CAPA: composición  |  ARCHIVO: main.py
# QUÉ HACE: Compone la FastAPI: importa modelos, registra routers y crea las tablas.
# DETALLE: compone la app FastAPI, registra 4 routers y crea las tablas; health check en /
# ============================================================================
from fastapi import FastAPI

from src.core.database import Base, engine

# Importar los modelos ORM antes de create_all. El orden respeta las llaves
# foráneas del modelo lógico 2.1:
#   auth -> inventory -> auction -> finance -> mail
import src.modules.auth.infrastructure.models_db  # noqa: F401  # auth: jugador, personaje
import src.modules.inventory.infrastructure.models_db  # noqa: F401  # inventory: item, inventario
import src.modules.auction.infrastructure.models_db  # noqa: F401  # auction: subasta, puja
import src.modules.finance.infrastructure.models_db  # noqa: F401  # finance: depósito, comisión, transacción
import src.modules.mail.infrastructure.models_db  # noqa: F401  # mail: correo

from src.modules.auth.presentation.router import router as auth_router  # auth: /auth
from src.modules.inventory.presentation.router import (  # inventory: /inventory
    router as inventory_router,
)
from src.modules.auction.presentation.router import router as auction_router  # auction: /auctions
from src.modules.mail.presentation.router import router as mail_router  # mail: /mail
# finance no se registra: es un módulo interno usado por auction.

# create_all es idempotente: si init.sql ya creó las tablas, no hace nada.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProyectoX — Subastas WoW",
    version="1.0.0",
    description=(
        "Monolito modular DDD para subastas de World of Warcraft. "
        "Módulos internos: auth, inventory, auction, finance y mail."
    ),
)

app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(auction_router)
app.include_router(mail_router)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "architecture": "Modular DDD (Domain-Driven Design)",
        "modules": [
            "auth",
            "inventory",
            "auction",
            "finance",
            "mail",
        ],
    }
