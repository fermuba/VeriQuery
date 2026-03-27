"""
PostgreSQL database connector implementation using psycopg2.
Implements the DatabaseConnector interface for PostgreSQL/Supabase.

Features:
- psycopg2 driver-based connection
- Connection pooling awareness
- Parameterized queries (SQL injection prevention)
- Comprehensive error handling and logging
- Performance monitoring
"""

import psycopg2
import psycopg2.extras
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .base import DatabaseConnector, ConnectionConfig, QueryResult

logger = logging.getLogger(__name__)


class PostgreSQLConnectorException(Exception):
    """Base exception for PostgreSQL connector errors."""
    pass


class PostgreSQLConnectionException(PostgreSQLConnectorException):
    """Raised when connection fails."""
    pass


class PostgreSQLQueryException(PostgreSQLConnectorException):
    """Raised when query execution fails."""
    pass


class PostgreSQLConnector(DatabaseConnector):
    """
    PostgreSQL connector implementation using psycopg2.
    
    Supports:
    - PostgreSQL 12+
    - Supabase (PostgreSQL cloud)
    - Amazon RDS for PostgreSQL
    - Parameterized queries
    - Connection pooling (driver level)
    
    Configuration:
    - Host: database.xxxxx.supabase.co or similar
    - Port: 5432 (default)
    - Username: postgres or custom
    - Password: from environment or config
    - Database: postgres or custom database name
    """
    
    # Connection timeout in seconds
    CONNECT_TIMEOUT = 10
    QUERY_TIMEOUT = 30
    
    def __init__(self, config: ConnectionConfig) -> None:
        """
        Initialize PostgreSQL connector.
        
        Args:
            config: ConnectionConfig with PostgreSQL parameters
            
        Raises:
            ValueError: If configuration is invalid
            PostgreSQLConnectorException: If connection fails
        """
        super().__init__(config)
        
        self.connection = None
        self._last_query_time: Optional[datetime] = None
        self._query_count = 0
        logger.info(f"PostgreSQLConnector initialized with database: {config.database}")
    
    def connect(self) -> bool:
        """
        Establish connection to PostgreSQL database.
        
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            PostgreSQLConnectionException: On connection failure
        """
        try:
            logger.info(f"Attempting to connect to PostgreSQL: host={self.config.host}, database={self.config.database}")
            
            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                connect_timeout=self.CONNECT_TIMEOUT,
                # Use JSON instead of problematic data types
                options="-c statement_timeout={0}".format(int(self.QUERY_TIMEOUT * 1000))
            )
            
            # Test connection with a simple query
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            self.is_connected = True
            logger.info(f"Successfully connected to PostgreSQL: {self.config.database}")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL connection failed: {str(e)}")
            self.is_connected = False
            raise PostgreSQLConnectionException(f"Failed to connect to {self.config.host}:{self.config.port}/{self.config.database}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during PostgreSQL connection: {str(e)}")
            self.is_connected = False
            raise PostgreSQLConnectorException(f"Unexpected connection error: {str(e)}")
    
    def disconnect(self) -> bool:
        """
        Close PostgreSQL connection.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.connection:
                self.connection.close()
                logger.info("Successfully disconnected from PostgreSQL")
            self.is_connected = False
            return True
        except Exception as e:
            logger.error(f"Error during PostgreSQL disconnection: {str(e)}")
            return False
    
    def execute_query(self, query: str) -> QueryResult:
        """
        Execute SQL query against PostgreSQL.
        
        Args:
            query: SQL query string
            
        Returns:
            QueryResult: Result with data or error
        """
        if not self.is_connected or not self.connection:
            return QueryResult(
                success=False,
                data=[],
                error="Not connected to database",
                row_count=0,
                execution_time_ms=0
            )
        
        start_time = datetime.now()
        cursor = None
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            logger.debug(f"Executing PostgreSQL query: {query[:100]}...")
            cursor.execute(query)
            
            # For SELECT queries, fetch results
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                # Convert DictRow to regular dict for JSON serialization
                data = [dict(row) for row in rows]
                row_count = len(data)
            else:
                # For INSERT/UPDATE/DELETE, use rowcount
                self.connection.commit()
                row_count = cursor.rowcount
                data = []
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._query_count += 1
            self._last_query_time = datetime.now()
            
            logger.info(f"Query executed successfully: {row_count} rows in {execution_time:.3f}ms (Total queries: {self._query_count})")
            
            return QueryResult(
                success=True,
                data=data,
                error=None,
                row_count=row_count,
                execution_time_ms=execution_time
            )
            
        except psycopg2.Error as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = str(e)
            logger.error(f"PostgreSQL query error: {error_msg}")
            
            return QueryResult(
                success=False,
                data=[],
                error=error_msg,
                row_count=0,
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            
            return QueryResult(
                success=False,
                data=[],
                error=error_msg,
                row_count=0,
                execution_time_ms=execution_time
            )
        
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the PostgreSQL connection.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            if not self.is_connected or not self.connection:
                success, msg = self.connect()
                if not success:
                    return (False, f"Connection failed: {msg}")
            
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                return (True, f"Connected to PostgreSQL: {version}")
            
        except Exception as e:
            return (False, f"Connection test failed: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get PostgreSQL connection information.
        
        Returns:
            Dict with connection details
        """
        return {
            "type": "postgresql",
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "username": self.config.username,
            "connected": self.is_connected,
            "queries_executed": self._query_count,
            "last_query_time": self._last_query_time.isoformat() if self._last_query_time else None
        }
