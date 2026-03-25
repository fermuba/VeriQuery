"""
Normaliza sentencias SQL usando parsing AST con sqlglot.
Asegura consistencia de dialecto independientemente de qué motor de BD
haya "alucinado" el LLM durante la generación.
"""

import logging
from typing import Optional, Dict, Any
import sqlglot
from sqlglot.errors import ParseError, TokenError

from src.backend.core.tracer import QueryTracer

logger = logging.getLogger(__name__)

# Mapeo de engine de VeriQuery a dialecto de sqlglot
DIALECT_MAPPING = {
    "sqlserver": "tsql",
    "postgresql": "postgres",
    "sqlite": "sqlite",
    "mysql": "mysql"
}

class SQLNormalizer:
    def normalize(
        self,
        sql: str,
        dialect_db_type: Optional[str] = "sqlserver",
        tracer: Optional[QueryTracer] = None
    ) -> Dict[str, Any]:
        """
        Transpila y formatea una query SQL al dialecto objetivo activo.
        """
        # Obtenemos el dialecto de salida, default tsql
        target_dialect = DIALECT_MAPPING.get((dialect_db_type or "").lower(), "tsql")

        if tracer:
            tracer.step(
                archivo="sql_normalizer",
                paso="iniciar_normalizacion",
                entrada=sql[:80].replace('\n', ' '),
                accion=f"Parseando AST y transpilando a dialecto: {target_dialect}",
                salida="pendiente..."
            )

        try:
            # Asumimos entrada T-SQL (ya que el prompt base le exige T-SQL al LLM)
            # Si el LLM alucina LIMIT (Postgres), sqlglot en modo tsql igual lo entiende.
            # Lo transpilamos al dialecto objetivo (write=target_dialect)
            normalized_sql = sqlglot.transpile(
                sql,
                read="tsql",
                write=target_dialect,
                pretty=True
            )[0]
            
            # Limpiamos delimitadores si el LLM pone punto y coma final
            normalized_sql = normalized_sql.rstrip(";")

            if tracer:
                tracer.step(
                    archivo="sql_normalizer",
                    paso="fin_normalizacion",
                    entrada=f"Dialecto objetivo: {target_dialect}",
                    accion="Transpilación AST exitosa",
                    salida=normalized_sql[:80].replace('\n', ' ')
                )
                
            return {
                "success": True,
                "normalized_sql": normalized_sql,
                "target_dialect": target_dialect
            }

        except (ParseError, TokenError) as e:
            logger.error(f"❌ Error parseando AST de SQL: {e}")
            if tracer:
                tracer.step(
                    archivo="sql_normalizer",
                    paso="error_parseo",
                    entrada=sql[:80].replace('\n', ' '),
                    accion="El SQL generado por el LLM tiene errores de sintaxis o de dialecto mixtos irrecuperables",
                    salida=str(e)[:150]
                )
                
            return {
                "success": False,
                "error": str(e)
            }
