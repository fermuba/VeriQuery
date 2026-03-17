"""
SQL Fix Agent - Agente que usa Azure OpenAI para corregir errores SQL
"""
import os
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import AzureOpenAI
from tools.sql_connector_local import SQLConnectorLocal
import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class SQLFixAgent:
    """Agente que corrige errores SQL usando Azure OpenAI"""
    
    def __init__(self):
        """Inicializar el agente"""
        # Cliente Azure OpenAI
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")
        
        # Conector SQL (usando SQLite local por ahora)
        try:
            self.sql_connector = SQLConnectorLocal()
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar a SQL: {e}")
            self.sql_connector = None
        
        self.conversation_history = []
    
    def analyze_sql_error(self, error_message: str, sql_query: str = None) -> str:
        """
        Analizar un error SQL y proporcionar una solución
        
        Args:
            error_message: Mensaje de error SQL
            sql_query: Consulta SQL que causó el error (opcional)
            
        Returns:
            Análisis y solución propuesta
        """
        logger.info(f"🔍 Analizando error SQL...")
        
        # Construir el prompt
        prompt = f"""Eres un experto en SQL y estás ayudando a un usuario a corregir un error SQL.

Error recibido:
{error_message}

{f'Consulta SQL que causa el error:{sql_query}' if sql_query else ''}

Por favor:
1. Identifica la causa del error
2. Explica qué salió mal en lenguaje claro
3. Proporciona la consulta SQL corregida
4. Da consejos para evitar este error en el futuro

Formatea tu respuesta de forma clara y estructurada."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Eres un experto en SQL y asistente de debugging."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content
            logger.info("✅ Análisis completado")
            return analysis
        
        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}")
            return f"Error al analizar: {e}"
    
    def optimize_query(self, sql_query: str, table_schema: dict = None) -> str:
        """
        Optimizar una consulta SQL
        
        Args:
            sql_query: Consulta SQL a optimizar
            table_schema: Esquema de las tablas (opcional)
            
        Returns:
            Consulta optimizada y recomendaciones
        """
        logger.info(f"⚡ Optimizando consulta SQL...")
        
        schema_info = ""
        if table_schema:
            schema_info = f"\n\nEsquema disponible:\n{json.dumps(table_schema, indent=2)}"
        
        prompt = f"""Eres un experto en optimización SQL de Azure SQL Database.

Consulta actual:
{sql_query}
{schema_info}

Por favor:
1. Analiza la consulta para identificar cuellos de botella
2. Proporciona una versión optimizada
3. Explica las mejoras realizadas
4. Sugiere índices que podrían ayudar
5. Estima el mejora de rendimiento esperada

Sé específico y práctico en tus recomendaciones."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Eres un experto en optimización SQL y rendimiento de bases de datos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            optimization = response.choices[0].message.content
            logger.info("✅ Optimización completada")
            return optimization
        
        except Exception as e:
            logger.error(f"❌ Error en optimización: {e}")
            return f"Error al optimizar: {e}"
    
    def suggest_schema(self, data_description: str) -> str:
        """
        Sugerir un esquema de base de datos basado en una descripción
        
        Args:
            data_description: Descripción de los datos a almacenar
            
        Returns:
            Sugerencia de esquema SQL
        """
        logger.info(f"🏗️ Sugiriendo esquema...")
        
        prompt = f"""Eres un experto en diseño de bases de datos SQL.

Descripción de los datos a almacenar:
{data_description}

Por favor:
1. Sugiere un esquema de base de datos normalizado
2. Define las tablas necesarias
3. Especifica tipos de datos apropiados
4. Define relaciones entre tablas (PRIMARY KEY, FOREIGN KEY)
5. Sugiere índices útiles
6. Proporciona comandos CREATE TABLE listos para ejecutar

Optimiza para rendimiento y mantenibilidad."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Eres un experto en diseño de esquemas de bases de datos SQL."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            schema_suggestion = response.choices[0].message.content
            logger.info("✅ Esquema sugerido")
            return schema_suggestion
        
        except Exception as e:
            logger.error(f"❌ Error en sugerencia: {e}")
            return f"Error al sugerir: {e}"
    
    def explain_query(self, sql_query: str) -> str:
        """
        Explicar qué hace una consulta SQL
        
        Args:
            sql_query: Consulta SQL a explicar
            
        Returns:
            Explicación en lenguaje natural
        """
        logger.info(f"📖 Explicando consulta...")
        
        prompt = f"""Eres un instructor de SQL.

Consulta SQL:
{sql_query}

Por favor:
1. Explica en lenguaje simple qué hace esta consulta
2. Describe cada cláusula (SELECT, FROM, WHERE, etc.)
3. Identifica qué datos retorna
4. Menciona cualquier problema potencial
5. Sugiere mejoras si las hay

Usa un lenguaje claro y educativo."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Eres un instructor de SQL experto en explicar consultas de forma clara."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            explanation = response.choices[0].message.content
            logger.info("✅ Explicación completada")
            return explanation
        
        except Exception as e:
            logger.error(f"❌ Error en explicación: {e}")
            return f"Error al explicar: {e}"
    
    def chat(self, user_message: str) -> str:
        """
        Conversación interactiva con el agente SQL
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Respuesta del agente
        """
        # Agregar mensaje del usuario al historial
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Sistema prompt
        system_prompt = """Eres ForensicGuardian SQL Agent, un asistente experto en SQL y debugging de consultas.
Ayudas a los usuarios a:
- Corregir errores SQL
- Optimizar consultas
- Diseñar esquemas de bases de datos
- Explicar cómo funcionan las consultas

Sé amable, preciso y práctico. Siempre proporciona código SQL cuando sea relevante."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt}
                ] + self.conversation_history,
                max_tokens=1500,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message.content
            
            # Agregar respuesta al historial
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        
        except Exception as e:
            logger.error(f"❌ Error en chat: {e}")
            return f"Error: {e}"
    
    def close(self):
        """Cerrar conexiones"""
        if self.sql_connector:
            self.sql_connector.close()
        logger.info("✅ Agente cerrado")


if __name__ == "__main__":
    print("=" * 60)
    print("SQL FIX AGENT - TEST INTERACTIVO")
    print("=" * 60)
    
    try:
        agent = SQLFixAgent()
        print("\n✅ Agente inicializado correctamente")
        
        # Ejemplo 1: Analizar un error
        print("\n1️⃣ Analizando un error SQL...")
        error = agent.analyze_sql_error(
            "Incorrect syntax near 'WHERE'",
            "SELECT * FROM usuarios WHERE edad > 30"
        )
        print(f"\n{error}\n")
        
        # Ejemplo 2: Optimizar una consulta
        print("\n2️⃣ Optimizando una consulta...")
        optimization = agent.optimize_query(
            "SELECT * FROM usuarios WHERE nombre LIKE '%juan%'"
        )
        print(f"\n{optimization}\n")
        
        # Ejemplo 3: Chat interactivo
        print("\n3️⃣ Chat interactivo...")
        response = agent.chat("¿Cómo creo un índice en SQL?")
        print(f"\n{response}\n")
        
        agent.close()
        print("\n✅ Test completado")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
