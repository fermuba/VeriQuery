"""
NL2SQL Generator - Demo
=======================

Demuestra cómo usar el Semantic Metadata Mapping para generar SQL a partir de 
lenguaje natural usando Azure OpenAI.

Este archivo es un prototipo que:
1. Carga el esquema de metadatos
2. Inyecta el esquema en el System Prompt de ChatGPT
3. Envía preguntas en lenguaje natural
4. Recibe SQL generado
5. Valida que la SQL solo use tablas/columnas definidas
"""

import os
import sys
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from openai import AzureOpenAI
from src.backend.core.schema import (
    get_schema_prompt,
    get_table_by_name,
    validate_column_exists,
)
import logging
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class NL2SQLGenerator:
    """
    Generador de SQL a partir de Lenguaje Natural.
    
    Arquitectura:
    1. System Prompt: Incluye el esquema completo (prevención de alucinaciones)
    2. User Message: Pregunta en lenguaje natural
    3. Respuesta: SQL generada
    4. Validación: Verificar que solo use tablas/columnas válidas
    """
    
    def __init__(self):
        """Inicializar el generador NL2SQL"""
        
        # Inicializar cliente Azure OpenAI
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")
        
        # Obtener el prompt del esquema
        self.schema_prompt = get_schema_prompt()
        
        logger.info("✅ NL2SQLGenerator inicializado")
    
    def generate_sql(self, natural_language_query: str) -> dict:
        """
        Genera SQL a partir de una pregunta en lenguaje natural.
        
        Args:
            natural_language_query: Pregunta en lenguaje natural
            
        Returns:
            Diccionario con:
            - sql: Consulta SQL generada
            - explanation: Explicación de la SQL
            - valid: ¿La SQL es válida?
            - tables_used: Tablas identificadas
        """
        
        logger.info(f"🔄 Generando SQL para: {natural_language_query}")
        
        # Construir el mensaje del usuario
        user_message = f"""
Pregunta del usuario (en lenguaje natural):
"{natural_language_query}"

Por favor:
1. Convierte esta pregunta a una consulta SQL válida
2. Usa SOLO las tablas y columnas definidas en el esquema anterior
3. Genera SQL limpia y bien formateada
4. Incluye comentarios explicativos en la SQL
5. Proporciona una breve explicación de la lógica

FORMATO DE RESPUESTA (CRÍTICO):
```sql
-- [Tu SQL aquí]
```

EXPLICACIÓN:
[Tu explicación aquí]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un experto en SQL y eres responsable de convertir preguntas "
                            "en lenguaje natural a consultas SQL precisas. "
                            "NUNCA uses tablas o columnas que no estén en el esquema proporcionado. "
                            "Siempre verifica que existan antes de usarlas. "
                            "Usa el Star Schema correctamente (FACT en el centro, DIM como satélites).\n\n"
                            + self.schema_prompt
                        )
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                max_tokens=1500,
                temperature=0.3  # Baja temperatura para ser más determinista
            )
            
            full_response = response.choices[0].message.content
            
            # Extraer SQL del response
            sql_match = re.search(r'```sql\n(.*?)\n```', full_response, re.DOTALL)
            if sql_match:
                sql = sql_match.group(1).strip()
            else:
                # Si no encuentra el patrón sql, intenta extraer cualquier código
                sql_match = re.search(r'```\n(.*?)\n```', full_response, re.DOTALL)
                if sql_match:
                    sql = sql_match.group(1).strip()
                else:
                    sql = "NO SE PUDO EXTRAER SQL"
            
            # Extraer explicación
            parts = full_response.split("EXPLICACIÓN:")
            explanation = parts[1].strip() if len(parts) > 1 else ""
            
            # Validar la SQL
            validation_result = self._validate_sql(sql)
            
            result = {
                "natural_query": natural_language_query,
                "sql": sql,
                "explanation": explanation,
                "valid": validation_result["valid"],
                "validation_notes": validation_result["notes"],
                "tables_used": validation_result["tables"],
                "tokens_used": response.usage.total_tokens,
                "cost_usd": (
                    response.usage.prompt_tokens * 0.00000015 +
                    response.usage.completion_tokens * 0.0000006
                )
            }
            
            logger.info(f"✅ SQL generada. Válida: {validation_result['valid']}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Error generando SQL: {e}")
            return {
                "error": str(e),
                "natural_query": natural_language_query
            }
    
    def _validate_sql(self, sql: str) -> dict:
        """
        Valida que la SQL solo use tablas/columnas del esquema.
        
        Args:
            sql: Consulta SQL a validar
            
        Returns:
            Diccionario con resultados de validación
        """
        
        tables = set()
        valid = True
        notes = []
        
        # Regex simple para extraer FROM y JOIN
        from_pattern = r'FROM\s+(\w+)'
        join_pattern = r'JOIN\s+(\w+)'
        
        from_matches = re.findall(from_pattern, sql, re.IGNORECASE)
        join_matches = re.findall(join_pattern, sql, re.IGNORECASE)
        
        all_tables = set(from_matches + join_matches)
        
        for table in all_tables:
            tables.add(table)
            if not get_table_by_name(table):
                valid = False
                notes.append(f"⚠️  Tabla '{table}' no existe en el esquema")
        
        # TODO: Validar columnas (más complejo con regex)
        
        return {
            "valid": valid,
            "tables": list(tables),
            "notes": notes if notes else ["✅ Todas las tablas son válidas"]
        }


# ============================================================================
# PRUEBAS
# ============================================================================

def test_nl2sql():
    """Pruebas del generador NL2SQL"""
    
    print("=" * 80)
    print("NL2SQL GENERATOR - PRUEBAS")
    print("=" * 80)
    
    generator = NL2SQLGenerator()
    
    # Casos de prueba
    test_cases = [
        "¿Cuántos beneficiarios recibieron arroz en marzo de 2024?",
        "¿Cuál es el gasto total por beneficiario en medicamentos?",
        "¿Qué transacciones fueron registradas después de las 22:00?",
        "¿Cuáles son los beneficiarios de barrio Centro que recibieron más de 3 asistencias?",
        "¿Hay inconsistencias en las transacciones registradas por usuario 'admin'?",
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"PRUEBA {i}")
        print(f"{'=' * 80}")
        print(f"🗣️  Pregunta natural: {query}\n")
        
        result = generator.generate_sql(query)
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            print(f"📊 SQL Generada:")
            print(f"{result['sql']}\n")
            
            print(f"📝 Explicación:")
            print(f"{result['explanation']}\n")
            
            print(f"✅ Válida: {result['valid']}")
            print(f"📋 Tablas usadas: {', '.join(result['tables_used'])}")
            print(f"💡 Notas de validación: {', '.join(result['validation_notes'])}")
            print(f"📈 Tokens: {result['tokens_used']} | Costo: ${result['cost_usd']:.8f}")


if __name__ == "__main__":
    test_nl2sql()
