"""
Agents para Forensic Guardian
==============================

Módulo contiene los agentes especializados del sistema:
- QueryCrafter: Generador de SQL desde lenguaje natural
- QueryValidator: Validación de seguridad de queries
- ResultsFormatter: Formateo de resultados
"""

from .query_crafter import QueryCrafter

__all__ = ["QueryCrafter"]
