"""
Multi-Query Generator for Comprehensive Analysis
Generates multiple complementary queries for ambiguous or complex questions
"""

from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from .ambiguity_detector import MetricType


@dataclass
class QueryTemplate:
    """Template for generating SQL queries"""
    type: str  # "main", "supporting", "context"
    name: str
    description: str
    instruction: str
    metric: MetricType
    priority: int = 1


class MultiQueryGenerator:
    """
    Generates multiple complementary queries for comprehensive analysis
    """

    def __init__(self):
        """Initialize the multi-query generator with templates"""
        self.templates_by_metric = {
            MetricType.BENEFICIARIOS_COUNT: [
                QueryTemplate(
                    type="main",
                    name="Total de beneficiarios",
                    description="Cantidad total de beneficiarios únicos",
                    instruction="Genera una query SQL que cuente el TOTAL de beneficiarios únicos. Usa COUNT(DISTINCT customer_id) o similar.",
                    metric=MetricType.BENEFICIARIOS_COUNT,
                    priority=1,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Crecimiento de beneficiarios",
                    description="Variación porcentual año a año",
                    instruction="Calcula el crecimiento porcentual de beneficiarios comparando períodos consecutivos. Usa YEAR() para agrupar por año.",
                    metric=MetricType.CRECIMIENTO_PERCENT,
                    priority=2,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Distribución por zona",
                    description="Desglose de beneficiarios por región/zona",
                    instruction="Agrupa beneficiarios por zona geográfica. Usa una columna de ubicación o región si existe.",
                    metric=MetricType.COBERTURA_ZONAS,
                    priority=3,
                ),
                QueryTemplate(
                    type="context",
                    name="Tendencia de beneficiarios",
                    description="Evolución temporal de beneficiarios",
                    instruction="Muestra la evolución de beneficiarios por mes o trimestre para visualizar tendencias.",
                    metric=MetricType.BENEFICIARIOS_COUNT,
                    priority=4,
                ),
            ],
            MetricType.DONACIONES_SUM: [
                QueryTemplate(
                    type="main",
                    name="Presupuesto total de donaciones",
                    description="Monto total recibido en donaciones",
                    instruction="Calcula la SUMA total de donaciones/presupuesto. Usa SUM() en la columna de montos.",
                    metric=MetricType.DONACIONES_SUM,
                    priority=1,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Variación de donaciones",
                    description="Cambio porcentual en presupuesto",
                    instruction="Compara presupuesto entre períodos (año a año). Calcula variación porcentual.",
                    metric=MetricType.CRECIMIENTO_PERCENT,
                    priority=2,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Fuentes de donación",
                    description="Desglose por tipo o fuente de donación",
                    instruction="Agrupa donaciones por fuente/tipo si existe. Muestra top 5 fuentes.",
                    metric=MetricType.DONACIONES_SUM,
                    priority=3,
                ),
                QueryTemplate(
                    type="context",
                    name="Tendencia de donaciones",
                    description="Evolución temporal del presupuesto",
                    instruction="Muestra presupuesto por mes/trimestre para visualizar patrones de donación.",
                    metric=MetricType.DONACIONES_SUM,
                    priority=4,
                ),
            ],
            MetricType.ENTREGAS_COUNT: [
                QueryTemplate(
                    type="main",
                    name="Total de entregas",
                    description="Cantidad total de entregas/asistencias realizadas",
                    instruction="Cuenta el total de entregas. Usa COUNT(*) o COUNT(delivery_id).",
                    metric=MetricType.ENTREGAS_COUNT,
                    priority=1,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Crecimiento de entregas",
                    description="Variación porcentual de entregas",
                    instruction="Calcula el crecimiento en número de entregas comparando períodos consecutivos.",
                    metric=MetricType.CRECIMIENTO_PERCENT,
                    priority=2,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Desglose por tipo de entrega",
                    description="Entregas clasificadas por tipo/categoría",
                    instruction="Agrupa entregas por tipo (si existe columna de tipo). Muestra cantidad por tipo.",
                    metric=MetricType.ENTREGAS_COUNT,
                    priority=3,
                ),
                QueryTemplate(
                    type="context",
                    name="Frecuencia de entregas",
                    description="Patrón temporal de entregas",
                    instruction="Muestra entregas por mes/semana para identificar patrones estacionales.",
                    metric=MetricType.ENTREGAS_COUNT,
                    priority=4,
                ),
            ],
            MetricType.COSTO_BENEFICIARIO: [
                QueryTemplate(
                    type="main",
                    name="Costo promedio por beneficiario",
                    description="Costo unitario de atención",
                    instruction="Calcula el costo promedio dividiendo presupuesto total entre beneficiarios totales.",
                    metric=MetricType.COSTO_BENEFICIARIO,
                    priority=1,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Eficiencia comparativa",
                    description="Costo por beneficiario en diferentes períodos",
                    instruction="Compara costo unitario entre años o zonas para medir eficiencia.",
                    metric=MetricType.COSTO_BENEFICIARIO,
                    priority=2,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Costo por tipo de entrega",
                    description="Costo unitario por tipo de programa",
                    instruction="Calcula costo promedio para cada tipo de programa/entrega si existe clasificación.",
                    metric=MetricType.COSTO_BENEFICIARIO,
                    priority=3,
                ),
            ],
            MetricType.CRECIMIENTO_PERCENT: [
                QueryTemplate(
                    type="main",
                    name="Tasa de crecimiento anual",
                    description="Porcentaje de crecimiento año a año",
                    instruction="Calcula porcentaje de cambio anual. Fórmula: ((Actual - Anterior) / Anterior) * 100",
                    metric=MetricType.CRECIMIENTO_PERCENT,
                    priority=1,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Crecimiento acumulado",
                    description="Crecimiento desde punto base",
                    instruction="Calcula crecimiento acumulado desde año inicial. Muestra evolución temporal.",
                    metric=MetricType.CRECIMIENTO_PERCENT,
                    priority=2,
                ),
            ],
            MetricType.COBERTURA_ZONAS: [
                QueryTemplate(
                    type="main",
                    name="Cobertura geográfica",
                    description="Número de zonas/regiones cubiertas",
                    instruction="Cuenta zonas/regiones distintas con actividad. Usa COUNT(DISTINCT region).",
                    metric=MetricType.COBERTURA_ZONAS,
                    priority=1,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Beneficiarios por zona",
                    description="Distribución geográfica de alcance",
                    instruction="Agrupa beneficiarios por zona. Muestra count de beneficiarios por región.",
                    metric=MetricType.COBERTURA_ZONAS,
                    priority=2,
                ),
                QueryTemplate(
                    type="supporting",
                    name="Zonas sin cobertura",
                    description="Identificar gaps de cobertura",
                    instruction="Compara zonas potenciales vs cubiertas para identificar gaps.",
                    metric=MetricType.COBERTURA_ZONAS,
                    priority=3,
                ),
            ],
        }

    def generate(
        self,
        user_question: str,
        chosen_metric: MetricType,
        time_period: str = "year",
    ) -> Dict:
        """
        Generate multiple complementary queries for a given metric

        Args:
            user_question: Original user question
            chosen_metric: Selected MetricType to analyze
            time_period: Time grouping ("year", "month", "quarter", "week")

        Returns:
            Dictionary with:
            {
                "user_question": str,
                "chosen_metric": str,
                "time_period": str,
                "queries": List[Dict] containing query templates with instructions
            }
        """
        if chosen_metric not in self.templates_by_metric:
            return {
                "user_question": user_question,
                "chosen_metric": chosen_metric.value,
                "time_period": time_period,
                "queries": [],
                "error": f"No templates available for metric {chosen_metric.value}",
            }

        templates = self.templates_by_metric[chosen_metric]
        queries = []

        for template in templates:
            query_dict = asdict(template)
            query_dict["metric"] = template.metric.value
            
            # Inject time period context into instruction
            if time_period:
                query_dict["instruction"] = self._inject_context(
                    query_dict["instruction"], time_period
                )
            
            queries.append(query_dict)

        return {
            "user_question": user_question,
            "chosen_metric": chosen_metric.value,
            "time_period": time_period,
            "query_count": len(queries),
            "queries": queries,
        }

    def _inject_context(self, instruction: str, time_period: str) -> str:
        """
        Inject time period context into instruction

        Args:
            instruction: Original instruction
            time_period: Time grouping to inject

        Returns:
            Modified instruction with context
        """
        period_map = {
            "year": "por año (YEAR())",
            "month": "por mes (MONTH())",
            "quarter": "por trimestre (QUARTER())",
            "week": "por semana (WEEK())",
            "day": "por día (DAY())",
        }
        
        if time_period in period_map:
            period_str = period_map[time_period]
            instruction += f" Agrupa los resultados {period_str}."
        
        return instruction

    def get_query_count(self, metric: MetricType) -> int:
        """
        Get the number of queries generated for a metric

        Args:
            metric: MetricType to check

        Returns:
            Number of queries for this metric
        """
        if metric in self.templates_by_metric:
            return len(self.templates_by_metric[metric])
        return 0
