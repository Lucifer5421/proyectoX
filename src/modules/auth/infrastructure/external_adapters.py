# ============================================================================
# MÓDULO: auth  |  CAPA: infrastructure  |  ARCHIVO: external_adapters.py
# QUÉ HACE: Adaptador externo del módulo auth con AzerothCore.
# DETALLE: clases: WowAuthAdapter
# ============================================================================
"""Adaptador externo del módulo auth con AzerothCore.

La integración es de **solo lectura**: consulta las bases `acore_auth` y
`acore_characters` para sincronizar cuentas y personajes. Nunca escribe en
las bases del servidor WoW.
"""

from typing import Any, Dict, List, Optional

from src.integrations.wow.client import WowClient
from src.integrations.wow.config import WowSettings, load_settings


class WowAuthAdapter:
    """Expone las cuentas/personajes de AzerothCore al módulo auth."""

    def __init__(self, settings: Optional[WowSettings] = None):
        self.settings = settings or load_settings()
        self.client = WowClient(self.settings)

    def fetch_characters(self) -> List[Dict[str, Any]]:
        """Devuelve las filas de personajes con su cuenta asociada."""
        return self.client.fetch_characters()
