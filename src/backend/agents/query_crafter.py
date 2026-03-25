"""
VeriQuery — Query Crafter
=========================
Genera SQL a partir de lenguaje natural usando el schema real de la BD.

# Correccion: schema llega como parámetro externo (no se carga en __init__)
# Correccion: eliminado import de table_mapping (hardcodeado)
# Correccion: eliminado pyodbc directo — la conexión la maneja factory.py
# Agregado: recibe QueryTracer para registrar cada paso
# Agregado: devuelve reasoning_data con datos estructurados del proceso
# v2: SYSTEM_PROMPT_BASE reescrito desde cero — sin patches, sin ejemplos hardcodeados
"""

import os
import logging
import re
from typing import Optional
from openai import AzureOpenAI

from src.backend.core.tracer import QueryTracer

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — reescrito desde cero
#
# Estructura en 3 secciones ordenadas por prioridad:
#   1. ROL          — qué es y para qué existe
#   2. CONTRATO     — exactamente qué puede devolver y cuándo
#   3. SINTAXIS     — reglas técnicas T-SQL concisas + few-shot genéricos
#
# Principio: el modelo NUNCA debe inventar. Si no puede responder con el
# schema que recibe → devuelve ERROR:SCHEMA (texto plano, sin SQL).
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_BASE = """Eres un traductor de lenguaje natural a SQL Server T-SQL.

Recibirás una pregunta y el schema real de una base de datos.
Tu único trabajo es generar un SELECT correcto que responda exactamente la pregunta
usando SOLO las tablas y columnas del schema.

## CONTRATO DE SALIDA

Solo podés devolver:

A) Un SELECT válido en T-SQL (sin markdown, sin comentarios, sin ;)
B) ERROR:SCHEMA si no es posible responder con el schema

NUNCA inventes tablas, columnas ni valores.

## REGLAS

- Solo SELECT (no INSERT, UPDATE, DELETE, etc.)
- Un solo statement
- Usá SOLO tablas y columnas del schema

### Columnas
- Si una columna tiene espacios → SIEMPRE usar corchetes [columna]
- Ejemplo correcto: [Net Price], [Order Date]
- Ejemplo incorrecto: Net Price

### TOP
- Usá TOP 25 SOLO si la consulta devuelve múltiples filas
- NO usar TOP en agregaciones escalares (SUM, COUNT, etc.)
- Sintaxis correcta: SELECT TOP 25 col FROM tabla

### Agregaciones
- Si la pregunta pide un total → devolver un solo valor
- NO usar GROUP BY en agregaciones escalares
- Usar: SUM, COUNT, AVG, MAX, MIN

### Fechas
- NO usar GETDATE()
- Usar siempre la fecha máxima del dataset:
  (SELECT MAX([columna_fecha]) FROM tabla)

Ejemplo:
WHERE [Order Date] >= DATEADD(MONTH, -12, (SELECT MAX([Order Date]) FROM Sales))

## VALIDACIÓN FINAL OBLIGATORIA

Antes de responder:
- Verificá que todas las columnas con espacios tengan []
- Verificá que no haya columnas fuera del schema
- Si algo falla → corregir

## EJEMPLO CRÍTICO

Correcto:
SELECT SUM([Net Price]) FROM Sales

Incorrecto:
SELECT SUM(Net Price) FROM Sales
"""


class QueryCrafter:
    """
    Genera SQL desde lenguaje natural.
    Compatible con cualquier BD — el schema llega como parámetro externo.
    """

    def __init__(self, azure_client: Optional[AzureOpenAI] = None):
        """
        Args:
            azure_client: Cliente Azure OpenAI reutilizable.
                El orquestador pasa su propio cliente para evitar
                instancias duplicadas.

        # Correccion: eliminado parámetro connection_string y carga de schema.
        # El schema ahora llega en generate_sql() como parámetro.
        # Esto permite cambiar de BD sin reiniciar el servidor.
        """
        if azure_client is None:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            self.client = azure_client

        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")

    def generate_sql(
        self,
        user_question: str,
        schema_info: str,
        tracer: Optional[QueryTracer] = None
    ) -> dict:
        """
        Genera SQL a partir de pregunta en lenguaje natural.

        Args:
            user_question: Pregunta del usuario
            schema_info:   Schema real de la BD activa (viene del orquestador)
            tracer:        QueryTracer para registrar este paso (opcional)

        Returns:
            dict con sql, tables_used, reasoning_data, tokens, cost_usd
        """
        logger.info(f"🔄 Generando SQL para: {user_question}")

        # Agregado: trazar entrada
        if tracer:
            tracer.step(
                archivo="query_crafter",
                paso="generar_sql",
                entrada=f"Pregunta: '{user_question}' | Schema: {len(schema_info)} chars",
                accion="Llamando a Azure OpenAI con schema real inyectado en prompt",
                salida="pendiente..."
            )

        try:
            user_prompt = f"""
Pregunta del usuario: "{user_question}"

Generá un SELECT en SQL Server usando SOLO el schema proporcionado.

Reglas:
- Solo SELECT, sin markdown ni backticks
- Usá únicamente tablas y columnas del schema
- No inventes nada → si falta información, devolvé ERROR:SCHEMA
- Columnas con espacios deben ir entre corchetes [columna]

Formato:
- Usá TOP 25 SOLO si la consulta devuelve múltiples filas
- NO uses TOP en agregaciones escalares (SUM, COUNT, etc.)
- Ordená los resultados si tiene sentido (ORDER BY)

Salida:
- Devolvé SOLO el SQL o ERROR:SCHEMA
"""

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        # Agregado: schema real inyectado dinámicamente
                        "content": SYSTEM_PROMPT_BASE + "\n\n" + schema_info
                    },
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )

            sql = response.choices[0].message.content.strip()
            sql = sql.replace("```sql", "").replace("```", "").replace("`", "").strip()
            tables_used = self._extract_tables(sql)

            reasoning_data = {
                "tables_identified": tables_used,
                "question_processed": user_question,
                "tokens_prompt": response.usage.prompt_tokens,
                "tokens_completion": response.usage.completion_tokens,
            }

            cost = (
                response.usage.prompt_tokens * 0.00000015 +
                response.usage.completion_tokens * 0.0000006
            )

            logger.info(f"✅ SQL generada. Tablas: {tables_used}")

            # Agregado: trazar salida
            if tracer:
                tracer.step(
                    archivo="query_crafter",
                    paso="sql_generada",
                    entrada=f"Tokens: {response.usage.total_tokens}",
                    accion="SQL extraída y limpiada de markdown",
                    salida=f"Tablas detectadas: {tables_used} → pasa a nl2sql_generator"
                )

            return {
                "sql": sql,
                "tables_used": tables_used,
                "reasoning_data": reasoning_data,
                "tokens": response.usage.total_tokens,
                "cost_usd": cost
            }

        except Exception as e:
            logger.error(f"❌ Error generando SQL: {e}")
            if tracer:
                tracer.error("query_crafter", "generar_sql", str(e), user_question)
            return {
                "sql": "",
                "error": str(e),
                "tables_used": [],
                "reasoning_data": {},
                "tokens": 0,
                "cost_usd": 0
            }

    def _extract_tables(self, sql: str) -> list:
        pattern = r'(?:FROM|JOIN)\s+\[?([a-zA-Z_][a-zA-Z0-9_]*)\]?'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        return list(set(matches))
