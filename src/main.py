from fastapi import FastAPI

from src.core.database import Base, engine

# Importar los modelos ORM antes de create_all. El orden respeta las llaves
# foráneas del modelo lógico 2.1:
#   auth -> inventory -> auction -> finance -> mail
import src.modules.auth.infrastructure.models_db  # noqa: F401
import src.modules.inventory.infrastructure.models_db  # noqa: F401
import src.modules.auction.infrastructure.models_db  # noqa: F401
import src.modules.finance.infrastructure.models_db  # noqa: F401
import src.modules.mail.infrastructure.models_db  # noqa: F401

from src.modules.auth.presentation.router import router as auth_router
from src.modules.inventory.presentation.router import (
    router as inventory_router,
)
from src.modules.auction.presentation.router import router as auction_router
from src.modules.mail.presentation.router import router as mail_router

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
