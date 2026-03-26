"""
VeriQuery — Intent Validator
============================
Paso previo a la generación SQL. Clasifica la intención del usuario usando LLM,
evaluando si la pregunta puede responderse con el schema disponible.

Devuelve una de tres decisiones:
  GENERAR_SQL       → la pregunta es clara y el schema la soporta
  NECESITA_ACLARACION → la pregunta es ambigua o le falta información
  NO_SOPORTADO      → la pregunta no puede responderse con el schema actual

Configurable con variable de entorno INTENT_VALIDATION=true/false (default: true).
"""

import os
import json
import logging
from typing import Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# Opciones válidas de decisión
DECISION_GENERAR_SQL = "GENERAR_SQL"
DECISION_ACLARACION = "NECESITA_ACLARACION"
DECISION_NO_SOPORTADO = "NO_SOPORTADO"


INTENT_SYSTEM_PROMPT = """You are a NL2SQL intent classifier. Your only job is to decide if a natural language question can be answered using the provided database schema.
 
## ROLE
Expert data analyst. You think like a business user, not a database engineer.
 
## TASK
Classify the user question into exactly ONE of:
- GENERAR_SQL
- NECESITA_ACLARACION
- NO_SOPORTADO
 
## DECISION RULES
 
### GENERAR_SQL — use when:
- Intent is clear enough for a reasonable analyst to write SQL
- Business terms can map to schema (ventas→Sales, clientes→Customer, productos→Product)
- Minor details are missing but a default interpretation exists
 
### NECESITA_ACLARACION — use when:
- Two or more EQUALLY valid interpretations exist with no way to choose
- Always prefer this over NO_SOPORTADO when uncertain
 
### NO_SOPORTADO — use when:
- Zero logical relationship between question and schema exists
- No reasonable mapping is possible
 
## SEMANTIC MAPPING (apply always)
ventas / ingresos / facturación → Sales
clientes / compradores          → Customer
productos / artículos / items   → Product
tiendas / locales / sucursales  → Store
fechas / períodos / tiempo      → Date
 
## CONSTRAINTS
- ONE clarification question maximum
- TWO to FOUR concrete options when asking for clarification
- NEVER invent tables or columns
- NEVER reject due to literal mismatch
- NEVER output text outside the JSON
 
## RESPONSE FORMAT (strict)
{
  "decision": "GENERAR_SQL" | "NECESITA_ACLARACION" | "NO_SOPORTADO",
  "reason": "<brief explanation in Spanish, max 20 words>",
  "clarification_question": "<single question in Spanish>" | null,
  "clarification_options": ["<option1>", "<option2>"] | null
}
 
## EXAMPLES
 
Input: "ventas del último trimestre"
Output: {"decision": "GENERAR_SQL", "reason": "Intención clara, ventas mapea a Sales, período inferible", "clarification_question": null, "clarification_options": null}
 
Input: "ventas"
Output: {"decision": "NECESITA_ACLARACION", "reason": "Ambigüedad real: múltiples agrupaciones igualmente válidas", "clarification_question": "¿Cómo querés analizar las ventas?", "clarification_options": ["Ventas totales", "Ventas por mes", "Ventas por producto", "Ventas por región"]}
 
Input: "temperatura corporal de empleados"
Output: {"decision": "NO_SOPORTADO", "reason": "Sin relación con el schema disponible", "clarification_question": null, "clarification_options": null}"""
 

