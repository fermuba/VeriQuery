"""
Schema Scanner API Router
Endpoints for scanning and retrieving database schemas
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import sys
from pathlib import Path
import json
import logging

# Add src to path for imports
src_path = str(Path(__file__).parent.parent)
tools_path = str(Path(__file__).parent.parent.parent.parent / "tools")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

from database.multi_db_connector import MultiDatabaseConnector

logger = logging.getLogger(__name__)

# Initialize connector
db_connector = MultiDatabaseConnector()

# Global reference to nl2sql_generator (será establecida desde main.py)
nl2sql_generator = None

def set_nl2sql_generator(generator):
    """Called from main.py to set the nl2sql_generator instance"""
    global nl2sql_generator
    nl2sql_generator = generator

router = APIRouter(prefix="/api/schema", tags=["schema"])


# Request/Response Models
class SchemaScanRequest(BaseModel):
    database_name: Optional[str] = None


class SchemaResponse(BaseModel):
    tables: list
    database_name: Optional[str] = None
    error: Optional[str] = None


class SchemaExportRequest(BaseModel):
    database_name: Optional[str] = None
    format: str = "json"  # "json" or "sql"


class SchemaExportResponse(BaseModel):
    content: str
    format: str
    database_name: Optional[str] = None
    error: Optional[str] = None


# Endpoints

@router.post("/scan", response_model=SchemaResponse)
async def scan_schema(request: SchemaScanRequest, db_name: Optional[str] = None):
    """Scan database schema
    
    Acepta database_name del body o db_name del query param
    """
    try:
        # Usar db_name del query param si no viene en el body
        database_name = request.database_name or db_name
        logger.info(f"🔍 SCHEMA SCAN START: database_name={database_name}, db_name_param={db_name}")
        schema, error = db_connector.scan_schema(database_name)
        
        if error:
            logger.error(f"Schema scan error: {error}")
            raise HTTPException(status_code=400, detail=error)
            
        tables_list = []
        for table_name, data in schema.items():
            tables_list.append({
                "name": table_name,
                "columns": data["columns"],
                "record_count": data["row_count"],
                "sample_data": data["sample_data"]
            })
        
        # IMPORTANTE: Sincronizar con nl2sql_generator para que tenga el schema actualizado
        if nl2sql_generator:
            try:
                config = db_connector.active_database
                if config:
                    # Convertir schema a formato texto (similar a _load_schema_from_connector)
                    schema_text = f"=== SCHEMA: {database_name} ({config.db_type}) ===\n\n"
                    for table_name, data in schema.items():
                        cols = ", ".join(data["columns"])
                        schema_text += f"{table_name}({cols})\n"
                    
                    nl2sql_generator.set_active_schema_direct(
                        db_name=database_name,
                        db_type=config.db_type,
                        schema_text=schema_text
                    )
                    logger.info(f"✅ nl2sql_generator schema sincronizado para: {database_name}")
            except Exception as e:
                logger.warning(f"⚠ Error sincronizando nl2sql_generator: {e}")
        
        logger.info(f"✓ Schema scan successful for database: {database_name}")
        return SchemaResponse(
            tables=tables_list,
            database_name=database_name,
            error=None,
        )
    except Exception as e:
        logger.error(f"Unexpected error during schema scan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("", response_model=SchemaResponse)
async def get_cached_schema():
    """Get currently cached schema (from active database)"""
    if not db_connector.active_database:
        raise HTTPException(status_code=400, detail="No active database set")
    
    schema, error = db_connector.scan_schema()
    
    if error:
        raise HTTPException(status_code=400, detail=error)
        
    tables_list = []
    for table_name, data in schema.items():
        tables_list.append({
            "name": table_name,
            "columns": data["columns"],
            "record_count": data["row_count"],
            "sample_data": data["sample_data"]
        })
    
    return SchemaResponse(
        tables=tables_list,
        database_name=db_connector.active_database.name,
        error=None,
    )


@router.post("/export", response_model=SchemaExportResponse)
async def export_schema(request: SchemaExportRequest):
    """Export database schema in specified format"""
    from schema_scanner import SchemaScanner
    
    # Get database config
    if request.database_name:
        config = db_connector.config_manager.get_database(request.database_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Database '{request.database_name}' not found")
    else:
        if not db_connector.active_database:
            raise HTTPException(status_code=400, detail="No active database set")
        config = db_connector.active_database
    
    # Create scanner
    scanner = SchemaScanner(config)
    
    try:
        if request.format.lower() == "json":
            content = scanner.export_json()
            format_type = "json"
        elif request.format.lower() == "sql":
            content = scanner.export_sql_schema()
            format_type = "sql"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        return SchemaExportResponse(
            content=content,
            format=format_type,
            database_name=config.name,
            error=None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")
