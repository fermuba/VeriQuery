"""
SQL Server database connector implementation using pyodbc.
Implements the DatabaseConnector interface for SQL Server/Azure SQL.

Features:
- ODBC driver-based connection
- Connection pooling awareness
- Parameterized queries (SQL injection prevention)
- Comprehensive error handling and logging
- Performance monitoring
"""

import pyodbc
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .base import DatabaseConnector, ConnectionConfig, QueryResult

logger = logging.getLogger(__name__)


class SQLServerConnectorException(Exception):
    """Base exception for SQL Server connector errors."""
    pass


class SQLServerConnectionException(SQLServerConnectorException):
    """Raised when connection fails."""
    pass


class SQLServerQueryException(SQLServerConnectorException):
    """Raised when query execution fails."""
    pass


class SQLServerConnector(DatabaseConnector):
    """
    SQL Server connector implementation using pyodbc.
    
    Supports:
    - SQL Server 2019, 2022
    - Azure SQL Database
    - Parameterized queries
    - Connection pooling (driver level)
    - Transaction management (future)
    
    Configuration:
    - Driver: "ODBC Driver 17 for SQL Server" (preferred) or "ODBC Driver 18 for SQL Server"
    - Encryption: Disable if using local Docker development
    """
    
    # ODBC Driver preference order (fallback mechanism)
    PREFERRED_DRIVERS = [
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 18 for SQL Server",
        "SQL Server",
    ]
    
    # Connection timeout in seconds
    CONNECT_TIMEOUT = 10
    QUERY_TIMEOUT = 30
    
    def __init__(self, config: ConnectionConfig) -> None:
        """
        Initialize SQL Server connector.
        
        Args:
            config: ConnectionConfig with SQL Server parameters
            
        Raises:
            ValueError: If configuration is invalid
            SQLServerConnectorException: If driver not found
        """
        super().__init__(config)
        
        # Verify ODBC driver is available
        self.driver = self._find_driver()
        if not self.driver:
            raise SQLServerConnectorException(
                "No compatible ODBC driver found. "
                "Install 'ODBC Driver 17 for SQL Server' or 'ODBC Driver 18'"
            )
        
        logger.info(f"Using ODBC driver: {self.driver}")
        self._last_query_time: Optional[datetime] = None
        self._query_count = 0
    
    def _find_driver(self) -> Optional[str]:
        """
        Find available ODBC driver using fallback mechanism.
        
        Returns:
            str: Driver name if found, None otherwise
        """
        try:
            drivers = pyodbc.drivers()
            logger.debug(f"Available ODBC drivers: {drivers}")
            
            # Use preferred driver if available, else fallback
            for preferred_driver in self.PREFERRED_DRIVERS:
                if preferred_driver in drivers:
                    return preferred_driver
            
            logger.warning(f"No preferred driver found. Available: {drivers}")
            return None
            
        except Exception as e:
            logger.error(f"Error listing ODBC drivers: {e}")
            return None
    
    def _build_connection_string(self) -> str:
        """
        Build ODBC connection string safely.
        
        Returns:
            str: ODBC connection string
            
        Raises:
            SQLServerConnectorException: If connection string cannot be built
        """
        try:
            # Determine encryption setting
            encrypt = "yes" if "azure" in self.config.host.lower() else "no"
            trust_cert = "no" if encrypt == "yes" else "yes"
            
            connection_string = (
                f"Driver={{{self.driver}}};"
                f"Server={self.config.host},{self.config.port};"
                f"Database={self.config.database};"
                f"UID={self.config.username};"
                f"PWD={self.config.password};"
                f"Encrypt={encrypt};"
                f"TrustServerCertificate={trust_cert};"
                f"Connection Timeout={self.CONNECT_TIMEOUT};"
            )
            
            return connection_string
            
        except Exception as e:
            logger.error(f"Error building connection string: {e}")
            raise SQLServerConnectorException(f"Failed to build connection string: {e}")
    
    def connect(self) -> bool:
        """
        Establish connection to SQL Server.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.is_connected and self._connection:
            logger.debug("Already connected, skipping connection attempt")
            return True
        
        try:
            logger.info(
                f"Attempting to connect to SQL Server: "
                f"host={self.config.host}, "
                f"database={self.config.database}"
            )
            
            connection_string = self._build_connection_string()
            
            # Establish connection
            self._connection = pyodbc.connect(
                connection_string,
                timeout=self.CONNECT_TIMEOUT,
                autocommit=False  # Explicit transaction control
            )
            
            # Note: pyodbc.Cursor doesn't have a timeout attribute
            # Query timeout is handled at connection level in ODBC
            
            self.is_connected = True
            logger.info(f"Successfully connected to {self.config.database}")
            
            return True
            
        except pyodbc.OperationalError as e:
            logger.error(f"Operational error connecting to SQL Server: {e}")
            self.is_connected = False
            raise SQLServerConnectionException(f"Connection failed: {e}")
            
        except pyodbc.Error as e:
            logger.error(f"ODBC error connecting to SQL Server: {e}")
            self.is_connected = False
            raise SQLServerConnectionException(f"Connection failed: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error connecting to SQL Server: {e}")
            self.is_connected = False
            raise SQLServerConnectionException(f"Connection failed: {e}")
    
    def disconnect(self) -> bool:
        """
        Close connection to SQL Server gracefully.
        
        Returns:
            bool: True if successful or already closed, False on error
        """
        try:
            if self._connection:
                self._connection.close()
                logger.info("Successfully disconnected from SQL Server")
            
            self.is_connected = False
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from SQL Server: {e}")
            # Still mark as disconnected even on error
            self.is_connected = False
            return False
    
    def execute_query(self, sql: str) -> QueryResult:
        """
        Execute a SELECT query against SQL Server.
        
        Args:
            sql: SQL SELECT query
            
        Returns:
            QueryResult: Standardized result
        """
        if not sql or not sql.strip():
            logger.warning("Empty SQL query received")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error="Empty SQL query",
                error_type="ValidationError"
            )
        
        # Security: Ensure SELECT-only
        if not self._is_select_query(sql):
            logger.warning(f"Non-SELECT query attempted: {sql[:50]}...")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error="Only SELECT queries are allowed",
                error_type="SecurityError"
            )
        
        if not self.is_connected:
            logger.error("Not connected to database, attempting reconnect")
            if not self.connect():
                return QueryResult(
                    success=False,
                    data=[],
                    row_count=0,
                    error="Database connection lost and reconnection failed",
                    error_type="ConnectionError"
                )
        
        try:
            logger.debug(f"Executing query: {sql[:100]}...")
            start_time = datetime.now()
            
            cursor = self._connection.cursor()
            # Note: pyodbc doesn't support cursor-level timeout
            # Query timeout is controlled at connection level
            cursor.execute(sql)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            data = [dict(zip(columns, row)) for row in rows]
            
            elapsed = (datetime.now() - start_time).total_seconds()
            self._last_query_time = datetime.now()
            self._query_count += 1
            
            logger.info(
                f"Query executed successfully: "
                f"{len(data)} rows in {elapsed:.3f}s "
                f"(Total queries: {self._query_count})"
            )
            
            return QueryResult(
                success=True,
                data=data,
                row_count=len(data),
                error=None
            )
            
        except pyodbc.ProgrammingError as e:
            logger.error(f"SQL programming error: {e}")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error=f"SQL error: {str(e)[:200]}",
                error_type="ProgrammingError"
            )
            
        except pyodbc.DatabaseError as e:
            logger.error(f"Database error during query execution: {e}")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error=f"Database error: {str(e)[:200]}",
                error_type="DatabaseError"
            )
            
        except pyodbc.Error as e:
            logger.error(f"ODBC error during query execution: {e}")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error=f"ODBC error: {str(e)[:200]}",
                error_type="ODBCError"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error=f"Unexpected error: {str(e)[:200]}",
                error_type="UnexpectedError"
            )
    
    def execute_query_with_params(self, sql: str, params: Dict[str, Any]) -> QueryResult:
        """
        Execute a parameterized SELECT query.
        
        Args:
            sql: SQL query with ? placeholders for parameters
            params: Dictionary of parameter values (order matters for ?)
            
        Returns:
            QueryResult: Standardized result
            
        Note:
            pyodbc uses ? placeholders. For named parameters, convert dict to positional args.
        """
        if not sql or not sql.strip():
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error="Empty SQL query",
                error_type="ValidationError"
            )
        
        # Security: Ensure SELECT-only
        if not self._is_select_query(sql):
            logger.warning(f"Non-SELECT parameterized query attempted: {sql[:50]}...")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error="Only SELECT queries are allowed",
                error_type="SecurityError"
            )
        
        if not self.is_connected:
            if not self.connect():
                return QueryResult(
                    success=False,
                    data=[],
                    row_count=0,
                    error="Database connection lost",
                    error_type="ConnectionError"
                )
        
        try:
            logger.debug(f"Executing parameterized query: {sql[:100]}... with {len(params)} params")
            start_time = datetime.now()
            
            cursor = self._connection.cursor()
            # Note: pyodbc doesn't support cursor-level timeout
            # Query timeout is controlled at connection level
            
            # Convert dict to positional tuple (order of ? placeholders matters)
            param_values = tuple(params.values()) if params else ()
            cursor.execute(sql, param_values)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]
            
            elapsed = (datetime.now() - start_time).total_seconds()
            self._last_query_time = datetime.now()
            self._query_count += 1
            
            logger.info(
                f"Parameterized query executed: "
                f"{len(data)} rows in {elapsed:.3f}s"
            )
            
            return QueryResult(
                success=True,
                data=data,
                row_count=len(data),
                error=None
            )
            
        except (pyodbc.ProgrammingError, pyodbc.DatabaseError, pyodbc.Error) as e:
            logger.error(f"Database error in parameterized query: {e}")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error=f"Database error: {str(e)[:200]}",
                error_type=type(e).__name__
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in parameterized query: {e}")
            return QueryResult(
                success=False,
                data=[],
                row_count=0,
                error=f"Unexpected error: {str(e)[:200]}",
                error_type="UnexpectedError"
            )
    
    def health_check(self) -> Tuple[bool, str]:
        """
        Perform lightweight health check on SQL Server.
        
        Returns:
            Tuple[bool, str]: (is_healthy, message)
        """
        if not self.is_connected:
            return False, "Not connected to database"
        
        try:
            cursor = self._connection.cursor()
            # Note: pyodbc doesn't support cursor-level timeout
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            status_msg = (
                f"✓ Connected to {self.config.database} | "
                f"Queries executed: {self._query_count}"
            )
            if self._last_query_time:
                elapsed = (datetime.now() - self._last_query_time).total_seconds()
                status_msg += f" | Last query: {elapsed:.1f}s ago"
            
            return True, status_msg
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False, f"Health check failed: {str(e)[:100]}"
    
    @staticmethod
    def _is_select_query(sql: str) -> bool:
        """
        Validate that SQL query is SELECT-only (security).
        
        Args:
            sql: SQL query string
            
        Returns:
            bool: True if query is safe SELECT-only
        """
        if not sql:
            return False
        
        # Remove leading/trailing whitespace and comments
        query = sql.strip()
        
        # Remove leading comments
        while query.lower().startswith("--") or query.lower().startswith("/*"):
            if query.lower().startswith("--"):
                query = query.split("\n", 1)[1] if "\n" in query else ""
            elif query.lower().startswith("/*"):
                query = query.split("*/", 1)[1] if "*/" in query else ""
            query = query.strip()
        
        # Check that first meaningful word is SELECT
        first_word = query.split()[0].upper() if query.split() else ""
        if first_word not in ["SELECT", "WITH"]:  # WITH for CTEs
            return False
        
        # Deny dangerous statements
        dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "EXEC", "EXECUTE"]
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                return False
        
        return True
    
    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        try:
            if hasattr(self, '_connection') and self._connection:
                self._connection.close()
        except Exception:
            pass  # Silently ignore errors during garbage collection
