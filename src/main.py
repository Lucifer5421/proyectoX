from fastapi import FastAPI

from src.core.database import Base, engine

# Importar los modelos ORM para que SQLAlchemy los registre antes de create_all
import src.modules.auction.infrastructure.models_db  # noqa: F401
from src.modules.auction.presentation.router import (
    mail_router,
    router as auction_router,
)

# create_all es idempotente: si init.sql ya creó las tablas, no hace nada.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProyectoX — Subastas WoW",
    version="1.0.0",
    description=(
        "Módulo de subastas de World of Warcraft siguiendo el molde "
        "de monolito modular DDD (delivery-monolith como guía)."
    ),
)

app.include_router(auction_router)
app.include_router(mail_router)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "architecture": "Modular DDD (Domain-Driven Design)",
        "module": "auction",
    }
