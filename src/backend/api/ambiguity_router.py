"""
Ambiguity Detection API Router
Endpoints for analyzing query ambiguity and suggesting clarifications
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path

# Add paths for imports - go up to src/backend then to agents
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import using relative path notation
try:
    from agents import get_ambiguity_detector, MetricType
except ImportError:
    # Fallback: try direct import with path manipulation
    agents_path = str(Path(__file__).parent.parent / "agents")
    sys.path.insert(0, agents_path)
    from ambiguity_detector import AmbiguityDetector, MetricType
    def get_ambiguity_detector():
        return AmbiguityDetector()

router = APIRouter(prefix="/api/query", tags=["query-analysis"])


# Request/Response Models
class AnalyzeAmbiguityRequest(BaseModel):
    question: str


class Clarification(BaseModel):
    label: str
    metric: str
    description: str
    icon: str


class AnalyzeAmbiguityResponse(BaseModel):
    question: str
    is_ambiguous: bool
    keywords_found: List[str]
    clarifications: List[Clarification]
    confidence: float


class SelectClarificationRequest(BaseModel):
    question: str
    chosen_metric: str


class SelectClarificationResponse(BaseModel):
    question: str
    chosen_metric: str
    metric_label: str
    message: str
    next_step: str


# Endpoints

@router.post("/analyze-ambiguity", response_model=AnalyzeAmbiguityResponse)
async def analyze_ambiguity(request: AnalyzeAmbiguityRequest):
    """
    Analyze a question for ambiguity and suggest clarifications
    
    Example:
        POST /api/query/analyze-ambiguity
        {"question": "¿Cuál fue el mejor año?"}
    
    Response:
        {
            "is_ambiguous": true,
            "keywords_found": ["mejor"],
            "clarifications": [
                {
                    "label": "📊 Más beneficiarios atendidos",
                    "metric": "count_beneficiarios",
                    "description": "Mayor número de beneficiarios alcanzados",
                    "icon": "📊"
                },
                ...
            ],
            "confidence": 0.9
        }
    """
    detector = get_ambiguity_detector()
    result = detector.detect(request.question)
    
    return AnalyzeAmbiguityResponse(
        question=request.question,
        is_ambiguous=result["is_ambiguous"],
        keywords_found=result["keywords_found"],
        clarifications=[
            Clarification(
                label=c["label"],
                metric=c["metric"],
                description=c["description"],
                icon=c["icon"],
            )
            for c in result["clarifications"]
        ],
        confidence=result["confidence"],
    )


@router.post("/select-clarification", response_model=SelectClarificationResponse)
async def select_clarification(request: SelectClarificationRequest):
    """
    User selects a clarification option
    Returns confirmation and next steps
    
    Example:
        POST /api/query/select-clarification
        {
            "question": "¿Cuál fue el mejor año?",
            "chosen_metric": "count_beneficiarios"
        }
    
    Response:
        {
            "question": "¿Cuál fue el mejor año?",
            "chosen_metric": "count_beneficiarios",
            "metric_label": "📊 Más beneficiarios atendidos",
            "message": "Entendido. Voy a analizar el año con más beneficiarios atendidos.",
            "next_step": "generating_queries"
        }
    """
    # Map metric value to label
    metric_labels = {
        "count_beneficiarios": "📊 Más beneficiarios atendidos",
        "sum_donaciones": "💰 Mayor presupuesto recibido",
        "count_entregas": "🎁 Más entregas realizadas",
        "costo_por_beneficiario": "📉 Menor costo por beneficiario",
        "crecimiento_percent": "📈 Mayor crecimiento",
        "cobertura_zonas": "🗺️ Cobertura geográfica",
    }
    
    metric_label = metric_labels.get(
        request.chosen_metric,
        f"Métrica: {request.chosen_metric}"
    )
    
    return SelectClarificationResponse(
        question=request.question,
        chosen_metric=request.chosen_metric,
        metric_label=metric_label,
        message=f"Entendido. Voy a analizar: {metric_label}",
        next_step="generating_queries",
    )
