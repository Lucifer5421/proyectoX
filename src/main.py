from fastapi import FastAPI

from src.core.database import Base, engine

# Importar los modelos ORM antes de create_all. Se respeta el orden de las
# llaves foráneas y el mismo orden de módulos que delivery-monolith:
# auth, restaurant, tracking, order y payment.
import src.modules.auth.infrastructure.models_db  # noqa: F401
import src.modules.restaurant.infrastructure.models_db  # noqa: F401
import src.modules.tracking.infrastructure.models_db  # noqa: F401
import src.modules.order.infrastructure.models_db  # noqa: F401
import src.modules.payment.infrastructure.models_db  # noqa: F401

from src.modules.auth.presentation.router import router as auth_router
from src.modules.restaurant.presentation.router import (
    router as restaurant_router,
)
from src.modules.order.presentation.router import router as order_router
from src.modules.payment.presentation.router import router as payment_router

# create_all es idempotente: si init.sql ya creó las tablas, no hace nada.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ProyectoX — Subastas WoW",
    version="1.0.0",
    description=(
        "Monolito modular DDD para subastas de World of Warcraft. "
        "Módulos internos: auth, restaurant, order, payment y tracking."
    ),
)

app.include_router(auth_router)
app.include_router(restaurant_router)
app.include_router(order_router)
app.include_router(payment_router)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "architecture": "Modular DDD (Domain-Driven Design)",
        "modules": [
            "auth",
            "restaurant",
            "order",
            "payment",
            "tracking",
        ],
    }
