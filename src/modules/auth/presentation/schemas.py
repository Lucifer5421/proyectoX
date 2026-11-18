"""Esquemas Pydantic de la API del módulo auth.

Los contratos de datos viven en `application/datos.py`; la capa de
presentación los reexporta para mantener una única fuente de verdad.
"""

from src.modules.auth.application.datos import JugadorOut, PersonajeOut

__all__ = ["JugadorOut", "PersonajeOut"]
