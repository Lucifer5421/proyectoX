# ============================================================================
# MÓDULO: core  |  CAPA: base  |  ARCHIVO: config.py
# QUÉ HACE: Lee la configuración del entorno (.env) y expone los ajustes de la aplicación.
# DETALLE: lee .env y expone la URL de la base de datos
# ============================================================================
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://wow_auction_user:wow_auction_password@localhost:5433/wow_auctions",
)
APP_ENV = os.getenv("APP_ENV", "development")
APP_PORT = int(os.getenv("APP_PORT", "8002"))
