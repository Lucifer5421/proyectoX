# ============================================================================
# MÓDULO: finance  |  CAPA: domain  |  ARCHIVO: exceptions.py
# QUÉ HACE: Excepciones de negocio del módulo finance (finanzas).
# DETALLE: clases: FinanceError, TransaccionNoEncontrada
# ============================================================================
"""Excepciones de negocio del módulo finance (finanzas)."""


class FinanceError(Exception):
    """Error base del dominio financiero."""


class TransaccionNoEncontrada(FinanceError):
    pass
