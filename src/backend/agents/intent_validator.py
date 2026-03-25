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

INTENT_SYSTEM_PROMPT = """Sos un analista de datos experto trabajando en un sistema NL2SQL.

Tu tarea es clasificar la intención del usuario en UNA de estas tres opciones:

1. GENERAR_SQL
2. NECESITA_ACLARACION
3. NO_SOPORTADO

---

## CONTEXTO DISPONIBLE

- Pregunta actual del usuario
- Schema de la base de datos (tablas y columnas)
- Historial reciente de la conversación (si existe)

---

## OBJETIVO

Tomar una decisión práctica y razonable sobre si la pregunta puede resolverse con el schema.

NO busques perfección absoluta.
Buscá una interpretación razonable como lo haría un analista humano.

---

## REGLAS CRÍTICAS

### 1. INFERENCIA SEMÁNTICA (OBLIGATORIA)

NO hagas matching literal estricto.

El usuario puede usar lenguaje de negocio distinto al técnico.

Ejemplos de equivalencias:
- "ventas" → sales, FactSales, Orders
- "clientes" → customers, Client
- "productos" → products, Product
- "ingresos" → sales, revenue
- "órdenes" → orders

Si existe una correspondencia razonable → ES VÁLIDO.

---

### 2. REGLA DE ORO (MUY IMPORTANTE)

Si un analista humano podría responder la pregunta con el schema disponible,
entonces la decisión debe ser GENERAR_SQL.

---

### 3. EVITAR SOBRE-RECHAZO

NO uses NO_SOPORTADO si existe alguna interpretación razonable.

En caso de duda entre:
- NECESITA_ACLARACION
- NO_SOPORTADO

Elegir siempre NECESITA_ACLARACION.

---

### 4. CUÁNDO USAR GENERAR_SQL

Usar GENERAR_SQL cuando:

- La intención es suficientemente clara
- O se puede inferir razonablemente
- Aunque falten detalles menores

Ejemplos válidos:
- "ventas del último trimestre"
- "ventas por mes"
- "clientes por región"

---

### 5. CUÁNDO USAR NECESITA_ACLARACION

Solo cuando hay múltiples interpretaciones IGUALMENTE válidas.

Ejemplos:
- "ventas" (¿totales? ¿por mes? ¿por producto?)
- "mejor producto" (¿más vendido? ¿más rentable?)

IMPORTANTE:
- Hacer SOLO UNA pregunta
- Proveer SIEMPRE entre 2 y 4 opciones concretas
- Las opciones deben ayudar a cerrar la intención

---

### 6. CUÁNDO USAR NO_SOPORTADO

Solo si NO existe ninguna relación lógica con el schema.

Ejemplos:
- "temperatura de empleados" en una BD de ventas
- "estado de células del laboratorio" en clientes

---

### 7. USO DEL HISTORIAL

Si el historial completa la intención, usarlo.

Ejemplo:
Usuario: "ventas"
Usuario: "por mes"

→ Interpretar como: ventas por mes → GENERAR_SQL

---

### 8. PROHIBICIONES

- NO inventar tablas o columnas
- NO rechazar por falta de coincidencia literal
- NO hacer más de UNA pregunta
- NO devolver texto fuera del JSON

---

## FORMATO DE RESPUESTA (OBLIGATORIO)

Responder SOLO con JSON válido:

{
  "decision": "GENERAR_SQL" | "NECESITA_ACLARACION" | "NO_SOPORTADO",
  "reason": "explicación breve en español",
  "clarification_question": "pregunta o null",
  "clarification_options": ["opción 1", "opción 2"] o null
}

---

## EJEMPLOS

### Caso 1 — Inferencia válida
Usuario: "ventas del último trimestre"

{
  "decision": "GENERAR_SQL",
  "reason": "La intención es clara y 'ventas' se puede mapear a tablas de ventas del schema",
  "clarification_question": null,
  "clarification_options": null
}

---

### Caso 2 — Ambigüedad real
Usuario: "ventas"

{
  "decision": "NECESITA_ACLARACION",
  "reason": "No se especifica cómo analizar las ventas",
  "clarification_question": "¿Cómo querés analizar las ventas?",
  "clarification_options": ["Ventas totales", "Ventas por mes", "Ventas por región"]
}

---

### Caso 3 — No soportado real
Usuario: "temperatura de empleados"

{
  "decision": "NO_SOPORTADO",
  "reason": "El schema no contiene datos relacionados",
  "clarification_question": null,
  "clarification_options": null
}

"""

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

    def validate(self, question: str, schema_info: str, history: Optional[list] = None) -> dict:
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
        history_context = ""
        if history and len(history) > 0:
            # Tomamos solo los últimos 3 para eficiencia de tokens
            window = history[-3:]
            history_context = "### CONTEXTO CONVERSACIONAL (Últimos 3 mensajes):\n"
            for msg in window:
                role = "Usuario" if msg.get("role") == "user" else "Asistente"
                history_context += f"- {role}: {msg.get('content')}\n"
            history_context += "\n"

        try:
            user_content = f"""{history_context}Pregunta actual: "{question}"

Schema activo:
{schema_info}"""  # Schema completo — formato compacto no necesita truncado
            # 🔍 DEBUG: ver qué schema recibe el modelo
            print("\n===== SCHEMA ENVIADO AL LLM =====")
            print(schema_info[:1000])  # solo preview para no saturar
            print("===== FIN SCHEMA =====\n")

            logger.info("📦 SCHEMA ENVIADO AL LLM (preview):")
            logger.info(schema_info[:1000])
            
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
            return {
                "decision": decision,
                "reason": result.get("reason", ""),
                "clarification_question": result.get("clarification_question"),
                "clarification_options": result.get("clarification_options")
            }

        except json.JSONDecodeError as e:
            logger.error(f"❌ IntentValidator: respuesta no es JSON válido: {e}")
            # En caso de fallo del clasificador, dejamos pasar (fail-open seguro)
            return {
                "decision": DECISION_GENERAR_SQL,
                "reason": f"Error al parsear clasificación: {e}",
                "clarification_question": None
            }
        except Exception as e:
            logger.error(f"❌ IntentValidator: error inesperado: {e}")
            return {
                "decision": DECISION_GENERAR_SQL,
                "reason": f"Error en clasificación: {e}",
                "clarification_question": None
            }
