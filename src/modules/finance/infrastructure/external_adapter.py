"""Adaptador externo del módulo finance.

Los depósitos, comisiones, transacciones y el correo son locales
(PostgreSQL). El módulo no consume servicios externos en tiempo de
ejecución; esta clase queda como punto de extensión para una futura
integración con el correo del servidor WoW.
"""


class WowFinanceAdapter:
    """Reservado para una integración futura con el correo de WoW."""
