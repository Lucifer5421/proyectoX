"""Excepciones de negocio del módulo finance."""


class FinanceError(Exception):
    """Error base del dominio financiero."""


class TransaccionNoEncontrada(FinanceError):
    pass
