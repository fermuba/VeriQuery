"""
Semantic Metadata Mapping - ACTUALIZADO PARA CONTOSO SOCIAL

Mapea conceptos de negocio a tablas REALES de tu base de datos:
- Usuario pregunta sobre "beneficiarios" → Buscar en "Dim_Beneficiario"
- Usuario pregunta sobre "asistencias" → Buscar en "Fact_Asistencia"
"""

import re
from typing import Dict, List, Tuple, Optional

# ============================================================================
# MAPEO SEMÁNTICO CORRECTO: Conceptos → Tablas REALES
# ============================================================================

SEMANTIC_MAPPING = {
    # DOMINIO: Beneficiarios
    "beneficiario": "Dim_Beneficiario",
    "beneficiarios": "Dim_Beneficiario",
    "beneficiaria": "Dim_Beneficiario",
    "familia": "Dim_Beneficiario",
    "familias": "Dim_Beneficiario",
    "persona": "Dim_Beneficiario",
    "personas": "Dim_Beneficiario",
    "usuario": "Dim_Beneficiario",
    "usuarios": "Dim_Beneficiario",
    "asistido": "Dim_Beneficiario",
    "asistidos": "Dim_Beneficiario",
    "cliente": "Dim_Beneficiario",
    "clientes": "Dim_Beneficiario",
    
    # DOMINIO: Asistencias/Entregas
    "asistencia": "Fact_Asistencia",
    "asistencias": "Fact_Asistencia",
    "entrega": "Fact_Asistencia",
    "entregas": "Fact_Asistencia",
    "transaccion": "Fact_Asistencia",
    "transacciones": "Fact_Asistencia",
    "evento": "Fact_Asistencia",
    "eventos": "Fact_Asistencia",
    "orden": "Fact_Asistencia",
    "ordenes": "Fact_Asistencia",
    
    # DOMINIO: Productos/Servicios/Tipos de Asistencia
    "producto": "Dim_TipoAsistencia",
    "productos": "Dim_TipoAsistencia",
    "servicio": "Dim_TipoAsistencia",
    "servicios": "Dim_TipoAsistencia",
    "item": "Dim_TipoAsistencia",
    "items": "Dim_TipoAsistencia",
    "tipo": "Dim_TipoAsistencia",
    "tipos": "Dim_TipoAsistencia",
    
    # DOMINIO: Ubicación
    "ubicacion": "Dim_Ubicacion",
    "ubicaciones": "Dim_Ubicacion",
    "zona": "Dim_Ubicacion",
    "zonas": "Dim_Ubicacion",
    "barrio": "Dim_Ubicacion",
    "barrios": "Dim_Ubicacion",
    "localidad": "Dim_Ubicacion",
    "localidades": "Dim_Ubicacion",
    "provincia": "Dim_Ubicacion",
    "provincias": "Dim_Ubicacion",
    
    # DOMINIO: Programas
    "programa": "Dim_Programa",
    "programas": "Dim_Programa",
    "proyecto": "Dim_Programa",
    "proyectos": "Dim_Programa",
    
    # DOMINIO: Tiempo
    "fecha": "Dim_Tiempo",
    "fechas": "Dim_Tiempo",
    "tiempo": "Dim_Tiempo",
    "periodo": "Dim_Tiempo",
    "periodos": "Dim_Tiempo",
    
    # DOMINIO: Donaciones
    "donacion": "Fact_Donacion",
    "donaciones": "Fact_Donacion",
    "donante": "Dim_Donante",
    "donantes": "Dim_Donante",
}

# ============================================================================
# MAPEO DE COLUMNAS CORRECTO
# ============================================================================

