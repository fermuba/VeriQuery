"""
Base abstract class for database connectors.
Follows Strategy Pattern for pluggable database implementations.

This module defines the interface that all database adapters must implement,
ensuring loose coupling and high cohesion across the application.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """
    Data class for database connection configuration.
    Immutable and type-safe configuration holder.
    """
    host: str
    port: int
    username: str
    password: str
    database: str
    driver: Optional[str] = None  # For ODBC-based connections
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.host or not self.port or not self.username or not self.database:
            raise ValueError("All connection parameters are required")
        if not isinstance(self.port, int) or self.port <= 0:
            raise ValueError("Port must be a positive integer")


@dataclass
class QueryResult:
    """
    Standardized result format for all database queries.
    Ensures consistent response structure across implementations.
    """
    success: bool
    data: List[Dict[str, Any]]
    row_count: int
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate result integrity."""
        if not self.success and not self.error:
            raise ValueError("Failed queries must include error message")
        if self.success and self.error:
            logger.warning("Successful query has error message - this should not happen")


class DatabaseConnector(ABC):
    """
    Abstract base class for database connectors.
    
    All database implementations must inherit from this class and implement
    the abstract methods. This ensures a consistent interface regardless of
    the underlying database technology.
    
    Features:
    - Type-safe connection configuration
    - Standardized error handling
    - Query execution with result normalization
    - Connection lifecycle management
    - Comprehensive logging
    """
    
    def __init__(self, config: ConnectionConfig) -> None:
        """
        Initialize the database connector with configuration.
        
        Args:
            config: ConnectionConfig object with all connection parameters
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, ConnectionConfig):
            raise TypeError("config must be a ConnectionConfig instance")
        
        self.config = config
        self.is_connected = False
        self._connection = None
        logger.info(f"{self.__class__.__name__} initialized with database: {config.database}")
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the database.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Implementation must:
        - Handle connection timeout gracefully
        - Log connection attempts and results
        - Set self.is_connected flag appropriately
        - Raise specific exceptions on critical failures
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close the database connection gracefully.
        
        Returns:
            bool: True if disconnection successful, False otherwise
            
        Implementation must:
        - Handle already-closed connections
        - Clean up resources properly
        - Log disconnection
        - Never raise exceptions
        """
        pass
    
    @abstractmethod
    def execute_query(self, sql: str) -> QueryResult:
        """
        Execute a SELECT query and return standardized result.
        
        Args:
            sql: SQL query string to execute (must be SELECT only for safety)
            
        Returns:
            QueryResult: Standardized result object
            
        Implementation must:
        - Validate SQL is SELECT-only (security)
        - Return empty data list for no results (not error)
        - Capture row count
        - Handle timeout, connection errors gracefully
        - Log query execution (without sensitive data)
        - Never raise exceptions (return QueryResult with error)
        """
        pass
    
    @abstractmethod
    def execute_query_with_params(self, sql: str, params: Dict[str, Any]) -> QueryResult:
        """
        Execute a parameterized SELECT query.
        
        Args:
            sql: SQL query with parameter placeholders
            params: Dictionary of parameter names and values
            
        Returns:
            QueryResult: Standardized result object
            
        Implementation must:
        - Prevent SQL injection via parameterization
        - Handle parameter type conversion
        - Log execution without exposing sensitive values
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Tuple[bool, str]:
        """
        Perform a health check on the database connection.
        
        Returns:
            Tuple[bool, str]: (is_healthy, message)
                - True/False: Whether database is accessible
                - message: Human-readable status message
                
        Implementation must:
        - Perform lightweight check (e.g., SELECT 1)
        - Not modify any data
        - Handle timeout and network errors
        - Return clear status messages
        """
        pass
    
    def __enter__(self):
        """Context manager entry: establish connection."""
        if not self.connect():
            raise RuntimeError(f"Failed to connect to {self.config.database}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: close connection gracefully."""
        self.disconnect()
        if exc_type:
            logger.error(f"Exception in context manager: {exc_type.__name__}: {exc_val}")
        return False
    
    def __repr__(self) -> str:
        """String representation for logging and debugging."""
        return (
            f"{self.__class__.__name__}("
            f"host={self.config.host}, "
            f"database={self.config.database}, "
            f"connected={self.is_connected})"
        )
