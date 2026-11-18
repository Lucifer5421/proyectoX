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
