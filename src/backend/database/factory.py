"""
Database connector factory.
Implements Factory Pattern for creating appropriate database connector instances.

This module provides a single entry point (get_database_connector) that returns
the correct database implementation based on configuration, enabling seamless
switching between different database backends without modifying application code.

Supported databases:
- SQL Server 2019+ (local Docker or Azure)
- SQLite (local development fallback)
- PostgreSQL (future support)
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

from .base import DatabaseConnector, ConnectionConfig
from .sql_server import SQLServerConnector

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DatabaseFactoryException(Exception):
    """Raised when database factory encounters an error."""
    pass


def get_database_connector() -> DatabaseConnector:
    """
    Factory function to create appropriate database connector.
    
    Returns:
        DatabaseConnector: Configured connector instance ready to use
        
    Raises:
        DatabaseFactoryException: If configuration is invalid or connector cannot be created
        
    Environment Variables (configure in .env):
        DATABASE_TYPE: Type of database ("sqlserver" or "sqlite", default: "sqlserver")
        
        For SQL Server:
        - DB_HOST: Server hostname (default: localhost)
        - DB_PORT: Server port (default: 1433)
        - DB_USERNAME: Database user (default: sa)
        - DB_PASSWORD: Database password (required)
        - DB_NAME: Database name (default: ContosoV210k)
        - DB_DRIVER: ODBC driver name (auto-detected if not provided)
        
        For SQLite:
        - SQLITE_PATH: Path to .db file (default: ./data/app.db)
        
    Examples:
        # Use SQL Server (production or local Docker)
        db = get_database_connector()
        db.connect()
        
        # Use as context manager (auto-disconnect)
        with get_database_connector() as db:
            result = db.execute_query("SELECT * FROM Users")
        
        # Override database type
        os.environ["DATABASE_TYPE"] = "sqlite"
        db = get_database_connector()
    """
    
    database_type = os.getenv("DATABASE_TYPE", "sqlserver").lower()
    
    logger.info(f"Creating database connector: {database_type}")
    
    if database_type == "sqlserver":
        return _create_sqlserver_connector()
    
    elif database_type == "sqlite":
        return _create_sqlite_connector()
    
    else:
        available = ["sqlserver", "sqlite"]
        raise DatabaseFactoryException(
            f"Unknown database type: {database_type}. "
            f"Available types: {', '.join(available)}"
        )


def _create_sqlserver_connector() -> SQLServerConnector:
    """
    Create and configure SQL Server connector.
    
    Returns:
        SQLServerConnector: Configured connector instance
        
    Raises:
        DatabaseFactoryException: If required configuration is missing
    """
    
    # Get configuration from environment with sensible defaults
    host = os.getenv("DB_HOST", "localhost")
    port_str = os.getenv("DB_PORT", "1433")
    username = os.getenv("DB_USERNAME", "sa")
    password = os.getenv("DB_PASSWORD")
    database = os.getenv("DB_NAME", "ContosoV210k")
    driver = os.getenv("DB_DRIVER")  # Optional, auto-detected if not provided
    
    # Validate required parameters
    if not password:
        raise DatabaseFactoryException(
            "DB_PASSWORD environment variable is required for SQL Server connection. "
            "Set it in .env file: DB_PASSWORD=your_password"
        )
    
    # Validate port is numeric
    try:
        port = int(port_str)
    except ValueError:
        raise DatabaseFactoryException(
            f"DB_PORT must be numeric, got: {port_str}"
        )
    
    # Build connection config
    config = ConnectionConfig(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        driver=driver
    )
    
    logger.info(
        f"Creating SQL Server connector: "
        f"host={host}, port={port}, database={database}"
    )
    
    try:
        connector = SQLServerConnector(config)
        logger.debug(f"SQL Server connector created successfully: {connector}")
        return connector
        
    except Exception as e:
        logger.error(f"Failed to create SQL Server connector: {e}")
        raise DatabaseFactoryException(f"Failed to create SQL Server connector: {e}")


def _create_sqlite_connector():
    """
    Create and configure SQLite connector (for development/testing).
    
    Returns:
        SQLiteConnector: Configured connector instance
        
    Raises:
        DatabaseFactoryException: If SQLite support is not yet implemented
        
    Note:
        SQLite is for local development and testing only.
        For production, use SQL Server or PostgreSQL.
    """
    
    sqlite_path = os.getenv("SQLITE_PATH", "./data/app.db")
    
    logger.info(f"Creating SQLite connector: path={sqlite_path}")
    
    # SQLite connector not yet implemented
    # This is a placeholder for future development
    raise DatabaseFactoryException(
        "SQLite connector is not yet implemented. "
        "Use DATABASE_TYPE=sqlserver for production."
    )


def validate_database_connection() -> bool:
    """
    Validate that database connection is working.
    
    This function attempts to create a connector and perform a health check.
    Useful for application startup validation.
    
    Returns:
        bool: True if connection is valid, False otherwise
        
    Example:
        if not validate_database_connection():
            logger.error("Database validation failed, exiting")
            sys.exit(1)
    """
    
    try:
        logger.info("Validating database connection...")
        connector = get_database_connector()
        
        if not connector.connect():
            logger.error("Failed to establish connection")
            return False
        
        is_healthy, message = connector.health_check()
        connector.disconnect()
        
        if is_healthy:
            logger.info(f"Database validation successful: {message}")
            return True
        else:
            logger.error(f"Database health check failed: {message}")
            return False
            
    except Exception as e:
        logger.error(f"Database validation failed with exception: {e}")
        return False


def get_connector_info() -> dict:
    """
    Get information about the current database connector.
    
    Useful for debugging and monitoring.
    
    Returns:
        dict: Connection information and status
    """
    
    try:
        database_type = os.getenv("DATABASE_TYPE", "sqlserver").lower()
        
        if database_type == "sqlserver":
            return {
                "type": "sqlserver",
                "host": os.getenv("DB_HOST", "localhost"),
                "port": os.getenv("DB_PORT", "1433"),
                "database": os.getenv("DB_NAME", "ContosoV210k"),
                "driver": os.getenv("DB_DRIVER", "auto-detected"),
                "status": "configured"
            }
        
        elif database_type == "sqlite":
            return {
                "type": "sqlite",
                "path": os.getenv("SQLITE_PATH", "./data/app.db"),
                "status": "configured"
            }
        
        else:
            return {
                "type": database_type,
                "status": "unknown"
            }
            
    except Exception as e:
        logger.error(f"Error getting connector info: {e}")
        return {"status": "error", "error": str(e)}
