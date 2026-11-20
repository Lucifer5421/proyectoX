# ============================================================================
# MÓDULO: finance  |  CAPA: infrastructure  |  ARCHIVO: external_adapters.py
# QUÉ HACE: Adaptador externo del módulo finance.
# DETALLE: clases: WowFinanceAdapter
# ============================================================================
"""Adaptador externo del módulo finance.

Los depósitos, comisiones y transacciones son locales (PostgreSQL). El
módulo no consume servicios externos en tiempo de ejecución; esta clase
queda como punto de extensión para una futura integración financiera.
"""


class WowFinanceAdapter:
    """Reservado para una integración futura con la economía de WoW."""
