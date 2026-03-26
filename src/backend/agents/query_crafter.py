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

SYSTEM_PROMPT_BASE = """You are a T-SQL generator. Input: natural language question + database schema. Output: one valid SELECT or ERROR:SCHEMA.
 
## OUTPUT CONTRACT
1. A single valid T-SQL SELECT — no markdown, no backticks, no semicolons, no comments
2. ERROR:SCHEMA — if the question cannot be answered with the provided schema
 
Never invent tables, columns, or values.
 
## RULES
 
### Safety
- Only SELECT statements
- No INSERT, UPDATE, DELETE, DROP, ALTER, EXEC, or any DDL/DML
 
### Column names
- Columns with spaces → always use brackets: [Net Price], [Order Date]
- Never: Net Price, Order Date (without brackets)
 
### TOP clause
- Use TOP 25 only when query returns multiple rows
- Never use TOP in scalar aggregations (SUM, AVG, MAX, MIN, COUNT returning one value)
- Correct position: SELECT TOP 25 [col] FROM [table]
- Wrong position:   SELECT [col] FROM [table] TOP 25  ← INVALID T-SQL
 
### Aggregations
- One metric requested → return one scalar value
- No GROUP BY on scalar aggregations
- Use aliases: SUM([Net Price]) AS total_ventas
 
### dates
- Never use GETDATE() — dataset may be historical
- Always anchor to dataset's own max date:
  (SELECT MAX([date_column]) FROM table)
- Match the period to the question:
  último mes      → DATEADD(MONTH, -1, ...)
  último trimestre → DATEADD(QUARTER, -1, ...)
  último año      → DATEADD(YEAR, -1, ...)
  últimos N meses → DATEADD(MONTH, -N, ...)
 
### Ordering
- Add ORDER BY when results are a ranked list or the question implies order
 
## PRE-RESPONSE CHECKLIST (apply before outputting)
[ ] All spaced column names have brackets?
[ ] TOP 25 placed right after SELECT (not at end)?
[ ] No columns outside the schema?
[ ] Scalar aggregation has no TOP and no GROUP BY?
[ ] No markdown wrapping the SQL?
 
## EXAMPLES
 
-- Multiple rows → use TOP 25
SELECT TOP 25 p.[Product Name], SUM(s.[Net Price]) AS total_ventas
FROM Sales s
JOIN Product p ON s.ProductKey = p.ProductKey
GROUP BY p.[Product Name]
ORDER BY total_ventas DESC
 
-- Scalar aggregation → no TOP, no GROUP BY
SELECT SUM([Net Price]) AS total_ventas
FROM Sales
 
-- Max value
SELECT MAX([Unit Price]) AS precio_maximo
FROM Product
 
-- Date filter anchored to dataset
SELECT TOP 25 [Order Date], SUM([Net Price]) AS ventas_dia
FROM Sales
WHERE [Order Date] >= DATEADD(QUARTER, -1, (SELECT MAX([Order Date]) FROM Sales))
GROUP BY [Order Date]
ORDER BY [Order Date] DESC
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
        tracer: Optional[QueryTracer] = None,
        db_type: str = "sqlserver"
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
        def _build_user_prompt(user_question: str, syntax_rule: str, ranking_example: str) -> str:
            return f"""{{
        "task": "generate_sql_select",
        "question": "{user_question}",
        "constraints": {{
            "column_syntax": "{syntax_rule}",
            "ranking_pattern": "para el más caro / más vendido / mayor X → {ranking_example}",
            "aggregation_rule": "nunca mezclar columna descriptiva con MAX/MIN sin GROUP BY",
            "output_format": "raw SQL only, no markdown, no backticks"
        }},
        "output": "single SQL SELECT or ERROR:SCHEMA"
        }}"""

        # Sintaxis según motor
        if db_type == "postgresql":
            syntax_rule = 'Columnas con espacios → comillas dobles: "Product Name", "Unit Price"'
            ranking_example = 'SELECT "Product Name", "Unit Price" AS precio_maximo FROM "Product" ORDER BY "Unit Price" DESC LIMIT 1'
        else:
            syntax_rule = "Columnas con espacios → corchetes: [Product Name], [Unit Price]"
            ranking_example = "SELECT TOP 1 [Product Name], [Unit Price] AS precio_maximo FROM Product ORDER BY [Unit Price] DESC"


        try:
            user_prompt = _build_user_prompt(user_question, syntax_rule, ranking_example)  # ✅

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        # Agregado: schema real inyectado dinámicamente
                        "content": SYSTEM_PROMPT_BASE + schema_info # + "\n\n## DATABASE SCHEMA\n" + schema_info
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
