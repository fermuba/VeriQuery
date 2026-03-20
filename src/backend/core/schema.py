"""
Semantic Metadata Mapping - Schema Configuration
=================================================

Módulo que implementa el 'Contrato de Datos' para el motor NL2SQL (Natural Language to SQL)
del proyecto 'Sentinel AI Auditor' (Forensic Data Guardian).

Patrón: Star Schema (Hechos y Dimensiones)
Propósito: Proporcionar contexto de negocio y estructura de datos al LLM para:
  1. Prevenir alucinaciones mediante definiciones explícitas
  2. Facilitar JOINs correctos entre tablas de hechos y dimensiones
  3. Mapear preguntas naturales a consultas SQL precisas
  4. Mantener trazabilidad de auditoría forense

Arquitectura:
  - Dimensiones (dim_*): Tablas de atributos maestros (lentamente cambiantes)
  - Hechos (fact_*): Tablas de transacciones/eventos con columnas de auditoría
  - Columnas de Auditoría: usuario_registrador, metodo_verificacion, timestamp

PEP 8 Compliance: ✅
Type Hinting: ✅
Docstrings: ✅
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


# ============================================================================
# TIPOS Y ENUMERACIONES
# ============================================================================

class ColumnType(str, Enum):
    """Tipos de datos SQL soportados"""
    INT = "INTEGER"
    BIGINT = "BIGINT"
    DECIMAL = "DECIMAL(10,2)"
    VARCHAR = "VARCHAR(255)"
    TEXT = "TEXT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIMESTAMP = "TIMESTAMP"
    BOOLEAN = "BOOLEAN"
    UUID = "UUID"


class ConstraintType(str, Enum):
    """Restricciones de columna"""
    PRIMARY_KEY = "PRIMARY_KEY"
    FOREIGN_KEY = "FOREIGN_KEY"
    UNIQUE = "UNIQUE"
    NOT_NULL = "NOT_NULL"
    DEFAULT = "DEFAULT"


@dataclass
class ColumnMetadata:
    """Metadatos de una columna individual"""
    name: str
    type: ColumnType
    description: str
    constraints: List[ConstraintType] = None
    foreign_key: Optional[str] = None  # Formato: "tabla.columna"
    default_value: Optional[Any] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []


@dataclass
class TableMetadata:
    """Metadatos de una tabla completa"""
    name: str
    table_type: str  # "DIMENSION" o "FACT"
    description: str
    business_context: str
    columns: List[ColumnMetadata]
    sample_queries: List[str]
    audit_tracked: bool = True


# ============================================================================
# ESQUEMA STAR: DIMENSIONES
# ============================================================================

DIM_BENEFICIARIOS: TableMetadata = TableMetadata(
    name="dim_beneficiarios",
    table_type="DIMENSION",
    description="Tabla de dimensión: Atributos maestros de beneficiarios",
    business_context=(
        "Almacena la información demográfica y personal de todos los beneficiarios "
        "del programa de asistencia. Esta es la dimensión principal que se relaciona "
        "con las transacciones de asistencia (fact_asistencias). "
        "Lentamente cambiante (SCD Type 1): Los cambios de dirección o familia se sobreescriben."
    ),
    columns=[
        ColumnMetadata(
            name="beneficiario_id",
            type=ColumnType.INT,
            description="Identificador único del beneficiario",
            constraints=[ConstraintType.PRIMARY_KEY, ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="dni",
            type=ColumnType.VARCHAR,
            description="Documento Nacional de Identidad (DNI) del beneficiario",
            constraints=[ConstraintType.UNIQUE, ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="nombre_completo",
            type=ColumnType.VARCHAR,
            description="Nombre y apellido completo del beneficiario",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="fecha_nacimiento",
            type=ColumnType.DATE,
            description="Fecha de nacimiento del beneficiario (YYYY-MM-DD)",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="barrio",
            type=ColumnType.VARCHAR,
            description="Barrio o localidad de residencia del beneficiario",
            constraints=[]
        ),
        ColumnMetadata(
            name="familia_id",
            type=ColumnType.INT,
            description="Identificador del núcleo familiar (para rastrear relaciones)",
            constraints=[ConstraintType.FOREIGN_KEY],
            foreign_key="dim_familias.familia_id"
        ),
        ColumnMetadata(
            name="estado",
            type=ColumnType.VARCHAR,
            description="Estado del beneficiario (activo/inactivo/suspendido)",
            constraints=[ConstraintType.NOT_NULL],
            default_value="activo"
        ),
        ColumnMetadata(
            name="fecha_inscripcion",
            type=ColumnType.DATETIME,
            description="Fecha y hora de inscripción al programa",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="ultima_actualizacion",
            type=ColumnType.TIMESTAMP,
            description="Timestamp de la última actualización del registro",
            constraints=[ConstraintType.NOT_NULL]
        ),
    ],
    sample_queries=[
        "¿Cuántos beneficiarios tenemos en el barrio Centro?",
        "¿Cuál es la edad promedio de nuestros beneficiarios?",
        "¿Quiénes son los beneficiarios de la familia 42?",
        "¿Cuál es el DNI del beneficiario Juan Pérez?",
        "¿Cuántos beneficiarios nuevos se inscribieron este mes?",
    ]
)

DIM_PRODUCTOS_SERVICIOS: TableMetadata = TableMetadata(
    name="dim_productos_servicios",
    table_type="DIMENSION",
    description="Tabla de dimensión: Catálogo de productos y servicios de asistencia",
    business_context=(
        "Catálogo maestro de todos los tipos de asistencia disponibles (alimentos, "
        "medicamentos, atención médica, etc.). Cada asistencia registrada en fact_asistencias "
        "hace referencia a un producto/servicio específico. "
        "Lentamente cambiante: Nuevos servicios se agregan, precios se actualizan ocasionalmente."
    ),
    columns=[
        ColumnMetadata(
            name="producto_id",
            type=ColumnType.INT,
            description="Identificador único del producto o servicio",
            constraints=[ConstraintType.PRIMARY_KEY, ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="nombre_item",
            type=ColumnType.VARCHAR,
            description="Nombre descriptivo del producto o servicio",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="categoria",
            type=ColumnType.VARCHAR,
            description="Categoría del producto (Alimentos/Medicamentos/Salud/Otro)",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="costo_estimado",
            type=ColumnType.DECIMAL,
            description="Costo unitario estimado en pesos argentinos",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="unidad_medida",
            type=ColumnType.VARCHAR,
            description="Unidad de medida (Kg, Unidad, Dosis, etc.)",
            constraints=[ConstraintType.NOT_NULL],
            default_value="Unidad"
        ),
        ColumnMetadata(
            name="descripcion_detallada",
            type=ColumnType.TEXT,
            description="Descripción técnica completa del producto/servicio",
            constraints=[]
        ),
        ColumnMetadata(
            name="requiere_especificacion",
            type=ColumnType.BOOLEAN,
            description="¿Se requieren especificaciones adicionales? (talla, sabor, dosis)",
            constraints=[ConstraintType.NOT_NULL],
            default_value=False
        ),
        ColumnMetadata(
            name="activo",
            type=ColumnType.BOOLEAN,
            description="¿Está disponible para usar? (servicios descontinuados = false)",
            constraints=[ConstraintType.NOT_NULL],
            default_value=True
        ),
    ],
    sample_queries=[
        "¿Cuáles son todos los medicamentos disponibles?",
        "¿Cuál es el costo estimado de un kg de arroz?",
        "¿Qué servicios médicos ofrecemos?",
        "¿Cuáles productos requieren especificaciones adicionales?",
        "¿Cuántos productos diferentes tenemos en la categoría Alimentos?",
    ]
)

DIM_FAMILIAS: TableMetadata = TableMetadata(
    name="dim_familias",
    table_type="DIMENSION",
    description="Tabla de dimensión: Núcleos familiares y composición familiar",
    business_context=(
        "Agrupa beneficiarios en unidades familiares. Facilita análisis por familia "
        "y asignación de recursos a nivel de hogar. Datos lentamente cambiantes."
    ),
    columns=[
        ColumnMetadata(
            name="familia_id",
            type=ColumnType.INT,
            description="Identificador único de la familia/hogar",
            constraints=[ConstraintType.PRIMARY_KEY, ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="jefe_de_familia_id",
            type=ColumnType.INT,
            description="ID del beneficiario que es jefe de familia",
            constraints=[ConstraintType.FOREIGN_KEY, ConstraintType.NOT_NULL],
            foreign_key="dim_beneficiarios.beneficiario_id"
        ),
        ColumnMetadata(
            name="cantidad_integrantes",
            type=ColumnType.INT,
            description="Número total de integrantes del hogar",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="ingresos_mensuales_estimados",
            type=ColumnType.DECIMAL,
            description="Ingreso familiar total estimado mensual (para análisis de vulnerabilidad)",
            constraints=[]
        ),
        ColumnMetadata(
            name="clasificacion_vulnerabilidad",
            type=ColumnType.VARCHAR,
            description="Nivel de vulnerabilidad (Bajo/Medio/Alto/Crítico)",
            constraints=[ConstraintType.NOT_NULL]
        ),
    ],
    sample_queries=[
        "¿Cuáles son las familias más vulnerables?",
        "¿Cuál es el tamaño promedio de una familia atendida?",
        "¿Cuántos integrantes tiene la familia 42?",
    ]
)


# ============================================================================
# ESQUEMA STAR: HECHOS (FORENSE)
# ============================================================================

FACT_ASISTENCIAS: TableMetadata = TableMetadata(
    name="fact_asistencias",
    table_type="FACT",
    description="Tabla de hechos: Registro de todas las transacciones de asistencia",
    business_context=(
        "Centro del modelo Star Schema. Cada fila representa UNA asistencia otorgada "
        "a UN beneficiario. Incluye referencias a dimensiones (qué, a quién, cuándo) "
        "y columnas de AUDITORÍA FORENSE para garantizar trazabilidad completa. "
        "Clave para análisis de: cobertura, equidad, fraude, irregularidades. "
        "NOTA: Nunca eliminar registros (soft-delete con estado). Mantener historial "
        "completo para investigaciones forenses."
    ),
    columns=[
        ColumnMetadata(
            name="asistencia_id",
            type=ColumnType.BIGINT,
            description="Identificador único e inmutable de la transacción",
            constraints=[ConstraintType.PRIMARY_KEY, ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="beneficiario_id",
            type=ColumnType.INT,
            description="FK a dim_beneficiarios (quién recibe la asistencia)",
            constraints=[ConstraintType.FOREIGN_KEY, ConstraintType.NOT_NULL],
            foreign_key="dim_beneficiarios.beneficiario_id"
        ),
        ColumnMetadata(
            name="producto_id",
            type=ColumnType.INT,
            description="FK a dim_productos_servicios (qué se entrega)",
            constraints=[ConstraintType.FOREIGN_KEY, ConstraintType.NOT_NULL],
            foreign_key="dim_productos_servicios.producto_id"
        ),
        ColumnMetadata(
            name="cantidad",
            type=ColumnType.DECIMAL,
            description="Cantidad entregada del producto/servicio",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="fecha_asistencia",
            type=ColumnType.DATE,
            description="Fecha en que se otorgó la asistencia (YYYY-MM-DD)",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="costo_real",
            type=ColumnType.DECIMAL,
            description="Costo real incurrido (puede diferir del costo estimado)",
            constraints=[ConstraintType.NOT_NULL]
        ),
        # ==================== COLUMNAS DE AUDITORÍA FORENSE ====================
        ColumnMetadata(
            name="usuario_registrador",
            type=ColumnType.VARCHAR,
            description="Usuario que registró la asistencia (trazabilidad de responsable)",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="metodo_verificacion",
            type=ColumnType.VARCHAR,
            description=(
                "Método de verificación usado: 'biometrico', 'documento', 'testigo', "
                "'declaracion_beneficiario', 'otro' (crítico para detectar irregularidades)"
            ),
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="observaciones_auditor",
            type=ColumnType.TEXT,
            description="Notas de auditoría o investigador (flags, inconsistencias detectadas)",
            constraints=[]
        ),
        ColumnMetadata(
            name="timestamp_registro",
            type=ColumnType.TIMESTAMP,
            description="Marca de tiempo exacta del registro (para detectar anomalías temporales)",
            constraints=[ConstraintType.NOT_NULL]
        ),
        ColumnMetadata(
            name="ip_registrador",
            type=ColumnType.VARCHAR,
            description="IP desde la cual se registró (para auditoría de acceso)",
            constraints=[]
        ),
        ColumnMetadata(
            name="estado_verificacion",
            type=ColumnType.VARCHAR,
            description="Estado de verificación: 'pendiente', 'verificado', 'bajo_sospecha', 'rechazado'",
            constraints=[ConstraintType.NOT_NULL],
            default_value="verificado"
        ),
        ColumnMetadata(
            name="flag_anomalia",
            type=ColumnType.BOOLEAN,
            description="¿Se detectó alguna anomalía en esta transacción?",
            constraints=[ConstraintType.NOT_NULL],
            default_value=False
        ),
        # ========================================================================
        ColumnMetadata(
            name="especificacion",
            type=ColumnType.VARCHAR,
            description="Especificaciones adicionales (talla, sabor, dosis si aplica)",
            constraints=[]
        ),
        ColumnMetadata(
            name="estado",
            type=ColumnType.VARCHAR,
            description="Estado del registro: 'completo', 'parcial', 'cancelado', 'en_revision'",
            constraints=[ConstraintType.NOT_NULL],
            default_value="completo"
        ),
    ],
    sample_queries=[
        "¿Cuántos kg de arroz se distribuyeron en marzo?",
        "¿Cuál es el gasto total en medicamentos por beneficiario?",
        "¿Qué transacciones fueron registradas después de las 22:00?",
        "¿Cuáles registros tienen método de verificación 'declaracion_beneficiario'?",
        "¿Cuántos beneficiarios recibieron asistencia más de 5 veces?",
        "¿Hay transacciones con costos que desvían significativamente del promedio?",
        "¿Quién registró la asistencia ID 12345?",
        "¿Cuáles asistencias tienen flag_anomalia = true?",
        "¿Cuál es el promedio de asistencias por familia?",
    ]
)


# ============================================================================
# DICCIONARIO MAESTRO DE SCHEMA
# ============================================================================

DB_SCHEMA_METADATA: Dict[str, TableMetadata] = {
    "dim_beneficiarios": DIM_BENEFICIARIOS,
    "dim_productos_servicios": DIM_PRODUCTOS_SERVICIOS,
    "dim_familias": DIM_FAMILIAS,
    "fact_asistencias": FACT_ASISTENCIAS,
}


# ============================================================================
# FUNCIONES DE UTILIDAD PARA EL LLM
# ============================================================================

def get_schema_prompt() -> str:
    """
    Genera el prompt completo del esquema para inyectar en el System Message.
    CONTOSO V2 10K ECOMMERCE
    """
    
    return """
