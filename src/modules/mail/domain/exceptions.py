# ============================================================================
# MÓDULO: mail  |  CAPA: domain  |  ARCHIVO: exceptions.py
# QUÉ HACE: Excepciones de negocio del módulo mail.
# DETALLE: clases: MailError, CorreoNoEncontrado
# ============================================================================
"""Excepciones de negocio del módulo mail."""


class MailError(Exception):
    """Error base del dominio de correo."""


class CorreoNoEncontrado(MailError):
    """El correo solicitado no existe."""
