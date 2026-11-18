"""Adaptador externo del módulo restaurant (catálogo e inventario) con AzerothCore.

La integración es de **solo lectura**: consulta el inventario y el catálogo
de ítems de AzerothCore para sincronizarlos con PostgreSQL. Nunca escribe
en las bases del servidor WoW.
"""

from typing import Any, Dict, List, Optional

from src.integrations.wow.client import WowClient
from src.integrations.wow.config import WowSettings, load_settings


class WowInventoryAdapter:
    """Expone el catálogo e inventario de AzerothCore al módulo restaurant (catálogo e inventario)."""

    def __init__(self, settings: Optional[WowSettings] = None):
        self.settings = settings or load_settings()
        self.client = WowClient(self.settings)

    def fetch_inventory(self) -> List[Dict[str, Any]]:
        """Devuelve las filas de inventario con los datos del ítem."""
        return self.client.fetch_inventory()
