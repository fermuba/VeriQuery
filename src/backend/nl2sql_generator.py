"""
VeriQuery — NL2SQL Generator (Orquestador)
==========================================
Coordin el flujo completo NL → SQL → Respuesta.

# v2 — Mejoras arquitectónicas:
# - Eliminado schema_cache: siempre recarga fresco al cambiar de BD
# - Integrado IntentValidator (LLM): reemplaza al AmbiguityDetector por keywords
# - Integrado SemanticValidator (LLM): verifica que el SQL responde la pregunta
# - Detecta ERROR:SCHEMA devuelto por QueryCrafter cuando el schema no alcanza
# - Registra schema_loaded_at en el tracer para trazabilidad
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from openai import AzureOpenAI

from src.backend.agents.intent_validator import IntentValidator
from src.backend.agents.semantic_validator import SemanticValidator
from src.backend.agents.query_crafter import QueryCrafter
from src.backend.agents.sql_normalizer import SQLNormalizer
from src.backend.database.factory import get_database_connector
from src.backend.core.tracer import QueryTracer

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Agregado: map de schema_name por tipo de BD
# Cada motor de BD usa un nombre distinto para el schema por defecto
DB_SCHEMA_NAMES = {
    "sqlserver":  "dbo",
    "postgresql": "public",   # PostgreSQL, Supabase, Azure PostgreSQL
    "sqlite":     "main",
}


class NL2SQLGenerator:
    """
    Orquestador del flujo NL → SQL.
    Compatible con SQL Server, PostgreSQL (Supabase, Azure), SQLite.
    """

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")

        # Schema activo — sin caché. Cada cambio de BD recarga desde el conector.
        self._active_schema: Optional[str] = None
        self._active_db_name: Optional[str] = None
        self._active_db_type: Optional[str] = None
        self._active_connector = None
        self._schema_loaded_at: Optional[str] = None  # timestamp de carga del schema

        # Agentes del pipeline
        self.intent_validator = IntentValidator(azure_client=self.client)
        self.semantic_validator = SemanticValidator(azure_client=self.client)
        self.query_crafter = QueryCrafter(azure_client=self.client)
        self.sql_normalizer = SQLNormalizer()

        self._load_default_database()
        logger.info("✅ NL2SQLGenerator inicializado")

    def _load_default_database(self) -> None:
        """Carga la BD configurada en .env al iniciar."""
        try:
            db_type = os.getenv("DATABASE_TYPE", "sqlserver").lower()
            db_name = os.getenv("DB_NAME", "default")

            connector = get_database_connector()
            connector.connect()

            schema = self._load_schema_from_connector(
                connector=connector,
                db_name=db_name,
                db_type=db_type
            )

            # Sin caché: guardar solo el schema activo
            self._active_schema = schema
            self._active_db_name = db_name
            self._active_db_type = db_type
            self._active_connector = connector
            self._schema_loaded_at = datetime.now().isoformat()

            logger.info(
                f"✅ BD por defecto: {db_name} ({db_type}) "
                f"— {len(schema)} chars de schema"
            )
        except Exception as e:
            logger.error(f"❌ No se pudo cargar BD por defecto: {e}")

    def set_active_database(
        self,
        db_name: str,
        connector,
        db_type: str = "sqlserver"
    ) -> dict:
        """
        Cambia la BD activa en runtime sin reiniciar el servidor.
        Llamado desde POST /api/connect en main.py.

        IMPORTANTE: sin caché — siempre recarga el schema fresco desde el conector.
        Esto evita que información de una BD anterior contamine las queries.

        Args:
            db_name:   identificador de la BD (ej: "contoso", "supabase_ong")
            connector: instancia ya conectada
            db_type:   "sqlserver" | "postgresql" | "sqlite"

        Returns:
            dict con success, db_name, schema_chars
        """
        # Limpiar estado de la BD anterior antes de cargar la nueva
        prev_db = self._active_db_name
        self._active_schema = None
        self._active_db_name = None
        self._active_db_type = None
        self._active_connector = None
        self._schema_loaded_at = None

        if prev_db:
            logger.info(f"🧹 Schema anterior de '{prev_db}' limpiado")

        try:
            schema = self._load_schema_from_connector(
                connector=connector,
                db_name=db_name,
                db_type=db_type
            )

            # Guardar schema activo (sin caché entre BDs)
            self._active_schema = schema
            self._active_db_name = db_name
            self._active_db_type = db_type
            self._active_connector = connector
            self._schema_loaded_at = datetime.now().isoformat()

            logger.info(
                f"✅ BD activa → '{db_name}' ({db_type}) "
                f"— schema recargado {len(schema)} chars "
                f"— cargado a las {self._schema_loaded_at}"
            )
            return {
                "success": True,
                "db_name": db_name,
                "db_type": db_type,
                "schema_chars": len(schema),
                "schema_loaded_at": self._schema_loaded_at
            }
        except Exception as e:
            logger.error(f"❌ Error cargando schema de '{db_name}': {e}")
            return {"success": False, "error": str(e)}

    def get_active_schema(self) -> str:
        if self._active_schema:
            return self._active_schema
        return "⚠️ Schema no disponible — conectá una BD primero"

    def generate_sql(
        self,
        natural_language_query: str,
        conversation_history: list = None
    ) -> dict:
        """
        Orquesta el flujo completo para una consulta.

        Returns:
            dict con type + trace_steps (si TRACE_RESPONSE=true)
        """
        if conversation_history is None:
            conversation_history = []

        tracer = QueryTracer(question=natural_language_query)

        # ── PASO 1: Schema activo ─────────────────────────────────────────
        schema_info = self.get_active_schema()

        tracer.step(
            archivo="nl2sql_generator",
            paso="schema",
            entrada=f"BD: {self._active_db_name} ({self._active_db_type})",
            accion="Obteniendo schema activo",
            salida=(
                f"{len(schema_info)} chars — cargado: {self._schema_loaded_at}"
                if self._schema_loaded_at
                else "⚠️ Sin schema"
            )
        )

        if "⚠️" in schema_info:
            tracer.error(
                "nl2sql_generator", "schema",
                "Schema no disponible — no hay BD activa"
            )
            tracer.set_decision("RECHAZO")
            trace_data = tracer.finalize()
            return {
                "type": "error",
                "message": "No hay base de datos activa. Conectá una BD primero.",
                "trace_steps": trace_data
            }

        # ── PASO 2: Historial (Enriquecer contexto antes de clasificar) ───
        enriched_query = self._enrich_with_history(
            natural_language_query, conversation_history, tracer
        )

        # ── PASO 2b: Detectar si el usuario está respondiendo una aclaración ─
        # Si el último mensaje del asistente fue una pregunta de aclaración,
        # el usuario ya está respondiendo — no re-preguntar, generar SQL directo.
        _last_was_clarification = (
            len(conversation_history) >= 2
            and conversation_history[-1].get("role") == "assistant"
            and conversation_history[-1].get("type") == "necesita_aclaracion"
        )

        # ── PASO 3: Validar intención ─────────────────────────────────────
        if _last_was_clarification:
            # Bypass total del IntentValidator: el usuario ya respondió la aclaración.
            # La pregunta ya fue enriquecida con el historial en PASO 2.
            intent = {
                "decision": "GENERAR_SQL",
                "reason": "Respuesta directa a aclaración previa — bypass IntentValidator",
                "clarification_question": None,
                "clarification_options": None,
            }
            tracer.step(
                archivo="intent_validator",
                paso="bypass_aclaracion",
                entrada=enriched_query[:80],
                accion="Última respuesta del asistente era aclaración → GENERAR_SQL forzado",
                salida="GENERAR_SQL (bypass)"
            )
        else:
            tracer.step(
                archivo="intent_validator",
                paso="clasificar",
                entrada=enriched_query[:80],
                accion="Clasificando intención vía LLM (GENERAR_SQL / NECESITA_ACLARACION / NO_SOPORTADO)",
                salida="pendiente..."
            )

            intent = self.intent_validator.validate(
                question=enriched_query,
                schema_info=schema_info,
                history=conversation_history
            )

            tracer.step(
                archivo="intent_validator",
                paso="resultado",
                entrada=natural_language_query,
                accion=f"Decisión: {intent['decision']}",
                salida=intent.get("reason", "")[:120]
            )


        if intent["decision"] == "NECESITA_ACLARACION":
            tracer.set_decision("ACLARACION")
            trace_data = tracer.finalize()
            return {
                "type": "necesita_aclaracion",
                "reason": intent["reason"],
                "clarification_question": intent.get("clarification_question"),
                "clarification_options": intent.get("clarification_options"),
                "natural_query": natural_language_query,
                "trace_steps": trace_data
            }

        if intent["decision"] == "NO_SOPORTADO":
            tracer.set_decision("RECHAZO")
            trace_data = tracer.finalize()
            return {
                "type": "no_soportado",
                "reason": intent["reason"],
                "natural_query": natural_language_query,
                "trace_steps": trace_data
            }

        # ── PASO 4: Generar SQL ───────────────────────────────────────────
        crafter_result = self.query_crafter.generate_sql(
            user_question=enriched_query,
            schema_info=schema_info,
            tracer=tracer
        )

        if "error" in crafter_result and not crafter_result.get("sql"):
            tracer.error(
                "query_crafter", "generar_sql",
                crafter_result.get("error", "Error desconocido"),
                enriched_query
            )
            tracer.set_decision("RECHAZO")
            trace_data = tracer.finalize()
            return {
                "type": "error",
                "message": f"No pude generar la consulta: {crafter_result.get('error')}",
                "trace_steps": trace_data
            }

        # ── PASO 4b: Detectar ERROR:SCHEMA devuelto por el LLM ───────────
        sql_raw = crafter_result.get("sql", "")
        if "ERROR:SCHEMA" in sql_raw:
            tracer.step(
                archivo="query_crafter",
                paso="error_schema_rescate",
                entrada=sql_raw[:80],
                accion="Schema insuficiente o ambiguo. Disparando agente de rescate.",
                salida="Generando pregunta de aclaración específica..."
            )
            clarification_msg = self._generate_rescue_clarification(
                natural_language_query,
                schema_info,
                tracer
            )
            tracer.set_decision("ACLARACION")
            trace_data = tracer.finalize()
            return {
                "type": "necesita_aclaracion",
                "reason": "Falta información específica o hay ambigüedad para mapear el schema.",
                "clarification_question": clarification_msg,
                "natural_query": natural_language_query,
                "trace_steps": trace_data
            }

        raw_sql = crafter_result["sql"]
        tables_used = crafter_result.get("tables_used", [])

        # ── PASO 4c: Normalización AST (sqlglot) ─────────────────────────
        norm_result = self.sql_normalizer.normalize(
            sql=raw_sql,
            dialect_db_type=self._active_db_type,
            tracer=tracer
        )

        if not norm_result["success"]:
            tracer.error("sql_normalizer", "normalize", norm_result["error"], raw_sql)
            tracer.set_decision("RECHAZO")
            trace_data = tracer.finalize()
            return {
                "type": "error",
                "message": f"Error de sintaxis en la consulta generada: {norm_result['error']}",
                "trace_steps": trace_data
            }

        sql = norm_result["normalized_sql"]

        # ── PASO 5: Validación estructural SQL ────────────────────────────
        validation = self._validate_sql(sql, tracer)

        # ── PASO 6: Validación semántica (SQL vs intención) ───────────────
        tracer.step(
            archivo="semantic_validator",
            paso="validar",
            # Fix 2: usar enriched_query para que el validador compare contra
            # la intención COMPLETA, no contra la respuesta corta del usuario
            entrada=f"Pregunta enriquecida: '{enriched_query[:60]}'",
            accion="Verificando que el SQL responde la pregunta",
            salida="pendiente..."
        )

        semantic = self.semantic_validator.validate(
            question=enriched_query,   # Fix 2: enriquecida, no la original corta
            sql=sql
        )

        tracer.step(
            archivo="semantic_validator",
            paso="resultado",
            entrada=sql[:80] + "..." if len(sql) > 80 else sql,
            accion=f"Válido semánticamente: {semantic['valid']}",
            salida=semantic.get("reason", "")[:120]
        )

        if not semantic["valid"]:
            # Fix 3: usar rescue_clarification con schema real en lugar de
            # la pregunta genérica que causa bucle infinito
            clarification_msg = self._generate_rescue_clarification(
                enriched_query, schema_info, tracer
            )
            tracer.set_decision("ACLARACION")
            trace_data = tracer.finalize()
            return {
                "type": "necesita_aclaracion",
                "reason": semantic["reason"],
                "clarification_question": clarification_msg,
                "natural_query": natural_language_query,
                "trace_steps": trace_data
            }

        # ── PASO 7: Confidence ────────────────────────────────────────────
        confidence, confidence_label = self._calculate_confidence(
            sql, tables_used, validation
        )

        # ── PASO 8: Reasoning + Explanation ──────────────────────────────
        reasoning = self._build_reasoning(
            natural_language_query, enriched_query,
            sql, tables_used, validation, tracer
        )
        explanation = self._generate_explanation(
            natural_language_query, sql, tracer
        )

        # Finalizar tracer — escribe logs, devuelve dict si TRACE_RESPONSE=true
        tracer.set_decision("SQL")
        trace_data = tracer.finalize()

        return {
            "type": "answer",
            "natural_query": natural_language_query,
            "sql": sql,
            "explanation": explanation,
            "reasoning": reasoning,
            "valid": validation["valid"],
            "validation_notes": validation["notes"],
            "tables_used": tables_used,
            "confidence": confidence,
            "confidence_label": confidence_label,
            "tokens_used": crafter_result.get("tokens", 0),
            "cost_usd": crafter_result.get("cost_usd", 0),
            "active_db": self._active_db_name,
            "active_db_type": self._active_db_type,
            "schema_loaded_at": self._schema_loaded_at,
            "trace_steps": trace_data
        }

    # ── CARGA DE SCHEMA ───────────────────────────────────────────────────

    def _load_schema_from_connector(
        self,
        connector,
        db_name: str,
        db_type: str = "sqlserver"
    ) -> str:
        """
        Carga schema real desde cualquier conector.

        Agregado: db_type determina el TABLE_SCHEMA correcto:
          - sqlserver  → 'dbo'
          - postgresql → 'public'  (Supabase, Azure PostgreSQL)
          - sqlite     → 'main'

        Esto resuelve el problema de tablas no encontradas
        al conectar a PostgreSQL/Supabase desde código escrito para SQL Server.
        """
        # Agregado: resolver schema_name según el motor
        schema_name = DB_SCHEMA_NAMES.get(db_type.lower(), "dbo")
        logger.info(
            f"📊 Cargando schema de '{db_name}' "
            f"({db_type}) — TABLE_SCHEMA='{schema_name}'"
        )

        try:
            schema_text = (
                f"=== SCHEMA: {db_name} ({db_type}) ===\n"
                f"TABLE_SCHEMA: {schema_name}\n\n"
            )

            # Agregado: query parametrizada con schema_name dinámico
            tables_result = connector.execute_query(f"""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{schema_name}'
                ORDER BY TABLE_NAME
            """)

            if not tables_result.success:
                raise Exception(
                    f"No se pudieron obtener tablas: {tables_result.error}"
                )

            tables = [row["TABLE_NAME"] for row in tables_result.data]
            logger.info(f"  → {len(tables)} tablas encontradas")

            for table_name in tables:
                # Columnas
                cols_result = connector.execute_query(f"""
                    SELECT
                        COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = '{table_name}'
                      AND TABLE_SCHEMA = '{schema_name}'
                    ORDER BY ORDINAL_POSITION
                """)

                if cols_result.success:
                    col_names = [col["COLUMN_NAME"] for col in cols_result.data]
                    schema_text += f"{table_name}({', '.join(col_names)})\n"
                else:
                    schema_text += f"{table_name}()\n"

            return schema_text.strip()

        except Exception as e:
            logger.error(f"❌ Error cargando schema de {db_name}: {e}")
            raise

    # ── MÉTODOS DE SOPORTE ────────────────────────────────────────────────

    def _enrich_with_history(
        self, question: str, history: list, tracer: QueryTracer
    ) -> str:
        if not history:
            return question
        recent = history[-4:]
        context = "\n".join(
            f"{'Usuario' if m['role']=='user' else 'Asistente'}: {m['content']}"
            for m in recent
        )
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un experto en reconstrucción de contexto. Tu tarea es tomar un historial de chat "
                            "y la respuesta actual del usuario (que puede ser corta como 'Sí', 'Net price') "
                            "y FUSIONARLA con la pregunta original del usuario para formar una única petición completa.\n"
                            "Ejemplo:\n"
                            "Historial:\nUsuario: Ventas por país\nAsistente: ¿Importe o Cantidad?\n"
                            "Actual: Importe\n"
                            "Tu salida: Dame el importe de ventas por país\n\n"
                            "NO respondas a la pregunta, SOLO devuelve la nueva oración reformulada de forma directa y clara."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Historial:\n{context}\n\nActual: {question}\n\nOrden completa reformulada:"
                    }
                ],
                max_tokens=150, temperature=0.1
            )
            enriched = response.choices[0].message.content.strip()
            if enriched != question:
                tracer.step(
                    archivo="nl2sql_generator",
                    paso="enriquecer_historial",
                    entrada=f"Original: '{question}'",
                    accion="Reformulando con contexto de conversación",
                    salida=f"Enriquecida: '{enriched}'"
                )
            return enriched
        except Exception as e:
            logger.warning(f"⚠️ No se pudo enriquecer pregunta: {e}")
            return question

    def _validate_sql(self, sql: str, tracer: QueryTracer) -> dict:
        import re
        notes = []
        valid = True

        if not sql:
            valid = False
            notes.append("❌ SQL vacía")
        elif not sql.strip().upper().startswith("SELECT"):
            valid = False
            notes.append("❌ Debe comenzar con SELECT")
        else:
            for cmd in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]:
                if re.search(rf"\b{cmd}\b", sql, re.IGNORECASE):
                    valid = False
                    notes.append(f"❌ Comando prohibido: {cmd}")

        if valid:
            notes.append("✅ SQL válida")

        tracer.step(
            archivo="nl2sql_generator",
            paso="validar_sql",
            entrada=sql[:80] + "..." if len(sql) > 80 else sql,
            accion="SELECT-only, sin comandos destructivos",
            salida=f"valid={valid} | {notes[0]}"
        )
        return {"valid": valid, "notes": notes}

    def _calculate_confidence(self, sql, tables, validation) -> tuple:
        import re
        confidence = 100.0
        if len(re.findall(r'\bJOIN\b', sql, re.IGNORECASE)) > 3:
            confidence -= 10
        if not validation["valid"]:
            confidence -= 50
        if not tables:
            confidence -= 20
        confidence = max(0, min(100, confidence))

        if confidence >= 90:
            label = "🟢 Muy alta"
        elif confidence >= 70:
            label = "🟡 Alta"
        elif confidence >= 50:
            label = "🟠 Media"
        else:
            label = "🔴 Baja — revisar"
        return confidence, label

    def _build_reasoning(
        self, question, enriched, sql, tables, validation, tracer
    ) -> str:
        data_text = (
            f"Tablas: {', '.join(tables) if tables else 'no detectadas'}\n"
            f"SQL válida: {'sí' if validation['valid'] else 'no'}\n"
        )
        if enriched != question:
            data_text += f"Pregunta interpretada: {enriched}\n"
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Explicá en 2-3 oraciones por qué se eligieron "
                            "estas tablas y filtros. Directo. Sin markdown."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Pregunta: '{question}'\n{data_text}\nSQL:\n{sql}"
                    }
                ],
                max_tokens=150, temperature=0.3
            )
            reasoning = response.choices[0].message.content.strip()
            tracer.step(
                archivo="nl2sql_generator",
                paso="reasoning",
                entrada=data_text,
                accion="LLM redacta razonamiento",
                salida=reasoning[:80] + "..." if len(reasoning) > 80 else reasoning
            )
            return reasoning
        except Exception:
            return f"Tablas usadas: {', '.join(tables)}."

    def _generate_explanation(self, question, sql, tracer) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "1-2 oraciones describiendo qué información va a traer "
                            "esta consulta. Sin mencionar SQL ni tablas."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Pregunta: '{question}'\nSQL:\n{sql}"
                    }
                ],
                max_tokens=100, temperature=0.3
            )
            explanation = response.choices[0].message.content.strip()
            tracer.step(
                archivo="nl2sql_generator",
                paso="explanation",
                entrada=f"Pregunta: '{question}'",
                accion="LLM genera respuesta amigable",
                salida=explanation[:80] + "..." if len(explanation) > 80 else explanation
            )
            return explanation
        except Exception:
            return "Consulta generada correctamente."

    def _generate_rescue_clarification(self, question: str, schema_info: str, tracer: QueryTracer) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un analista de datos hablando con un usuario. "
                            "Intentaste generar un reporte SQL para la pregunta provista, "
                            "pero te faltó información o tuviste una duda clave sobre cómo mapear "
                            "sus términos con el schema exacto de la base de datos.\n"
                            "Observa el schema y la pregunta. Formula UNA ÚNICA y BREVE pregunta "
                            "directa al usuario para aclarar exactamente qué campo o dato intentar cruzar. "
                            "Por ejemplo: '¿Con ventas te refieres a la Cantidad (Quantity) o al Importe (Net Price)?' "
                            "No des explicaciones técnicas, solo haz la pregunta amigable."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Schema:\n{schema_info}\n\nPregunta del usuario: '{question}'"
                    }
                ],
                max_tokens=150, temperature=0.2
            )
            clarification = response.choices[0].message.content.strip()
            tracer.step(
                archivo="nl2sql_generator",
                paso="rescue_clarification",
                entrada=f"Pregunta: '{question}'",
                accion="LLM genera pregunta de rescate",
                salida=clarification[:80] + "..." if len(clarification) > 80 else clarification
            )
            return clarification
        except Exception as e:
            return "Parece que me falta contexto para responder. ¿Podrías darme más detalles sobre qué datos exactos buscas?"
