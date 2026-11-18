"""Esquemas Pydantic de la API del módulo finance.

Los contratos de datos viven en `application/datos.py`; la capa de
presentación los reexporta para mantener una única fuente de verdad.
"""

from src.modules.finance.application.datos import CorreoOut

__all__ = ["CorreoOut"]
