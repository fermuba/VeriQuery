"""
Database connectivity module.

Provides pluggable database connectors following Strategy and Factory patterns.
Supports multiple database backends with consistent interface.

Usage:
    from src.backend.database import get_database_connector
    
    db = get_database_connector()
    db.connect()
    result = db.execute_query("SELECT * FROM Users")
    db.disconnect()

Or with context manager:
    from src.backend.database import get_database_connector
    
    with get_database_connector() as db:
        result = db.execute_query("SELECT TOP 10 * FROM Users")
"""

from .base import (
    DatabaseConnector,
    ConnectionConfig,
    QueryResult,
)
from .sql_server import SQLServerConnector
from .factory import (
    get_database_connector,
    validate_database_connection,
    get_connector_info,
    DatabaseFactoryException,
)

__all__ = [
    # Base classes
    "DatabaseConnector",
    "ConnectionConfig",
    "QueryResult",
    # Implementations
    "SQLServerConnector",
    # Factory functions
    "get_database_connector",
    "validate_database_connection",
    "get_connector_info",
    # Exceptions
    "DatabaseFactoryException",
]