COLUMN_MAPPING = {
    # Dim_Beneficiario
    "nombre": ["NombreCompleto"],
    "edad": ["Edad"],
    "genero": ["Sexo"],
    "sexo": ["Sexo"],
    "vulnerabilidad": ["NivelVulnerabilidad"],
    
    # Dim_Ubicacion
    "zona": ["Zona"],
    "barrio": ["Barrio"],
    "localidad": ["Localidad"],
    "provincia": ["Provincia"],
    "nivel_socioeconomico": ["NivelSocioeconomico"],
    
    # Fact_Asistencia
    "fecha": ["FechaHoraEntrega"],
    "fecha_entrega": ["FechaHoraEntrega"],
    "cantidad": ["CantidadEntregada"],
    "cantidad_entregada": ["CantidadEntregada"],
    "valor": ["ValorMonetarioEstimado"],
    "precio": ["ValorMonetarioEstimado"],
    "monto": ["ValorMonetarioEstimado"],
    
    # Dim_TipoAsistencia
    "tipo_asistencia": ["NombreTipoAsistencia"],
    "categoria": ["CategoriaAsistencia"],
    "valor_unitario": ["ValorUnitarioEstimado"],
    
    # Dim_Programa
    "nombre_programa": ["NombrePrograma"],
    "tipo_programa": ["TipoPrograma"],
    "estado": ["Estado"],
    "presupuesto": ["PresupuestoAsignado"],
    
    # Dim_Tiempo
    "año": ["Año"],
    "mes": ["Mes"],
    "trimestre": ["Trimestre"],
    "semana": ["Semana"],
    "dia": ["Dia"],
}


def enrich_system_prompt(schema_info: str) -> str:
    """
    Generar prompt enriquecido con mapeo semántico + schema real
    """
    
    prompt = f"""
=== SCHEMA REAL DE LA BASE DE DATOS ===

{schema_info}

=== MAPEO SEMÁNTICO (MUY IMPORTANTE) ===

Cuando el usuario pregunta sobre estos conceptos, usa ESTAS tablas:

📊 BENEFICIARIOS/FAMILIAS/PERSONAS:
   → Tabla: Dim_Beneficiario
   → Columnas: BeneficiarioKey, NombreCompleto, Edad, Sexo, NivelVulnerabilidad

📊 ASISTENCIAS/ENTREGAS/EVENTOS:
   → Tabla: Fact_Asistencia
   → Columnas: AsistenciaKey, BeneficiarioKey, FechaHoraEntrega, CantidadEntregada, ValorMonetarioEstimado

📊 TIPOS DE AYUDA/PRODUCTOS/SERVICIOS:
   → Tabla: Dim_TipoAsistencia
   → Columnas: TipoAsistenciaKey, NombreTipoAsistencia, CategoriaAsistencia

📊 ZONAS/BARRIOS/UBICACIONES:
   → Tabla: Dim_Ubicacion
   → Columnas: UbicacionKey, Provincia, Localidad, Barrio, Zona, NivelSocioeconomico

📊 PROGRAMAS/PROYECTOS:
   → Tabla: Dim_Programa
   → Columnas: ProgramaKey, NombrePrograma, TipoPrograma, PresupuestoAsignado

📊 FECHAS/TIEMPOS/PERIODOS:
   → Tabla: Dim_Tiempo
   → Columnas: TiempoKey, Fecha, Año, Trimestre, Mes, Semana, Dia

=== EJEMPLOS DE TRADUCCIÓN CORRECTA ===

❌ INCORRECTO:
Usuario: "¿Cuántos beneficiarios tenemos?"
SQL: SELECT COUNT(*) FROM Customer  ← Customer NO EXISTE

✅ CORRECTO:
Usuario: "¿Cuántos beneficiarios tenemos?"
SQL: SELECT COUNT(*) FROM Dim_Beneficiario WHERE EsActual = 1

❌ INCORRECTO:
Usuario: "Asistencias de este mes"
SQL: SELECT * FROM Orders WHERE OrderDate > ...  ← OrderDate NO EXISTE

✅ CORRECTO:
Usuario: "Asistencias de este mes"
SQL: 
SELECT 
    b.NombreCompleto,
    a.FechaHoraEntrega,
    a.CantidadEntregada
FROM Fact_Asistencia a
JOIN Dim_Beneficiario b ON a.BeneficiarioKey = b.BeneficiarioKey
WHERE MONTH(a.FechaHoraEntrega) = MONTH(GETDATE())
  AND YEAR(a.FechaHoraEntrega) = YEAR(GETDATE())

❌ INCORRECTO:
Usuario: "Beneficiarios por zona"
SQL: SELECT State, COUNT(*) FROM Customer GROUP BY State  ← State NO EXISTE

✅ CORRECTO:
Usuario: "Beneficiarios por zona"
SQL:
SELECT 
    u.Zona,
    COUNT(DISTINCT b.BeneficiarioKey) AS Total
FROM Dim_Beneficiario b
JOIN Dim_Ubicacion u ON b.UbicacionKey = u.UbicacionKey
WHERE b.EsActual = 1
GROUP BY u.Zona

=== REGLAS CRÍTICAS ===

1. ⚠️ NO uses tablas: Customer, Orders, Product, Sales
   → Esas tablas NO EXISTEN en esta base de datos

2. ⚠️ NO uses columnas: OrderDate, NetPrice, ProductID
   → Esas columnas NO EXISTEN

3. ✅ USA SOLO las tablas y columnas listadas en el schema arriba

4. ✅ Si el usuario pregunta sobre "clientes" o "ventas", interpreta como "beneficiarios" y "asistencias"

5. ✅ SIEMPRE incluye TOP o LIMIT para proteger performance

6. ✅ Usa JOINs cuando necesites información de múltiples tablas

=== JOINS COMUNES ===

Beneficiario con Ubicación:
FROM Dim_Beneficiario b
JOIN Dim_Ubicacion u ON b.UbicacionKey = u.UbicacionKey

Asistencia con Beneficiario:
FROM Fact_Asistencia a
JOIN Dim_Beneficiario b ON a.BeneficiarioKey = b.BeneficiarioKey

Asistencia con Tipo:
FROM Fact_Asistencia a
JOIN Dim_TipoAsistencia t ON a.TipoAsistenciaKey = t.TipoAsistenciaKey

Asistencia con Tiempo:
FROM Fact_Asistencia a
JOIN Dim_Tiempo dt ON a.TiempoKey = dt.TiempoKey

Asistencia Completa:
FROM Fact_Asistencia a
JOIN Dim_Beneficiario b ON a.BeneficiarioKey = b.BeneficiarioKey
JOIN Dim_Ubicacion u ON b.UbicacionKey = u.UbicacionKey
JOIN Dim_TipoAsistencia t ON a.TipoAsistenciaKey = t.TipoAsistenciaKey
JOIN Dim_Tiempo dt ON a.TiempoKey = dt.TiempoKey

"""
    
    return prompt