SCHEMA DE BASE DE DATOS - CONTOSO V2 10K ECOMMERCE
====================================================

INSTRUCCIONES CRITICAS PARA NL2SQL:
1. SOLO usa estas 5 tablas: Customer, Sales, Product, Store, Date
2. NUNCA inventes tablas o columnas que no existan
3. Usa [brackets] para nombres con espacios: [Order Date], [Product Name]
4. JOINs: Sales es la tabla central (FACT), las otras son dimensiones
5. Para fechas, usa DATEPART, MONTH, YEAR (SQL Server, NO DATE_TRUNC)

TABLAS Y COLUMNAS:

Customer (Clientes)
- CustomerKey (INT) - ID unico
- Name (NVARCHAR) - Nombre
- Gender (NVARCHAR) - Genero
- Age (INT) - Edad
- Birthday (DATE) - Cumpleanos
- Address (NVARCHAR) - Direccion
- City (NVARCHAR) - Ciudad
- State (NVARCHAR) - Provincia
- Country (NVARCHAR) - Pais
- Zip Code (NVARCHAR) - Codigo postal

Product (Catalogo de productos)
- ProductKey (INT) - ID unico
- Product Name (NVARCHAR) - Nombre
- Brand (NVARCHAR) - Marca
- Category (NVARCHAR) - Categoria
- Subcategory (NVARCHAR) - Subcategoria
- Color (NVARCHAR) - Color
- Weight (FLOAT) - Peso
- Unit Cost (MONEY) - Costo unitario
- Unit Price (MONEY) - Precio de venta

