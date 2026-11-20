# ============================================================================
# MÓDULO: auth  |  CAPA: domain  |  ARCHIVO: exceptions.py
# QUÉ HACE: Excepciones de negocio del módulo auth.
# DETALLE: clases: AuthError, JugadorNoEncontrado, PersonajeNoEncontrado, FondosInsuficientes
# ============================================================================
"""Excepciones de negocio del módulo auth."""


class AuthError(Exception):
    """Error base del dominio de autenticación/cuentas."""


class JugadorNoEncontrado(AuthError):
    pass


class PersonajeNoEncontrado(AuthError):
    pass


class FondosInsuficientes(AuthError):
    pass
