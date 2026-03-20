"""
Ambiguity Detector for Natural Language Queries
Identifies ambiguous keywords and suggests clarification options
"""

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass


class MetricType(Enum):
    """Enum for different metric types that can be measured"""
    BENEFICIARIOS_COUNT = "count_beneficiarios"
    DONACIONES_SUM = "sum_donaciones"
    ENTREGAS_COUNT = "count_entregas"
    COSTO_BENEFICIARIO = "costo_por_beneficiario"
    CRECIMIENTO_PERCENT = "crecimiento_percent"
    COBERTURA_ZONAS = "cobertura_zonas"


@dataclass
class Clarification:
    """Represents a clarification option for ambiguous queries"""
    label: str
    metric: MetricType
    description: str
    icon: str = "📊"


class AmbiguityDetector:
    """
    Detects ambiguous keywords in natural language queries
    and suggests clarification options
    """

    def __init__(self):
        """Initialize the ambiguity detector with keyword mappings"""
        
        self.ambiguous_keywords = {
            "mejor": {
                "confidence": 0.9,
                "clarifications": [
                    Clarification(
                        label="📊 Más beneficiarios atendidos",
                        metric=MetricType.BENEFICIARIOS_COUNT,
                        description="Mayor número de beneficiarios alcanzados",
                        icon="📊"
                    ),
                    Clarification(
                        label="💰 Mayor presupuesto recibido",
                        metric=MetricType.DONACIONES_SUM,
                        description="Mayor cantidad de donaciones/presupuesto",
                        icon="💰"
                    ),
                    Clarification(
                        label="🎁 Más entregas realizadas",
                        metric=MetricType.ENTREGAS_COUNT,
                        description="Mayor número de entregas/asistencias",
                        icon="🎁"
                    ),
                    Clarification(
                        label="📉 Menor costo por beneficiario",
                        metric=MetricType.COSTO_BENEFICIARIO,
                        description="Más eficiente en costos",
                        icon="📉"
                    ),
                ]
            },
            "peor": {
                "confidence": 0.85,
                "clarifications": [
                    Clarification(
                        label="📊 Menos beneficiarios atendidos",
                        metric=MetricType.BENEFICIARIOS_COUNT,
                        description="Menor número de beneficiarios alcanzados",
                        icon="📊"
                    ),
                    Clarification(
                        label="💔 Menor presupuesto recibido",
                        metric=MetricType.DONACIONES_SUM,
                        description="Menor cantidad de donaciones/presupuesto",
                        icon="💔"
                    ),
                    Clarification(
                        label="📈 Mayor costo por beneficiario",
                        metric=MetricType.COSTO_BENEFICIARIO,
                        description="Menos eficiente en costos",
                        icon="📈"
                    ),
                ]
            },
            "máximo": {
                "confidence": 0.95,
                "clarifications": [
                    Clarification(
                        label="📊 Máximo de beneficiarios",
                        metric=MetricType.BENEFICIARIOS_COUNT,
                        description="Número máximo de beneficiarios",
                        icon="📊"
                    ),
                    Clarification(
                        label="💰 Máximo presupuesto",
                        metric=MetricType.DONACIONES_SUM,
                        description="Mayor monto de donaciones",
                        icon="💰"
                    ),
                    Clarification(
                        label="🎁 Máximas entregas",
                        metric=MetricType.ENTREGAS_COUNT,
                        description="Mayor número de entregas",
                        icon="🎁"
                    ),
                ]
            },
            "mínimo": {
                "confidence": 0.95,
                "clarifications": [
                    Clarification(
                        label="📊 Mínimo de beneficiarios",
                        metric=MetricType.BENEFICIARIOS_COUNT,
                        description="Número mínimo de beneficiarios",
                        icon="📊"
                    ),
                    Clarification(
                        label="💔 Mínimo presupuesto",
                        metric=MetricType.DONACIONES_SUM,
                        description="Menor monto de donaciones",
                        icon="💔"
                    ),
                    Clarification(
                        label="📉 Mínimo costo por beneficiario",
                        metric=MetricType.COSTO_BENEFICIARIO,
                        description="Menor costo operativo",
                        icon="📉"
                    ),
                ]
            },
            "más": {
                "confidence": 0.8,
                "clarifications": [
                    Clarification(
                        label="📊 Más beneficiarios",
                        metric=MetricType.BENEFICIARIOS_COUNT,
                        description="Mayor cantidad de beneficiarios",
                        icon="📊"
                    ),
                    Clarification(
                        label="💰 Más donaciones",
                        metric=MetricType.DONACIONES_SUM,
                        description="Mayor volumen de donaciones",
                        icon="💰"
                    ),
                    Clarification(
                        label="🎁 Más entregas",
                        metric=MetricType.ENTREGAS_COUNT,
                        description="Mayor número de entregas",
                        icon="🎁"
                    ),
                ]
            },
            "menos": {
                "confidence": 0.75,
                "clarifications": [
                    Clarification(
                        label="📊 Menos beneficiarios",
                        metric=MetricType.BENEFICIARIOS_COUNT,
                        description="Menor cantidad de beneficiarios",
                        icon="📊"
                    ),
                    Clarification(
                        label="💔 Menos donaciones",
                        metric=MetricType.DONACIONES_SUM,
                        description="Menor volumen de donaciones",
                        icon="💔"
                    ),
                    Clarification(
                        label="📉 Menos costo total",
                        metric=MetricType.COSTO_BENEFICIARIO,
                        description="Operación más económica",
                        icon="📉"
                    ),
                ]
            },
            "alto": {
                "confidence": 0.7,
                "clarifications": [
                    Clarification(
                        label="💰 Alto presupuesto",
                        metric=MetricType.DONACIONES_SUM,
                        description="Presupuesto elevado",
                        icon="💰"
                    ),
                    Clarification(
                        label="📈 Alto costo por beneficiario",
                        metric=MetricType.COSTO_BENEFICIARIO,
                        description="Costo unitario elevado",
                        icon="📈"
                    ),
                ]
            },
            "bajo": {
                "confidence": 0.7,
                "clarifications": [
                    Clarification(
                        label="💔 Bajo presupuesto",
                        metric=MetricType.DONACIONES_SUM,
                        description="Presupuesto reducido",
                        icon="💔"
                    ),
                    Clarification(
                        label="📉 Bajo costo por beneficiario",
                        metric=MetricType.COSTO_BENEFICIARIO,
                        description="Costo unitario bajo",
                        icon="📉"
                    ),
                ]
            },
            "crecimiento": {
                "confidence": 0.85,
                "clarifications": [
                    Clarification(
                        label="📈 Crecimiento de beneficiarios",
                        metric=MetricType.CRECIMIENTO_PERCENT,
                        description="Aumento porcentual de beneficiarios",
                        icon="📈"
                    ),
                    Clarification(
                        label="📈 Crecimiento de donaciones",
                        metric=MetricType.CRECIMIENTO_PERCENT,
                        description="Aumento porcentual del presupuesto",
                        icon="📈"
                    ),
                    Clarification(
                        label="📈 Crecimiento de entregas",
                        metric=MetricType.CRECIMIENTO_PERCENT,
                        description="Aumento porcentual de entregas",
                        icon="📈"
                    ),
                ]
            },
            "cobertura": {
                "confidence": 0.9,
                "clarifications": [
                    Clarification(
                        label="🗺️ Cobertura geográfica",
                        metric=MetricType.COBERTURA_ZONAS,
                        description="Número de zonas cubiertas",
                        icon="🗺️"
                    ),
                ]
            },
        }

    def detect(self, query: str) -> Dict:
        """
        Detect ambiguous keywords in a query and suggest clarifications

        Args:
            query: Natural language query string

        Returns:
            Dictionary with ambiguity detection results:
            {
                "is_ambiguous": bool,
                "keywords_found": List[str],
                "clarifications": List[Clarification],
                "confidence": float (0-1)
            }
        """
        query_lower = query.lower()
        keywords_found = []
        all_clarifications = []
        max_confidence = 0.0

        # Search for ambiguous keywords
        for keyword, data in self.ambiguous_keywords.items():
            if keyword in query_lower:
                keywords_found.append(keyword)
                all_clarifications.extend(data["clarifications"])
                max_confidence = max(max_confidence, data["confidence"])

        # Remove duplicates while preserving order
        unique_clarifications = []
        seen_labels = set()
        for clarif in all_clarifications:
            if clarif.label not in seen_labels:
                unique_clarifications.append(clarif)
                seen_labels.add(clarif.label)

        is_ambiguous = len(keywords_found) > 0

        return {
            "is_ambiguous": is_ambiguous,
            "keywords_found": keywords_found,
            "clarifications": [
                {
                    "label": c.label,
                    "metric": c.metric.value,
                    "description": c.description,
                    "icon": c.icon,
                }
                for c in unique_clarifications[:4]  # Return max 4 clarifications
            ],
            "confidence": max_confidence if is_ambiguous else 0.0,
        }

    def get_default_metric(self, keyword: str) -> Optional[MetricType]:
        """
        Get the default metric type for a keyword

        Args:
            keyword: The ambiguous keyword

        Returns:
            Default MetricType or None
        """
        if keyword in self.ambiguous_keywords:
            clarifications = self.ambiguous_keywords[keyword]["clarifications"]
            if clarifications:
                return clarifications[0].metric
        return None