Store (Ubicaciones de tiendas)
- StoreKey (INT) - ID unico
- Name (NVARCHAR) - Nombre
- Country (NVARCHAR) - Pais
- State (NVARCHAR) - Provincia
- Square Meters (INT) - Tamanio
- Open Date (DATE) - Fecha apertura
- Close Date (DATE) - Fecha cierre
- Status (NVARCHAR) - Estado

Date (Dimension de tiempo)
- Date (DATE) - Fecha especifica
- Year (INT) - Anio
- Month (NVARCHAR) - Nombre mes
- Month Number (INT) - Numero 1-12
- Quarter (NVARCHAR) - Q1, Q2, Q3, Q4
- Day of Week (NVARCHAR) - Monday, Tuesday, etc.
- Day of Week Number (INT) - 1-7
- Working Day (BIT) - 1=si, 0=no

Sales (Transacciones - TABLA CENTRAL)
- Order Number (BIGINT) - ID orden
- Line Number (INT) - Numero linea
- Order Date (DATE) - Fecha orden
- Delivery Date (DATE) - Fecha entrega
- CustomerKey (INT) - FK a Customer
- StoreKey (INT) - FK a Store
- ProductKey (INT) - FK a Product
- Quantity (INT) - Cantidad
- Unit Price (MONEY) - Precio unitario
- Net Price (MONEY) - Precio neto
- Unit Cost (MONEY) - Costo
- Currency Code (NVARCHAR) - Moneda
- Exchange Rate (FLOAT) - Tipo cambio

