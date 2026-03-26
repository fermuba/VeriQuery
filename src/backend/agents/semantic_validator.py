"""
VeriQuery — Semantic Validator
==============================
Paso posterior a la generación SQL. Verifica que el SQL generado responde
realmente la pregunta del usuario, evitando ejecutar consultas desalineadas.

Si el QueryCrafter devolvió ERROR:SCHEMA, este paso se cortocircuita
sin llamar al LLM.

Configurable con variable de entorno SEMANTIC_VALIDATION=true/false (default: true).
"""

import os
import json
import logging
from typing import Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

SEMANTIC_SYSTEM_PROMPT = """Eres un validador semántico para un sistema NL2SQL.

Recibirás una pregunta de usuario y el SQL generado para responderla.
Tu tarea es verificar si el SQL efectivamente responde la pregunta.

Responde SOLO con un objeto JSON válido (sin markdown, sin texto adicional):

{
  "valid": true | false,
  "reason": "explicación breve en español"
}

### Cuándo marcar como válido (true):
- El SQL selecciona los datos que la pregunta pide
- Los filtros y agrupaciones tienen sentido para la pregunta
- Las métricas calculadas (SUM, COUNT, AVG) corresponden a lo pedido

### Cuándo marcar como inválido (false):
- El SQL consulta tablas/columnas irrelevantes para la pregunta
- Faltan filtros esenciales (ej: la pregunta dice "este mes" y el SQL no filtra por fecha)
- La pregunta pide un agregado pero el SQL devuelve filas individuales (o viceversa)
- El SQL es trivialmente incorrecto para la intención expresada

### Ejemplos:

Pregunta: "¿cuántos clientes registrados hay?"
SQL: SELECT COUNT(*) AS total FROM Customers
Respuesta: {"valid": true, "reason": "COUNT(*) sobre la tabla Customers responde directamente la pregunta."}

Pregunta: "ventas del mes pasado por región"
SQL: SELECT TOP 100 ProductName FROM Products
Respuesta: {"valid": false, "reason": "El SQL consulta productos, no ventas. No hay filtro de fecha ni agrupación por región."}
"""


class SemanticValidator:
    """
    Verifica que el SQL generado responde la pregunta del usuario.
    Se instancia en NL2SQLGenerator y se llama después del QueryCrafter.
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
        # Configurable: si SEMANTIC_VALIDATION=false, deja pasar todo
        self.enabled = os.getenv("SEMANTIC_VALIDATION", "true").lower() in ("true", "1", "yes")

        if not self.enabled:
            logger.info("⚠️ SemanticValidator desactivado (SEMANTIC_VALIDATION=false)")
        else:
            logger.info("✅ SemanticValidator activo")

    def validate(self, question: str, sql: str) -> dict:
        """
        Verifica que el SQL responde la pregunta del usuario.

        Args:
            question: Pregunta original del usuario
            sql:      SQL generado por el QueryCrafter

        Returns:
            {
              "valid": bool,
              "reason": str
            }
        """
        # Cortocircuito: si el modelo devolvió ERROR:SCHEMA, no hay SQL que validar
        if "ERROR:SCHEMA" in sql:
            return {
                "valid": False,
                "reason": "El modelo no pudo generar SQL porque el schema no soporta la pregunta."
            }

        # Si el validador está desactivado, aprobar siempre
        if not self.enabled:
            return {"valid": True, "reason": "Validación semántica desactivada"}

        # SQL muy corto probablemente sea un error
        if len(sql.strip()) < 20:
            return {
                "valid": False,
                "reason": f"SQL generado demasiado corto para ser válido: '{sql.strip()}'"
            }

        try:
            user_content = f"""Pregunta: "{question}"

SQL generado:
{sql[:2000]}"""

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": SEMANTIC_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content.strip()
            result = json.loads(raw)

            valid = bool(result.get("valid", True))
            reason = result.get("reason", "")

            if valid:
                logger.info(f"✅ SemanticValidator: SQL válido — {reason[:80]}")
            else:
                logger.warning(f"⚠️ SemanticValidator: SQL inválido — {reason[:80]}")

            return {"valid": valid, "reason": reason}

        except json.JSONDecodeError as e:
            logger.error(f"❌ SemanticValidator: respuesta no es JSON válido: {e}")
            # Fail-open: si el validador falla, dejar pasar
            return {"valid": True, "reason": f"Error al parsear validación semántica: {e}"}
        except Exception as e:
            logger.error(f"❌ SemanticValidator: error inesperado: {e}")
            return {"valid": True, "reason": f"Error en validación semántica: {e}"}
