"""
Database Management API Router
Endpoints for managing database connections and configurations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from database.multi_db_connector import MultiDatabaseConnector

# Initialize connector
db_connector = MultiDatabaseConnector()

router = APIRouter(prefix="/api/databases", tags=["databases"])


# Request/Response Models
class DatabaseTestRequest(BaseModel):
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    filepath: Optional[str] = None


class DatabaseTestResponse(BaseModel):
    success: bool
    message: str


class DatabaseSaveRequest(BaseModel):
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    filepath: Optional[str] = None


class DatabaseSaveResponse(BaseModel):
    success: bool
    message: str


class DatabaseConfig(BaseModel):
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    filepath: Optional[str] = None
    active: bool = False


class DatabaseListResponse(BaseModel):
    databases: List[str]
    active: Optional[str] = None


class DatabaseDetailsResponse(BaseModel):
    database: DatabaseConfig


class DatabaseActivateRequest(BaseModel):
    name: str


class DatabaseActivateResponse(BaseModel):
    success: bool
    message: str


# Endpoints

@router.post("/test", response_model=DatabaseTestResponse)
async def test_database_connection(request: DatabaseTestRequest):
    """Test connection to a database"""
    from connection_manager import DatabaseConfig as DBConfig

    config = DBConfig(
        name=request.name,
        db_type=request.db_type,
        host=request.host,
        port=request.port,
        database=request.database,
        username=request.username,
        password=request.password,
        filepath=request.filepath,
    )

    success, message = db_connector.test_connection(config)
    return DatabaseTestResponse(success=success, message=message)


@router.post("/save", response_model=DatabaseSaveResponse)
async def save_database_config(request: DatabaseSaveRequest):
    """Save a database configuration"""
    success, message = db_connector.save_database_config(
        name=request.name,
        db_type=request.db_type,
        database=request.database,
        host=request.host,
        port=request.port,
        username=request.username,
        password=request.password,
        filepath=request.filepath,
    )
    return DatabaseSaveResponse(success=success, message=message)


@router.get("", response_model=DatabaseListResponse)
async def list_databases():
    """List all saved database configurations"""
    databases = db_connector.list_databases()
    active = None
    if db_connector.active_database:
        active = db_connector.active_database.name
    return DatabaseListResponse(databases=databases, active=active)


@router.get("/{database_name}", response_model=DatabaseDetailsResponse)
async def get_database_info(database_name: str):
    """Get information about a specific database"""
    info = db_connector.get_database_info(database_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
    return DatabaseDetailsResponse(database=DatabaseConfig(**info))


@router.delete("/{database_name}", response_model=Dict)
async def delete_database(database_name: str):
    """Delete a database configuration"""
    success, message = db_connector.delete_database_config(database_name)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"success": success, "message": message}


@router.post("/{database_name}/activate", response_model=DatabaseActivateResponse)
async def activate_database(database_name: str):
    """Set a database as active"""
    success, message = db_connector.set_active_database(database_name)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return DatabaseActivateResponse(success=success, message=message)