RELACIONES:
Sales.CustomerKey -> Customer.CustomerKey
Sales.ProductKey -> Product.ProductKey
Sales.StoreKey -> Store.StoreKey
Sales.[Order Date] -> Date.Date (para analisis temporal)

COLUMNAS CON ESPACIOS (usa [brackets]):
[Order Date], [Order Number], [Line Number], [Delivery Date], [Product Name],
[Unit Price], [Net Price], [Unit Cost], [Currency Code], [Exchange Rate],
[Square Meters], [Open Date], [Close Date], [Month Number], [Day of Week],
[Day of Week Number], [Working Day], [Zip Code]

EJEMPLOS DE QUERIES VALIDAS:

OK: SELECT COUNT(DISTINCT s.CustomerKey) FROM Sales s 
    WHERE s.[Order Date] >= '2024-01-01'

OK: SELECT p.[Product Name], SUM(s.Quantity) as total_vendido
    FROM Sales s JOIN Product p ON s.ProductKey = p.ProductKey
    GROUP BY p.[Product Name] ORDER BY total_vendido DESC

MAL: SELECT * FROM fact_asistencias (no existe en Contoso)
MAL: SELECT * FROM Sales WHERE DATETRUNC (SQL Server usa DATEPART)
MAL: SELECT * FROM Sales s WHERE s.fecha_asistencia (no existe esta columna)

