"""Adaptador externo del módulo auction.

Las subastas de proyectoX viven en PostgreSQL y no se consultan en tiempo de
ejecución contra AzerothCore. La integración con WoW se limita al sync de
solo lectura de auth e inventory. Esta clase queda como punto de extensión
para una futura lectura de subastas del servidor.
"""


class WowAuctionAdapter:
    """Reservado para una integración futura con las subastas de WoW."""
