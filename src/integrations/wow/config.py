"""Configuración de la integración con AzerothCore.

Las credenciales se leen de variables de entorno. Nunca se escriben en el
repositorio: usa `wow-server/api/.env` (ignorado por git) o exporta las
variables en la shell.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WowSettings:
    host: str
    port: int
    user: str
    password: str
    auth_db: str
    characters_db: str
    world_db: str

    @property
    def configured(self) -> bool:
        return bool(self.password)


def load_settings() -> WowSettings:
    return WowSettings(
        host=os.getenv("WOW_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("WOW_DB_PORT", "3307")),
        user=os.getenv("WOW_DB_USER", "acore_api"),
        password=os.getenv("WOW_DB_PASSWORD", ""),
        auth_db=os.getenv("WOW_DB_AUTH", "acore_auth"),
        characters_db=os.getenv("WOW_DB_CHARACTERS", "acore_characters"),
        world_db=os.getenv("WOW_DB_WORLD", "acore_world"),
    )


def database_url_for_sync() -> str:
    """URL de PostgreSQL para ejecutar el sync desde el host.

    El contenedor de la API usa `postgres-db:5432`; desde el host se usa
    `localhost:5433`. Define `DATABASE_URL_LOCAL` en `.env` para el sync.
    """
    url = os.getenv("DATABASE_URL_LOCAL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "Define DATABASE_URL_LOCAL (o DATABASE_URL) para el sync."
        )
    return url
