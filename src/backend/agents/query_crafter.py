"""
Query Crafter - Generador de SQL con Mapeo Semántico
====================================================

Convierte preguntas en lenguaje natural a SQL usando:
1. Mapeo semántico (beneficiarios → Dim_Beneficiario)
2. Schema dinámico de la BD
3. Azure OpenAI con temperatura baja (precisión)
"""

import os
import logging
from typing import Optional
from openai import AzureOpenAI
import pyodbc

from table_mapping import enrich_system_prompt, get_semantic_context

logger = logging.getLogger(__name__)


class QueryCrafter:
    """
    Generador de consultas SQL a partir de lenguaje natural.
    Especializado en base de datos Contoso Social.
    """
    
    def __init__(self, connection_string: str, azure_client: Optional[AzureOpenAI] = None):
        """
        Inicializar Query Crafter
        
        Args:
            connection_string: Cadena de conexión a SQL Server
            azure_client: Cliente de Azure OpenAI (si None, crea uno nuevo)
        """
        self.connection_string = connection_string
        
        # Inicializar cliente Azure OpenAI
        if azure_client is None:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            self.client = azure_client
        
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI")
        
        # Cargar schema REAL de la base de datos
        logger.info("🔄 Cargando schema de SQL Server...")
        self.schema_info = self._load_schema()
        logger.info(f"✅ Schema cargado: {len(self.schema_info)} caracteres")
    
    def _load_schema(self) -> str:
        """
        Cargar schema real de SQL Server de Contoso Social
        Incluye: tablas, columnas, tipos de datos y ejemplos
        """
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            schema_text = "=== SCHEMA DE BASE DE DATOS CONTOSO SOCIAL ===\n\n"
            
            # Obtener todas las tablas (tablas reales, no vistas)
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                  AND TABLE_SCHEMA = 'dbo'
                ORDER BY TABLE_NAME
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"📊 Encontradas {len(tables)} tablas")
            
            for table_name in tables:
                schema_text += f"\n📊 TABLA: {table_name}\n"
                schema_text += "=" * 60 + "\n"
                schema_text += "Columnas:\n"
                
                # Obtener columnas
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME, 
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        IS_NULLABLE,
                        COLUMNPROPERTY(OBJECT_ID('{table_name}'), COLUMN_NAME, 'IsIdentity') AS IsIdentity
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ?
                      AND TABLE_SCHEMA = 'dbo'
                    ORDER BY ORDINAL_POSITION
                """, table_name)
                
                columns = cursor.fetchall()
                
                for col_row in columns:
                    col_name = col_row[0]
                    col_type = col_row[1]
                    col_len = col_row[2]
                    col_null = col_row[3]
                    is_identity = col_row[4]
                    
                    # Construir tipo de datos
                    if col_len and col_len > 0:
                        type_str = f"{col_type}({col_len})"
                    else:
                        type_str = col_type
                    
                    # Flags
                    flags = []
                    if is_identity == 1:
                        flags.append("PK")
                    if col_null == "NO":
                        flags.append("NOT NULL")
                    
                    flags_str = " [" + ", ".join(flags) + "]" if flags else ""
                    
                    schema_text += f"  • {col_name:30} {type_str:20}{flags_str}\n"
                
                # Obtener datos de ejemplo (2 filas para ver estructura)
                try:
                    cursor.execute(f"SELECT TOP 2 * FROM {table_name}")
                    sample_rows = cursor.fetchall()
                    
                    if sample_rows:
                        schema_text += "\nEjemplos de datos:\n"
                        col_names = [desc[0] for desc in cursor.description]
                        
                        for idx, row in enumerate(sample_rows, 1):
                            schema_text += f"  Fila {idx}:\n"
                            # Mostrar todas las columnas
                            for i, col_name in enumerate(col_names):
                                val = row[i]
                                if val is None:
                                    val_str = "NULL"
                                elif isinstance(val, str):
                                    val_str = val[:40]  # Truncar strings largos
                                elif isinstance(val, (int, float)):
                                    val_str = str(val)
                                else:
                                    val_str = str(val)[:40]
                                
                                schema_text += f"    {col_name}: {val_str}\n"
                except Exception as e:
                    logger.debug(f"⚠️ Error cargando ejemplos de {table_name}: {e}")
                
                schema_text += "\n"
            
            conn.close()
            return schema_text
        
        except Exception as e:
            logger.error(f"❌ Error cargando schema: {e}")
            return "⚠️ Schema no disponible - verifica conexión a SQL Server"
    
    def generate_sql(self, user_question: str) -> dict:
        """
        Generar SQL a partir de pregunta en lenguaje natural.
        
        Args:
            user_question: Pregunta del usuario (ej: "¿Cuántos beneficiarios hay?")
        
        Returns:
            Dict con:
                - sql: SQL generada
                - explanation: Explicación en español
                - tables_used: Tablas detectadas
                - valid: ¿Es válida?
        """
        
        logger.info(f"🔄 Generando SQL para: {user_question}")
        
        try:
            # Obtener contexto semántico
            semantic_context = get_semantic_context(user_question)
            
            # Construir system prompt
            system_prompt = enrich_system_prompt()
            
            # User prompt
            user_prompt = f"""
{semantic_context}

Pregunta del usuario: "{user_question}"

INSTRUCCIONES:
1. Genera SOLO el SQL (sin markdown, sin ```sql```)
2. Usa SOLO las tablas listadas en el schema
3. Usa SOLO las columnas listadas para cada tabla
4. Para COUNT de beneficiarios: usa Dim_Beneficiario donde EsActual = 1
5. Para asistencias: usa Fact_Asistencia con JOINs apropiados
6. Siempre incluye TOP 100 para limitar resultados
7. Usa aliases cortos: a, b, u, t, dt, p

El SQL debe ser:
- Sintácticamente correcto para SQL Server
- Una query de LECTURA (SELECT)
- Sin comentarios largos
- Con alias descriptivos

Responde con SOLO el SQL, nada más.
"""
            
            # Llamar a Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt + "\n\n" + self.schema_info},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # MUY BAJO para máxima precisión
                max_tokens=800
            )
            
            sql = response.choices[0].message.content.strip()
            
            # Limpiar markdown si existe
            sql = sql.replace("```sql", "").replace("```", "").replace("`", "").strip()
            
            # Extraer tablas usadas
            tables = self._extract_tables(sql)
            
            logger.info(f"✅ SQL generada. Tablas: {tables}")
            
            return {
                "sql": sql,
                "tables_used": tables,
                "tokens": response.usage.total_tokens,
                "cost_usd": (
                    response.usage.prompt_tokens * 0.00000015 +
                    response.usage.completion_tokens * 0.0000006
                )
            }
        
        except Exception as e:
            logger.error(f"❌ Error generando SQL: {e}")
            return {
                "sql": "",
                "error": str(e),
                "tables_used": [],
                "tokens": 0,
                "cost_usd": 0
            }
    
    def _extract_tables(self, sql: str) -> list:
        """
        Extraer nombres de tablas del SQL generado.
        """
        import re
        
        pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        
        return list(set(matches))  # Retornar únicos
