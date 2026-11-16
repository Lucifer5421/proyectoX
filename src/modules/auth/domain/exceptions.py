"""Excepciones de negocio del módulo auth."""


class AuthError(Exception):
    """Error base del dominio de autenticación/cuentas."""


class JugadorNoEncontrado(AuthError):
    pass


class PersonajeNoEncontrado(AuthError):
    pass


class FondosInsuficientes(AuthError):
    pass
