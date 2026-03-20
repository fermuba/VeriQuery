"""Semantic Metadata Mapping for Contoso Social Database"""
import re
from typing import Dict, List, Tuple, Optional

SEMANTIC_MAPPING = {
    "beneficiario": "Dim_Beneficiario",
    "beneficiarios": "Dim_Beneficiario",
    "asistencia": "Fact_Asistencia",
    "asistencias": "Fact_Asistencia",
    "entrega": "Fact_Asistencia",
    "entregas": "Fact_Asistencia",
    "tipo": "Dim_TipoAsistencia",
    "producto": "Dim_TipoAsistencia",
    "zona": "Dim_Ubicacion",
    "programa": "Dim_Programa",
    "fecha": "Dim_Tiempo",
    "donante": "Dim_Donante",
    "donacion": "Fact_Donacion",
}

COLUMN_MAPPING = {
    "nombre": "NombreCompleto",
    "fecha": "FechaHoraEntrega",
    "cantidad": "CantidadEntregada",
    "valor": "ValorMonetarioEstimado",
}

def map_domain_concept_to_table(concept: str) -> Optional[str]:
    """Maps a business domain concept to a real database table."""
    concept_lower = concept.lower().strip()
    return SEMANTIC_MAPPING.get(concept_lower)

def get_columns_for_concept(concept: str) -> List[str]:
    """Gets common columns for a business concept."""
    table = map_domain_concept_to_table(concept)
    if not table:
        return []
    if "Beneficiario" in table:
        return ["BeneficiarioID", "NombreCompleto", "EsActual"]
    elif "Asistencia" in table:
        return ["AsistenciaID", "FechaHoraEntrega", "CantidadEntregada", "ValorMonetarioEstimado"]
    elif "TipoAsistencia" in table:
        return ["TipoAsistenciaID", "Descripcion"]
    elif "Ubicacion" in table:
        return ["UbicacionID", "Zona"]
    elif "Programa" in table:
        return ["ProgramaID", "Nombre"]
    elif "Tiempo" in table:
        return ["TiempoID", "Fecha"]
    return []

def enrich_system_prompt(original_prompt: str = "", user_question: str = "") -> str:
    """Enriches the system prompt with semantic mapping context."""
    return original_prompt + "\n\nCONTOSO SOCIAL: Dim_Beneficiario, Fact_Asistencia, Dim_TipoAsistencia, Dim_Ubicacion, Dim_Programa, Dim_Tiempo\nUse FechaHoraEntrega NOT OrderDate, ValorMonetarioEstimado NOT NetPrice"

def remap_question(question: str) -> Tuple[str, Dict[str, str]]:
    """Remaps a user's natural language question."""
    mappings_found = {}
    for concept, table in SEMANTIC_MAPPING.items():
        if concept.lower() in question.lower():
            mappings_found[concept] = table
    return question, mappings_found

def get_all_tables() -> List[str]:
    """Returns list of all real database tables."""
    return list(set(SEMANTIC_MAPPING.values()))

def get_table_description(table_name: str) -> str:
    """Gets a human-readable description of a table."""
    return table_name
