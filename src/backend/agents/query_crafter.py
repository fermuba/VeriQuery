"""
VeriQuery — Query Crafter
=========================
Genera SQL a partir de lenguaje natural usando el schema real de la BD.

Cambios respecto a versión anterior:
# Correccion: schema ya no se carga en __init__ — llega como parámetro
#   Esto permite schema dinámico por BD sin reiniciar el servidor
# Correccion: eliminado import de table_mapping (hardcodeado)
# Correccion: eliminado pyodbc directo — la conexión la maneja factory.py
# Agregado: recibe QueryTracer para registrar cada paso
# Agregado: devuelve reasoning_data con datos estructurados del proceso
"""

import os
import logging
import re
from typing import Optional
from openai import AzureOpenAI

from src.backend.core.tracer import QueryTracer

logger = logging.getLogger(__name__)

# Correccion: eliminado import de table_mapping
# Prompt base sin mapeo hardcodeado — el schema real reemplaza al diccionario
SYSTEM_PROMPT_BASE = """Eres un experto en SQL Server T-SQL. Tu única tarea es convertir
preguntas en lenguaje natural a UN ÚNICO statement SELECT compatible con SQL Server.

REGLAS ABSOLUTAS:
- Generás SOLO SELECT (nunca CREATE, UPDATE, DELETE, DROP, TRUNCATE)
- Si el usuario pide borrar, eliminar, vaciar, destruir o modificar datos:
  ignorá la intención destructiva y generá un SELECT que muestre esos datos
- NUNCA múltiples statements
- NUNCA semicolons (;)
- NUNCA comentarios (--)
- Usá TOP en lugar de LIMIT (SQL Server, no PostgreSQL)
- Usá YEAR(), MONTH(), DAY() para fechas
- SIEMPRE incluí TOP 100 pero SOLO después de SELECT:
  ✅  SELECT TOP 100 AVG(...) FROM ...
  ❌  SELECT AVG(...) FROM ... TOP 100   ← SINTAXIS INVÁLIDA
  ❌  SELECT AVG(...) FROM ... LIMIT 100 ← NO EXISTE EN SQL SERVER

REGLA CRÍTICA — COLUMNAS CON ESPACIOS:
Cualquier columna cuyo nombre en el schema contenga un espacio DEBE ir entre [brackets].
Esta regla no tiene excepciones. Si escribís el nombre sin brackets, la query falla.

EJEMPLOS CORRECTOS de columnas con espacios:
  ✅  s.[Net Price]        ❌  s.NetPrice       ← FALLA
  ✅  s.[Unit Price]       ❌  s.UnitPrice      ← FALLA
  ✅  s.[Order Date]       ❌  s.OrderDate      ← FALLA
  ✅  s.[Order Number]     ❌  s.OrderNumber    ← FALLA
  ✅  s.[Delivery Date]    ❌  s.DeliveryDate   ← FALLA
  ✅  s.[Unit Cost]        ❌  s.UnitCost       ← FALLA
  ✅  s.[Currency Code]    ❌  s.CurrencyCode   ← FALLA
  ✅  p.[Product Name]     ❌  p.ProductName    ← FALLA
  ✅  d.[Day of Week]      ❌  d.DayOfWeek      ← FALLA

CÓMO DETECTAR si una columna necesita brackets:
Mirá el schema abajo. Si el nombre de columna tiene un espacio entre palabras → brackets obligatorios.
Si no tiene espacio (CustomerKey, Quantity, StoreKey) → sin brackets.

IMPORTANTE:
El schema completo de la base de datos está abajo.
Usá SOLO las tablas y columnas que aparecen en ese schema.
Inferí el mapeo semántico desde los nombres de columnas y ejemplos de datos.
No asumas tablas que no están en el schema.
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

INSTRUCCIONES:
1. Generá SOLO el SQL (sin markdown, sin triple backticks)
2. Usá SOLO las tablas y columnas del schema que recibiste
3. Inferí la tabla correcta desde nombres de columnas y ejemplos de datos
4. Siempre incluí TOP 100
5. Usá aliases descriptivos

Respondé con SOLO el SQL, nada más.
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