def remap_question(question: str) -> Tuple[str, Dict[str, str]]:
    """
    Remapear pregunta del usuario a lenguaje de BD
    """
    remapped = question
    mappings = {}
    
    for domain_word, table_word in SEMANTIC_MAPPING.items():
        # Escapar caracteres especiales de regex
        escaped_word = re.escape(domain_word)
        pattern = rf'\b{escaped_word}\b'
        if re.search(pattern, question, re.IGNORECASE):
            mappings[domain_word] = table_word
            # NO reemplazar en la pregunta, solo loguear el mapeo
    
    return (question, mappings)  # Retornar pregunta original, solo loguear mapeos


def get_semantic_context(question: str) -> str:
    """
    Obtener contexto semántico para agregar al prompt
    """
    _, mappings = remap_question(question)
    
    if not mappings:
        return ""
    
    context = "\n=== CONTEXTO SEMÁNTICO DE LA PREGUNTA ===\n"
    context += "El usuario está preguntando sobre:\n"
    
    for concept, table in mappings.items():
        context += f"  • '{concept}' → usar tabla '{table}'\n"
    
    return context


# ============================================================================
# TABLE_ALIASES: Para compatibilidad con código existente (retry de tablas)
# ============================================================================

TABLE_ALIASES = {
    'Dim_Beneficiario': ['Dim_Beneficiario', 'DimBeneficiario', 'Beneficiario', 'Customer'],
    'Fact_Asistencia': ['Fact_Asistencia', 'FactAsistencia', 'Asistencia', 'Orders'],
    'Dim_TipoAsistencia': ['Dim_TipoAsistencia', 'DimTipoAsistencia', 'TipoAsistencia', 'Product'],
    'Dim_Ubicacion': ['Dim_Ubicacion', 'DimUbicacion', 'Ubicacion', 'Geography'],
    'Dim_Programa': ['Dim_Programa', 'DimPrograma', 'Programa'],
    'Dim_Tiempo': ['Dim_Tiempo', 'DimTiempo', 'Tiempo', 'Date'],
    'Dim_Donante': ['Dim_Donante', 'DimDonante', 'Donante'],
    'Fact_Donacion': ['Fact_Donacion', 'FactDonacion', 'Donacion'],
}