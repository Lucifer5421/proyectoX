"""Excepciones de negocio del módulo payment (finanzas)."""


class FinanceError(Exception):
    """Error base del dominio financiero."""


class TransaccionNoEncontrada(FinanceError):
    pass