class IntentValidator:
    """
    Clasifica la intención del usuario antes de generar SQL.
    Se instancia en NL2SQLGenerator y se llama en generate_sql() como primer paso.
    """

    def __init__(self, azure_client: Optional[AzureOpenAI] = None):
        """
        Args:
            azure_client: Cliente Azure OpenAI reutilizable del orquestador.
        """
        if azure_client is None:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            self.client = azure_client

        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")
        # Configurable: si INTENT_VALIDATION=false, el validador deja pasar todo
        self.enabled = os.getenv("INTENT_VALIDATION", "true").lower() in ("true", "1", "yes")

        if not self.enabled:
            logger.info("⚠️ IntentValidator desactivado (INTENT_VALIDATION=false)")
        else:
            logger.info("✅ IntentValidator activo")

    # Sin tracer
    # def validate(self, question: str, schema_info: str, history: Optional[list] = None) -> dict:

    # Con tracer
    def validate(self, question: str, schema_info: str, history: Optional[list] = None, tracer=None) -> dict:
        """
        Clasifica la intención de la pregunta en relación al schema.

        Args:
            question:    Pregunta original del usuario
            schema_info: Schema activo de la base de datos
            history:     Historial de mensajes previos (opcional)

        Returns:
            {
              "decision": "GENERAR_SQL" | "NECESITA_ACLARACION" | "NO_SOPORTADO",
              "reason": str,
              "clarification_question": str | None,
              "clarification_options": list | None
            }
        """
        # Si el validador está desactivado, pasar siempre
        if not self.enabled:
            return {
                "decision": DECISION_GENERAR_SQL,
                "reason": "Validación de intención desactivada",
                "clarification_question": None,
                "clarification_options": None
            }

        # Contexto del historial (últimos 3 mensajes) para no perder el hilo
        def _build_user_content(question: str, schema_info: str, history: list = None) -> str:
            """
            Construye el mensaje de usuario para el clasificador de intención.
            Separado en secciones claras para mejor parsing del LLM.
            """
        
            # Historial: últimos 3 mensajes, solo si existe
            history_section = ""
            if history and len(history) > 0:
                window = history[-3:]
                lines = []
                for msg in window:
                    role = "user" if msg.get("role") == "user" else "assistant"
                    lines.append(f'  {{"role": "{role}", "content": "{msg.get("content", "")}"}}')
                history_section = f"""
        "conversation_history": [
        {chr(10).join(lines)}
        ],"""
        
            user_content = f"""{{
        "task": "classify_intent",{history_section}
        "current_question": "{question}",
        "database_schema": "{schema_info}"
        }}"""
        
            return user_content

        try:
            user_content = _build_user_content(question, schema_info, history)

            # Tracer:
            if tracer:
                tracer.step(
                    archivo="intent_validator",
                    paso="schema_al_llm",
                    entrada=question,
                    accion="Schema enviado al LLM para clasificación de intención",
                    salida=schema_info[:500]
                )

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content.strip()
            result = json.loads(raw)

            # Validar que la decisión sea una de las esperadas
            decision = result.get("decision", "")
            if decision not in (DECISION_GENERAR_SQL, DECISION_ACLARACION, DECISION_NO_SOPORTADO):
                logger.warning(f"⚠️ IntentValidator devolvió decisión inesperada: '{decision}'. Asumiendo GENERAR_SQL.")
                return {
                    "decision": DECISION_GENERAR_SQL,
                    "reason": f"Decisión inesperada del clasificador: {decision}",
                    "clarification_question": None
                }

            logger.info(f"🧭 IntentValidator: {decision} — {result.get('reason', '')[:80]}")
            # con tracer
            if tracer:
                tracer.step(
                    archivo="intent_validator",
                    paso="decision_final",
                    entrada=question,
                    accion=f"Decisión LLM: {decision}",
                    salida=result.get("reason", "")
                )
            return {
                "decision": decision,
                "reason": result.get("reason", ""),
                "clarification_question": result.get("clarification_question"),
                "clarification_options": result.get("clarification_options")
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ IntentValidator: respuesta no es JSON válido: {e}")
            # En caso de fallo del clasificador, dejamos pasar (fail-open seguro)
            if tracer:
                tracer.error("intent_validator", "parsear_respuesta", str(e), entrada=question)
            return {
                "decision": DECISION_GENERAR_SQL,
                "reason": f"Error al parsear clasificación: {e}",
                "clarification_question": None
            }
        except Exception as e:
            logger.error(f"❌ IntentValidator: error inesperado: {e}")
            if tracer:
                tracer.error("intent_validator", "llamada_llm", str(e), entrada=question)
            return {
                "decision": DECISION_GENERAR_SQL,
                "reason": f"Error en clasificación: {e}",
                "clarification_question": None
            }
