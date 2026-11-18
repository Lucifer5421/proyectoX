"""Excepciones de negocio del módulo mail."""


class MailError(Exception):
    """Error base del dominio de correo."""


class CorreoNoEncontrado(MailError):
    """El correo solicitado no existe."""