====================================================
"""


def _format_table_for_prompt(table: TableMetadata) -> List[str]:
    """
    Formatea una tabla individual para el prompt.
    
    Args:
        table: Metadatos de la tabla
        
    Returns:
        Lista de líneas de texto formateadas
    """
    lines = [
        f"📋 TABLA: [{table.name}] ({table.table_type})",
        f"   Descripción: {table.description}",
        f"   Contexto: {table.business_context}",
        "",
        "   COLUMNAS:",
    ]
    
    for col in table.columns:
        constraint_str = ""
        if col.constraints:
            constraint_str = f" [{', '.join(c.value for c in col.constraints)}]"
        
        fk_str = ""
        if col.foreign_key:
            fk_str = f" → FK: {col.foreign_key}"
        
        lines.append(
            f"     • {col.name} ({col.type.value}){constraint_str}{fk_str}"
        )
        lines.append(f"       └─ {col.description}")
    
    lines.append("")
    lines.append("   EJEMPLOS DE PREGUNTAS QUE RESUELVE:")
    for i, query in enumerate(table.sample_queries, 1):
        lines.append(f"     {i}. {query}")
    
    return lines


def _generate_join_guide() -> List[str]:
    """
    Genera una guía de JOINs correctos para el LLM.
    
    Returns:
        Lista de líneas de texto
    """
    lines = [
        "",
        "=" * 80,
        "GUÍA DE JOINS - STAR SCHEMA",
        "=" * 80,
        "",
        "FACT_ASISTENCIAS puede hacer JOIN con:",
        "  1. dim_beneficiarios ON fact_asistencias.beneficiario_id = dim_beneficiarios.beneficiario_id",
        "  2. dim_productos_servicios ON fact_asistencias.producto_id = dim_productos_servicios.producto_id",
        "",
        "EJEMPLO CORRECTO:",
        "  SELECT",
        "    b.nombre_completo,",
        "    p.nombre_item,",
        "    SUM(f.cantidad) as total_cantidad,",
        "    SUM(f.costo_real) as gasto_total",
        "  FROM fact_asistencias f",
        "  JOIN dim_beneficiarios b ON f.beneficiario_id = b.beneficiario_id",
        "  JOIN dim_productos_servicios p ON f.producto_id = p.producto_id",
        "  WHERE f.fecha_asistencia >= '2024-01-01'",
        "  GROUP BY b.beneficiario_id, p.producto_id",
        "  ORDER BY gasto_total DESC",
        "",
    ]
    return lines


def _generate_audit_notes() -> List[str]:
    """
    Genera notas especiales sobre auditoría y trazabilidad forense.
    
    Returns:
        Lista de líneas de texto
    """
    lines = [
        "=" * 80,
        "COLUMNAS DE AUDITORÍA FORENSE (CRÍTICAS)",
        "=" * 80,
        "",
        "La tabla fact_asistencias incluye columnas especiales para investigación:",
        "",
        "  • usuario_registrador: Quién registró la transacción (responsabilidad)",
        "  • metodo_verificacion: CÓMO se verificó (crítico para detectar fraude)",
        "  • observaciones_auditor: Notas de investigación",
        "  • timestamp_registro: CUÁNDO exacto (detecta patrones sospechosos)",
        "  • ip_registrador: DÓNDE se registró (múltiples ubicaciones = sospechoso)",
        "  • estado_verificacion: Estado de auditoría",
        "  • flag_anomalia: ¿Hay inconsistencias detectadas?",
        "",
        "MÉTODOS DE VERIFICACIÓN VÁLIDOS:",
        "  • biometrico: Huella digital, facial",
        "  • documento: Presentación de documento oficial",
        "  • testigo: Tercero verificó",
        "  • declaracion_beneficiario: Solo el beneficiario afirma (alto riesgo)",
        "  • otro: Especificar en observaciones",
        "",
        "⚠️  REGLAS PARA NL2SQL:",
        "  - Siempre filtrar por fecha relevante (fact_asistencias.fecha_asistencia)",
        "  - Incluir metodo_verificacion en consultas de auditoría",
        "  - Flag transacciones con flag_anomalia = true cuando sea relevante",
        "  - Si pregunta por 'fraude' o 'irregularidad', usar metodo_verificacion = 'declaracion_beneficiario'",
        "  - Para análisis de cobertura, contar beneficiarios_id distintos",
        "",
    ]
    return lines


def get_table_by_name(table_name: str) -> Optional[TableMetadata]:
    """
    Obtiene metadatos de una tabla por nombre.
    
    Args:
        table_name: Nombre de la tabla (ej: 'fact_asistencias')
        
    Returns:
        TableMetadata si existe, None en caso contrario
    """
    return DB_SCHEMA_METADATA.get(table_name)


def get_all_tables() -> List[TableMetadata]:
    """
    Obtiene lista de todas las tablas disponibles.
    
    Returns:
        Lista de TableMetadata
    """
    return list(DB_SCHEMA_METADATA.values())


def get_dimension_tables() -> List[TableMetadata]:
    """
    Obtiene solo las tablas de dimensión.
    
    Returns:
        Lista de TableMetadata con table_type == "DIMENSION"
    """
    return [t for t in DB_SCHEMA_METADATA.values() if t.table_type == "DIMENSION"]


def get_fact_tables() -> List[TableMetadata]:
    """
    Obtiene solo las tablas de hechos.
    
    Returns:
        Lista de TableMetadata con table_type == "FACT"
    """
    return [t for t in DB_SCHEMA_METADATA.values() if t.table_type == "FACT"]


def validate_column_exists(table_name: str, column_name: str) -> bool:
    """
    Valida si una columna existe en una tabla.
    
    Args:
        table_name: Nombre de la tabla
        column_name: Nombre de la columna
        
    Returns:
        True si existe, False en caso contrario
    """
    table = get_table_by_name(table_name)
    if not table:
        return False
    
    return any(col.name == column_name for col in table.columns)


# ============================================================================
# MAIN: Demostración
# ============================================================================

if __name__ == "__main__":
    print(get_schema_prompt())
    print("\n\n" + "=" * 80)
    print("VALIDACIÓN DE SCHEMA")
    print("=" * 80)
    print(f"\n✅ Total de tablas: {len(DB_SCHEMA_METADATA)}")
    print(f"✅ Dimensiones: {len(get_dimension_tables())}")
    print(f"✅ Hechos: {len(get_fact_tables())}")
    
    # Test: validar columna
    print(f"\n✅ ¿Existe 'fact_asistencias.usuario_registrador'? {validate_column_exists('fact_asistencias', 'usuario_registrador')}")
    print(f"✅ ¿Existe 'fact_asistencias.columna_inexistente'? {validate_column_exists('fact_asistencias', 'columna_inexistente')}")
