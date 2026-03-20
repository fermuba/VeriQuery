"""
Agents para Forensic Guardian
==============================

Módulo contiene los agentes especializados del sistema:
- QueryCrafter: Generador de SQL desde lenguaje natural
- QueryValidator: Validación de seguridad de queries
- ResultsFormatter: Formateo de resultados
- AmbiguityDetector: Detección de ambigüedad en preguntas
- MultiQueryGenerator: Generador de múltiples queries relacionadas
"""

from .query_crafter import QueryCrafter
from .ambiguity_detector import AmbiguityDetector, MetricType
from .multi_query_generator import MultiQueryGenerator, QueryTemplate

__all__ = [
    "QueryCrafter",
    "AmbiguityDetector",
    "MultiQueryGenerator",
    "MetricType",
    "QueryTemplate",
]


def get_ambiguity_detector():
    """Get an instance of AmbiguityDetector"""
    return AmbiguityDetector()


def get_multi_query_generator():
    """Get an instance of MultiQueryGenerator"""
    return MultiQueryGenerator()
