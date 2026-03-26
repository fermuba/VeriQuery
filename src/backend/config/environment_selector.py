"""
Environment-aware configuration selector.
Switches database configuration between development (Docker local) and production (Azure SQL)
based on ENVIRONMENT variable.

Usage:
    - Set ENVIRONMENT=development in .env for local Docker (Contoso)
    - Set ENVIRONMENT=production in .env for Azure SQL
    
The backend automatically loads the correct credentials based on this setting.
"""

import os
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def get_active_environment() -> str:
    """Get current environment: 'development' or 'production'."""
    env = os.getenv("ENVIRONMENT", "development").lower().strip()
    if env not in ("development", "production"):
        logger.warning(f"Invalid ENVIRONMENT='{env}', defaulting to 'development'")
        return "development"
    return env


def get_database_credentials() -> Tuple[str, str, str, int, str, str]:
    """
    Get database credentials based on ENVIRONMENT variable.
    
    Returns:
        Tuple[host, port, database, port_int, username, password]
        
    Examples:
        >>> host, port, db, port_int, user, pwd = get_database_credentials()
        >>> # For development (Docker):
        >>> # ('localhost', '1433', 'ContosoV210k', 1433, 'sa', 'VeriQuery26!')
        >>> # For production (Azure SQL):
        >>> # ('sql-forensic-southcentral.database.windows.net', '1433', 'db-forensic-data', 1433, 'sqladmin', 'Hackathon2026!Pass')
    """
    environment = get_active_environment()
    
    if environment == "production":
        # === PRODUCTION - Azure SQL ===
        host = os.getenv("SQL_SERVER", "sql-forensic-southcentral.database.windows.net")
        database = os.getenv("SQL_DATABASE", "db-forensic-data")
        username = os.getenv("SQL_USERNAME", "sqladmin")
        password = os.getenv("SQL_PASSWORD")
        port = os.getenv("DB_PORT", "1433")
        
        logger.info(f"🔵 PRODUCTION MODE: Using Azure SQL Server at {host}")
        
    else:
        # === DEVELOPMENT - Docker Local ===
        host = os.getenv("LOCAL_DB_HOST", "localhost")
        database = os.getenv("LOCAL_DB_NAME", "ContosoV210k")
        username = os.getenv("LOCAL_DB_USERNAME", "sa")
        password = os.getenv("LOCAL_DB_PASSWORD")
        port = os.getenv("LOCAL_DB_PORT", "1433")
        
        logger.info(f"🟢 DEVELOPMENT MODE: Using Docker at {host}:{port}")
    
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        port_int = 1433
    
    return host, port, database, port_int, username, password


def log_environment_info():
    """Log current environment configuration (without passwords)."""
    environment = get_active_environment()
    host, port, db, port_int, user, pwd = get_database_credentials()
    
    pwd_masked = "***" if pwd else "NOT SET ❌"
    
    logger.info(f"""
    ╔════════════════════════════════════════════════════╗
    ║        DATABASE ENVIRONMENT CONFIGURATION          ║
    ╠════════════════════════════════════════════════════╣
    ║ Environment:  {environment.upper():40} ║
    ║ Host:         {host:40} ║
    ║ Port:         {port:40} ║
    ║ Database:     {db:40} ║
    ║ Username:     {user:40} ║
    ║ Password:     {pwd_masked:40} ║
    ╚════════════════════════════════════════════════════╝
    """)


# Auto-setup: Override environment variables with selected credentials on import
def setup_environment_variables():
    """
    Automatically configure os.environ with the correct credentials 
    based on ENVIRONMENT setting.
    
    This function is called automatically when the module is imported,
    so the rest of the backend code doesn't need to change.
    """
    host, port, database, port_int, username, password = get_database_credentials()
    
    # Override the generic DB_* variables with the selected environment's values
    os.environ["DB_HOST"] = host
    os.environ["DB_PORT"] = str(port_int)
    os.environ["DB_NAME"] = database
    os.environ["DB_USERNAME"] = username
    if password:
        os.environ["DB_PASSWORD"] = password
    
    # Log the configuration on first setup
    log_environment_info()


# Automatically setup on import
try:
    setup_environment_variables()
except Exception as e:
    logger.error(f"Failed to setup environment variables: {e}")
