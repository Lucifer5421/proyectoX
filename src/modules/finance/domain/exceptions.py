"""Excepciones de negocio del módulo finance (finanzas)."""


class FinanceError(Exception):
    """Error base del dominio financiero."""


class TransaccionNoEncontrada(FinanceError):
    pass
