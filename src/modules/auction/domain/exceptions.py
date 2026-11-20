# ============================================================================
# MÓDULO: auction  |  CAPA: domain  |  ARCHIVO: exceptions.py
# QUÉ HACE: Excepciones de negocio del módulo de subastas.
# DETALLE: clases: SubastaError, SubastaCerrada, PujaInsuficiente, CompraDirectaNoDisponible, SubastaNoEncontrada
# ============================================================================
"""Excepciones de negocio del módulo de subastas."""


class SubastaError(Exception):
    """Error base del dominio de subastas."""


class SubastaCerrada(SubastaError):
    pass


class PujaInsuficiente(SubastaError):
    pass


class CompraDirectaNoDisponible(SubastaError):
    pass


class SubastaNoEncontrada(SubastaError):
    pass
