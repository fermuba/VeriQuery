"""
Database Management API Router with Azure Key Vault Integration
Endpoints for managing database connections, configurations, and credentials
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add paths for imports
src_path = str(Path(__file__).parent.parent)
tools_path = str(Path(__file__).parent.parent.parent.parent / "tools")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

from database.multi_db_connector import MultiDatabaseConnector
from connection_manager import DatabaseConfig as DBConfig
from secure_credential_store import SecureCredentialStore
from permission_validator import PermissionValidator

logger = logging.getLogger(__name__)

# Initialize components
db_connector = MultiDatabaseConnector()

# Global reference to nl2sql_generator (será establecida desde main.py)
nl2sql_generator = None

def set_nl2sql_generator(generator):
    """Called from main.py to set the nl2sql_generator instance"""
    global nl2sql_generator
    nl2sql_generator = generator
try:
    cred_store = SecureCredentialStore()
    use_keyvault = True
    logger.info("✓ Azure Key Vault integration enabled")
except Exception as e:
    logger.warning(f"⚠ Key Vault not available: {str(e)}")
    cred_store = None
    use_keyvault = False

permission_validator = PermissionValidator()

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
    db_name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    filepath: Optional[str] = None
    active: bool = False


class DatabaseListResponse(BaseModel):
    databases: List[DatabaseConfig]
    active: Optional[str] = None


class DatabaseDetailsResponse(BaseModel):
    database: DatabaseConfig


class DatabaseActivateRequest(BaseModel):
    name: str


class DatabaseActivateResponse(BaseModel):
    success: bool
    message: str


class DatabaseCredentialsResponse(BaseModel):
    success: bool
    message: str
    stored_in_keyvault: bool
    is_readonly: Optional[bool] = None
    readonly_message: Optional[str] = None
    permission_details: Optional[Dict] = None
    warnings: Optional[List[str]] = None


class CredentialSecurityCheckResponse(BaseModel):
    success: bool
    message: str
    is_readonly: bool
    readonly_message: str
    permission_details: Dict
    can_save_securely: bool


class CredentialListResponse(BaseModel):
    credentials: List[str]
    stored_in_keyvault: bool


class CredentialMetadataResponse(BaseModel):
    db_name: str
    db_type: str
    host: Optional[str]
    database: str
    saved_at: Optional[str]
    product: str
    stored_in_keyvault: bool


# Endpoints

@router.post("/test", response_model=DatabaseTestResponse)
async def test_database_connection(request: DatabaseTestRequest):
    """Test connection to a database"""

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


@router.post("/save", response_model=DatabaseCredentialsResponse)
async def save_database_config(request: DatabaseSaveRequest):
    """
    Save a database configuration with security validation
    
    Process:
    1. Test database connection
    2. Validate read-only permissions
    3. Save credentials to Azure Key Vault (if enabled)
    4. Show warnings if not read-only
    """
    
    warnings = []
    
    try:
        # Step 1: Test connection
        logger.info(f"Testing connection to database: {request.name}")
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

        success, test_message = db_connector.test_connection(config)
        if not success:
            return DatabaseCredentialsResponse(
                success=False,
                message=f"Connection test failed: {test_message}",
                stored_in_keyvault=False
            )

        logger.info(f"✓ Connection test passed for {request.name}")

        # Step 2: Validate read-only permissions
        logger.info(f"Validating read-only permissions for {request.name}")
        is_readonly = False
        readonly_message = "Unknown"
        permission_details = {}

        try:
            # Get actual connection object
            conn = db_connector.get_connection(config)
            if conn:
                is_readonly, readonly_message, permission_details = permission_validator.validate_readonly_permissions(
                    request.db_type, conn
                )
                db_connector.close_connection(conn)
                
                if not is_readonly:
                    warnings.append(
                        "⚠ WARNING: This database connection has write permissions. "
                        "For VeriQuery, read-only access is recommended."
                    )
                    logger.warning(f"Non-read-only connection: {request.name}")
            else:
                readonly_message = "Could not validate permissions"
                logger.warning(f"Could not get connection for permission check: {request.name}")
                
        except Exception as e:
            logger.warning(f"Permission validation error: {str(e)}")
            warnings.append(f"Could not fully validate permissions: {str(e)}")

        # Step 3: Save credentials to Key Vault (if enabled)
        stored_in_keyvault = False
        try:
            if use_keyvault and cred_store:
                logger.info(f"Saving credentials to Key Vault for: {request.name}")
                
                cred_config = {
                    "db_type": request.db_type,
                    "host": request.host,
                    "port": request.port,
                    "database": request.database,
                    "username": request.username,
                    "password": request.password,
                    "filepath": request.filepath,
                }
                
                success, kv_message = cred_store.save_credentials(request.name, cred_config)
                if success:
                    logger.info(f"✓ Credentials saved to Key Vault: {request.name}")
                    stored_in_keyvault = True
                else:
                    logger.warning(f"Failed to save to Key Vault: {kv_message}")
                    warnings.append(f"Key Vault save warning: {kv_message}")
            else:
                logger.info("Key Vault integration not available, credentials not stored remotely")
                
        except Exception as e:
            logger.error(f"Key Vault save error: {str(e)}")
            warnings.append(f"Could not save to Key Vault: {str(e)}")

        # Step 4: Save to local config (as fallback/reference)
        success, local_message = db_connector.save_database_config(
            name=request.name,
            db_type=request.db_type,
            database=request.database,
            host=request.host,
            port=request.port,
            username=request.username,
            password=request.password if not stored_in_keyvault else None,  # Don't store password if in KV
            filepath=request.filepath,
        )

        if not success:
            logger.error(f"Failed to save local config: {local_message}")
            return DatabaseCredentialsResponse(
                success=False,
                message=f"Failed to save configuration: {local_message}",
                stored_in_keyvault=False
            )

        message = f"✓ Database '{request.name}' configured successfully"
        if stored_in_keyvault:
            message += " (credentials secured in Azure Key Vault)"
        else:
            message += " (credentials stored locally)"

        return DatabaseCredentialsResponse(
            success=True,
            message=message,
            stored_in_keyvault=stored_in_keyvault,
            is_readonly=is_readonly,
            readonly_message=readonly_message,
            permission_details=permission_details,
            warnings=warnings if warnings else None
        )

    except Exception as e:
        logger.error(f"Error saving database config: {str(e)}")
        return DatabaseCredentialsResponse(
            success=False,
            message=f"Unexpected error: {str(e)}",
            stored_in_keyvault=False
        )


@router.get("", response_model=DatabaseListResponse)
async def list_databases():
    """List all saved database configurations"""
    database_names = db_connector.list_databases()
    databases = []
    active = None
    if db_connector.active_database:
        active = db_connector.active_database.name
        
    for name in database_names:
        info = db_connector.get_database_info(name)
        if info:
            db_obj = {
                "db_name": name,
                "db_type": info.get("db_type", ""),
                "host": info.get("host"),
                "port": info.get("port"),
                "database": info.get("database", ""),
                "username": info.get("username"),
                "filepath": info.get("filepath"),
                "active": (name == active)
            }
            databases.append(DatabaseConfig(**db_obj))
            
    return DatabaseListResponse(databases=databases, active=active)


@router.get("/{database_name}", response_model=DatabaseDetailsResponse)
async def get_database_info(database_name: str):
    """Get information about a specific database"""
    info = db_connector.get_database_info(database_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
    
    info_dict = info.copy()
    if 'name' in info_dict:
        info_dict['db_name'] = info_dict.pop('name')
    elif 'db_name' not in info_dict:
        info_dict['db_name'] = database_name
        
    return DatabaseDetailsResponse(database=DatabaseConfig(**info_dict))


@router.delete("/{database_name}", response_model=Dict)
async def delete_database(database_name: str):
    """Delete a database configuration"""
    success, message = db_connector.delete_database_config(database_name)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    # Si se elimina la BD activa, sincronizar nl2sql_generator para que limpie su schema
    if nl2sql_generator and success:
        try:
            # Si era la BD activa, limpiar el schema
            if nl2sql_generator._active_db_name == database_name:
                nl2sql_generator._active_schema = None
                nl2sql_generator._active_db_name = None
                nl2sql_generator._active_db_type = None
                nl2sql_generator._active_connector = None
                nl2sql_generator._schema_loaded_at = None
                logger.info(f"✅ Schema de nl2sql_generator limpiado para BD eliminada: {database_name}")
        except Exception as e:
            logger.warning(f"⚠ Error sincronizando eliminación en nl2sql_generator: {e}")
    
    return {"success": success, "message": message}


@router.post("/{database_name}/activate", response_model=DatabaseActivateResponse)
async def activate_database(database_name: str):
    """Set a database as active"""
    success, message = db_connector.set_active_database(database_name)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    # Nota: El schema se sincronizará cuando se haga scan_schema desde el frontend
    # No intentamos cargar el schema aquí para evitar incompatibilidades
    logger.info(f"✅ BD activada: {database_name} (schema se sincronizará en el próximo scan)")
    
    return DatabaseActivateResponse(success=success, message=message)


# ==================== KEY VAULT CREDENTIAL ENDPOINTS ====================

@router.post("/credentials/validate", response_model=CredentialSecurityCheckResponse)
async def validate_credentials_security(request: DatabaseTestRequest):
    """
    Validate credentials and check read-only permissions
    Useful before saving to Key Vault
    """
    try:
        # Test connection
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
        if not success:
            return CredentialSecurityCheckResponse(
                success=False,
                message=f"Connection test failed: {message}",
                is_readonly=False,
                readonly_message="Could not test",
                permission_details={},
                can_save_securely=False
            )

        # Validate permissions
        conn = db_connector.get_connection(config)
        if not conn:
            return CredentialSecurityCheckResponse(
                success=False,
                message="Could not establish connection for validation",
                is_readonly=False,
                readonly_message="Connection failed",
                permission_details={},
                can_save_securely=False
            )

        is_readonly, readonly_message, permission_details = permission_validator.validate_readonly_permissions(
            request.db_type, conn
        )
        db_connector.close_connection(conn)

        return CredentialSecurityCheckResponse(
            success=True,
            message="✓ Credentials validated successfully",
            is_readonly=is_readonly,
            readonly_message=readonly_message,
            permission_details=permission_details,
            can_save_securely=use_keyvault and cred_store is not None
        )

    except Exception as e:
        logger.error(f"Credential validation error: {str(e)}")
        return CredentialSecurityCheckResponse(
            success=False,
            message=f"Validation failed: {str(e)}",
            is_readonly=False,
            readonly_message=str(e),
            permission_details={},
            can_save_securely=False
        )


@router.get("/credentials/list", response_model=CredentialListResponse)
async def list_stored_credentials():
    """List all stored credentials in Key Vault"""
    if not use_keyvault or not cred_store:
        return CredentialListResponse(
            credentials=[],
            stored_in_keyvault=False
        )

    try:
        credentials, error = cred_store.list_credentials()
        return CredentialListResponse(
            credentials=credentials,
            stored_in_keyvault=True
        )
    except Exception as e:
        logger.error(f"Error listing credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list credentials: {str(e)}")


@router.get("/credentials/{database_name}/metadata", response_model=CredentialMetadataResponse)
async def get_credential_metadata(database_name: str):
    """Get metadata about stored credentials (without retrieving password)"""
    if not use_keyvault or not cred_store:
        raise HTTPException(status_code=503, detail="Key Vault integration not available")

    try:
        metadata, error = cred_store.get_secret_metadata(database_name)
        if error:
            raise HTTPException(status_code=404, detail=error)

        metadata["stored_in_keyvault"] = True
        return CredentialMetadataResponse(**metadata)

    except Exception as e:
        logger.error(f"Error getting credential metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/credentials/{database_name}", response_model=Dict)
async def delete_stored_credentials(database_name: str):
    """Delete credentials from Key Vault"""
    if not use_keyvault or not cred_store:
        raise HTTPException(status_code=503, detail="Key Vault integration not available")

    try:
        success, message = cred_store.delete_credentials(database_name)
        if not success:
            raise HTTPException(status_code=404, detail=message)

        return {"success": success, "message": message}

    except Exception as e:
        logger.error(f"Error deleting credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/credentials/{database_name}/verify", response_model=Dict)
async def verify_stored_credentials(database_name: str):
    """
    Verify that stored credentials still work
    Retrieves credentials from Key Vault and tests connection
    """
    if not use_keyvault or not cred_store:
        raise HTTPException(status_code=503, detail="Key Vault integration not available")

    try:
        # Get credentials from Key Vault
        credentials, error = cred_store.get_credentials(database_name)
        if error:
            raise HTTPException(status_code=404, detail=error)

        # Test connection
        config = DBConfig(
            name=database_name,
            db_type=credentials.get("db_type"),
            host=credentials.get("host"),
            port=credentials.get("port"),
            database=credentials.get("database"),
            username=credentials.get("username"),
            password=credentials.get("password"),
            filepath=credentials.get("filepath"),
        )

        success, message = db_connector.test_connection(config)

        return {
            "success": success,
            "message": message,
            "database_name": database_name,
            "verified_at": str(datetime.utcnow().isoformat())
        }

    except Exception as e:
        logger.error(f"Error verifying credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keyvault/status", response_model=Dict)
async def get_keyvault_status():
    """Get Azure Key Vault integration status"""
    try:
        if use_keyvault and cred_store:
            return {
                "enabled": True,
                "status": "✓ Connected",
                "vault_url": cred_store.key_vault_url,
                "product": "VeriQuery"
            }
        else:
            return {
                "enabled": False,
                "status": "⚠ Not connected",
                "reason": "Key Vault credentials not configured"
            }
    except Exception as e:
        return {
            "enabled": False,
            "status": "✗ Error",
            "error": str(e)
        }
