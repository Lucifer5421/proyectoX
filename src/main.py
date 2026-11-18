from fastapi import FastAPI

from src.core.database import Base, engine

# Importar todos los modelos ORM antes de create_all. Cada módulo aporta sus
# tablas y las claves foráneas se resuelven con el metadata compartido.
import src.modules.auth.infrastructure.models_db  # noqa: F401
import src.modules.inventory.infrastructure.models_db  # noqa: F401
import src.modules.auction.infrastructure.models_db  # noqa: F401
import src.modules.finance.infrastructure.models_db  # noqa: F401
from src.modules.auction.presentation.routers import (
    router as auction_router,
)
from src.modules.auth.presentation.routers import router as auth_router
from src.modules.finance.presentation.routers import (
    router as mail_router,
)
from src.modules.inventory.presentation.routers import (
    router as inventory_router,
)

# create_all es idempotente: si init.sql ya creó las tablas, no hace nada.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProyectoX — Subastas WoW",
    version="1.0.0",
    description=(
        "Monolito modular DDD para subastas de World of Warcraft: "
        "auth, inventory, auction y finance."
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
        "modules": ["auth", "inventory", "auction", "finance"],
    }
