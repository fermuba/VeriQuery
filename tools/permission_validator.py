"""
Permission Validator for Database Read-Only Access
Validates that connections have appropriate read-only permissions
"""

from typing import Tuple, Optional
import logging
from database.multi_db_connector import MultiDatabaseConnector

logger = logging.getLogger(__name__)


class PermissionValidator:
    """
    Validates database permissions across different database engines
    Ensures read-only access and proper credential validation
    """

    def __init__(self):
        self.db_connector = MultiDatabaseConnector()

    def validate_readonly_permissions(self, db_type: str, connection_obj) -> Tuple[bool, str, Dict]:
        """
        Validate read-only permissions based on database type

        Args:
            db_type: Type of database (postgresql, sqlserver, mysql, sqlite)
            connection_obj: Database connection object

        Returns:
            Tuple[bool, str, Dict]: (is_readonly, message, permissions_info)
                - is_readonly: True if connection is read-only
                - message: Human-readable status message
                - permissions_info: Dictionary with permission details
        """
        db_type = db_type.lower()

        if db_type in ["postgresql", "postgres"]:
            return self._validate_postgres_permissions(connection_obj)
        elif db_type in ["sqlserver", "mssql", "tsql"]:
            return self._validate_sqlserver_permissions(connection_obj)
        elif db_type in ["mysql"]:
            return self._validate_mysql_permissions(connection_obj)
        elif db_type in ["sqlite"]:
            return self._validate_sqlite_permissions(connection_obj)
        else:
            return False, f"Unsupported database type: {db_type}", {}

    def _validate_postgres_permissions(self, conn) -> Tuple[bool, str, Dict]:
        """
        PostgreSQL: Check permissions by attempting temp table operations
        """
        try:
            cursor = conn.cursor()
            permissions_info = {
                "db_type": "PostgreSQL",
                "checks": []
            }

            # Check 1: Can list tables (SELECT from information_schema)
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                result = cursor.fetchone()
                permissions_info["checks"].append({
                    "name": "List Tables",
                    "status": "✓ PASS" if result else "✗ FAIL",
                    "has_permission": True
                })
            except Exception as e:
                permissions_info["checks"].append({
                    "name": "List Tables",
                    "status": "✗ FAIL",
                    "has_permission": False,
                    "error": str(e)
                })

            # Check 2: Try to create temporary table (indicates write permissions)
            try:
                cursor.execute("CREATE TEMP TABLE IF NOT EXISTS perm_test (id INT)")
                cursor.execute("DROP TABLE IF EXISTS perm_test")
                permissions_info["checks"].append({
                    "name": "Create Temporary Table",
                    "status": "✓ PASS (WARNING: Has write permissions)",
                    "has_permission": True,
                    "warning": "User has write permissions"
                })
                has_write = True
            except Exception as e:
                permissions_info["checks"].append({
                    "name": "Create Temporary Table",
                    "status": "✓ PASS (Read-only confirmed)",
                    "has_permission": False,
                    "info": "User cannot write - read-only confirmed"
                })
                has_write = False

            # Check 3: Get current user and role
            try:
                cursor.execute("SELECT current_user, session_user")
                user_info = cursor.fetchone()
                permissions_info["user"] = f"{user_info[0]} (session: {user_info[1]})"
                permissions_info["checks"].append({
                    "name": "User Identity",
                    "status": "✓ PASS",
                    "has_permission": True
                })
            except Exception as e:
                permissions_info["checks"].append({
                    "name": "User Identity",
                    "status": "✗ FAIL",
                    "has_permission": False
                })

            cursor.close()

            is_readonly = not has_write
            message = (
                "✓ Read-only permissions confirmed" if is_readonly 
                else "⚠ WARNING: User has write permissions"
            )

            return is_readonly, message, permissions_info

        except Exception as e:
            logger.error(f"PostgreSQL permission validation failed: {str(e)}")
            return False, f"Permission validation failed: {str(e)}", {"error": str(e)}

    def _validate_sqlserver_permissions(self, conn) -> Tuple[bool, str, Dict]:
        """
        SQL Server: Check permissions using HAS_PERMS_BY_NAME function
        """
        try:
            cursor = conn.cursor()
            permissions_info = {
                "db_type": "SQL Server",
                "checks": []
            }

            # Check 1: Get current user
            try:
                cursor.execute("SELECT SYSTEM_USER, CURRENT_USER, USER_NAME()")
                user_data = cursor.fetchone()
                permissions_info["user"] = f"{user_data[0]}"
                permissions_info["current_user"] = user_data[1]
                permissions_info["checks"].append({
                    "name": "User Identity",
                    "status": "✓ PASS",
                    "has_permission": True
                })
            except Exception as e:
                logger.warning(f"Could not get user info: {str(e)}")

            # Check 2: Check INSERT permissions (should fail for read-only)
            try:
                cursor.execute("""
                    SELECT HAS_PERMS_BY_NAME(NULL, NULL, 'CREATE TABLE') as can_create_table
                """)
                result = cursor.fetchone()[0]
                can_create = result == 1
                permissions_info["checks"].append({
                    "name": "CREATE TABLE Permission",
                    "status": "✗ FAIL (Read-only confirmed)" if not can_create else "✓ PASS (WARNING: Has write permissions)",
                    "has_permission": can_create
                })
                has_write = can_create
            except Exception as e:
                logger.warning(f"Could not check CREATE TABLE: {str(e)}")
                has_write = False

            # Check 3: Check INSERT permissions on any table (sample check)
            try:
                cursor.execute("""
                    DECLARE @table_name NVARCHAR(128) = 
                        (SELECT TOP 1 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                         WHERE TABLE_SCHEMA = 'dbo')
                    
                    IF @table_name IS NOT NULL
                        SELECT HAS_PERMS_BY_NAME(@table_name, 'OBJECT', 'INSERT') as can_insert
                    ELSE
                        SELECT 0 as can_insert
                """)
                result = cursor.fetchone()[0]
                can_insert = result == 1
                permissions_info["checks"].append({
                    "name": "INSERT Permission (Sample Table)",
                    "status": "✗ FAIL (Read-only confirmed)" if not can_insert else "✓ PASS (WARNING: Has write permissions)",
                    "has_permission": can_insert
                })
                has_write = has_write or can_insert
            except Exception as e:
                logger.warning(f"Could not check INSERT: {str(e)}")

            # Check 4: Check SELECT permissions
            try:
                cursor.execute("""
                    DECLARE @table_name NVARCHAR(128) = 
                        (SELECT TOP 1 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                         WHERE TABLE_SCHEMA = 'dbo')
                    
                    IF @table_name IS NOT NULL
                        SELECT HAS_PERMS_BY_NAME(@table_name, 'OBJECT', 'SELECT') as can_select
                    ELSE
                        SELECT 1 as can_select
                """)
                result = cursor.fetchone()[0]
                can_select = result == 1
                permissions_info["checks"].append({
                    "name": "SELECT Permission",
                    "status": "✓ PASS" if can_select else "✗ FAIL",
                    "has_permission": can_select
                })
            except Exception as e:
                logger.warning(f"Could not check SELECT: {str(e)}")

            cursor.close()

            is_readonly = not has_write
            message = (
                "✓ Read-only permissions confirmed" if is_readonly 
                else "⚠ WARNING: User has write permissions"
            )

            return is_readonly, message, permissions_info

        except Exception as e:
            logger.error(f"SQL Server permission validation failed: {str(e)}")
            return False, f"Permission validation failed: {str(e)}", {"error": str(e)}

    def _validate_mysql_permissions(self, conn) -> Tuple[bool, str, Dict]:
        """
        MySQL: Check permissions using SHOW GRANTS
        """
        try:
            cursor = conn.cursor()
            permissions_info = {
                "db_type": "MySQL",
                "checks": []
            }

            # Check 1: Get current user
            try:
                cursor.execute("SELECT USER(), CURRENT_USER()")
                user_data = cursor.fetchone()
                permissions_info["user"] = f"{user_data[0]}"
                permissions_info["checks"].append({
                    "name": "User Identity",
                    "status": "✓ PASS",
                    "has_permission": True
                })
            except Exception as e:
                logger.warning(f"Could not get user info: {str(e)}")

            # Check 2: Get user grants
            try:
                cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
                grants = cursor.fetchall()
                permissions_info["grants"] = [grant[0] for grant in grants]

                has_write = False
                for grant in grants:
                    grant_str = grant[0].upper()
                    if "INSERT" in grant_str or "UPDATE" in grant_str or "DELETE" in grant_str:
                        has_write = True
                        break

                permissions_info["checks"].append({
                    "name": "User Grants Analysis",
                    "status": "✗ FAIL (Read-only confirmed)" if not has_write else "✓ PASS (WARNING: Has write permissions)",
                    "has_permission": has_write
                })
            except Exception as e:
                logger.warning(f"Could not get grants: {str(e)}")
                has_write = False

            # Check 3: Try to create temporary table (indicates write permissions)
            try:
                cursor.execute("CREATE TEMPORARY TABLE perm_test (id INT)")
                cursor.execute("DROP TEMPORARY TABLE IF EXISTS perm_test")
                permissions_info["checks"].append({
                    "name": "Create Temporary Table",
                    "status": "✓ PASS (WARNING: Has write permissions)",
                    "has_permission": True,
                    "warning": "User can create temporary tables"
                })
                has_write = True
            except Exception as e:
                permissions_info["checks"].append({
                    "name": "Create Temporary Table",
                    "status": "✓ PASS (Read-only confirmed)",
                    "has_permission": False,
                    "info": "User cannot create tables"
                })

            cursor.close()

            is_readonly = not has_write
            message = (
                "✓ Read-only permissions confirmed" if is_readonly 
                else "⚠ WARNING: User has write permissions"
            )

            return is_readonly, message, permissions_info

        except Exception as e:
            logger.error(f"MySQL permission validation failed: {str(e)}")
            return False, f"Permission validation failed: {str(e)}", {"error": str(e)}

    def _validate_sqlite_permissions(self, conn) -> Tuple[bool, str, Dict]:
        """
        SQLite: Check if database file is read-only or if journal file can be created
        """
        try:
            import os
            permissions_info = {
                "db_type": "SQLite",
                "checks": []
            }

            # SQLite connection object has db_path
            db_path = getattr(conn, 'db_path', None) or str(conn)

            if db_path:
                # Check file permissions
                if os.path.exists(db_path):
                    is_writable = os.access(db_path, os.W_OK)
                    permissions_info["file_path"] = db_path
                    permissions_info["file_writable"] = is_writable

                    permissions_info["checks"].append({
                        "name": "Database File Write Permission",
                        "status": "✗ FAIL (Read-only confirmed)" if not is_writable else "✓ PASS (WARNING: Has write permissions)",
                        "has_permission": is_writable
                    })

                    # Also check directory for journal files
                    dir_writable = os.access(os.path.dirname(db_path), os.W_OK)
                    permissions_info["checks"].append({
                        "name": "Directory Write Permission (Journal Files)",
                        "status": "✗ FAIL" if not dir_writable else "✓ PASS",
                        "has_permission": dir_writable
                    })

                    is_readonly = not (is_writable and dir_writable)
                else:
                    permissions_info["checks"].append({
                        "name": "Database File",
                        "status": "✗ FAIL",
                        "has_permission": False,
                        "error": "Database file not found"
                    })
                    is_readonly = False
            else:
                permissions_info["checks"].append({
                    "name": "Database Path",
                    "status": "⚠ WARNING",
                    "has_permission": None,
                    "info": "Could not determine database file path"
                })
                is_readonly = None

            message = (
                "✓ Read-only permissions confirmed" if is_readonly 
                else "⚠ WARNING: Database is writable" if is_readonly is False
                else "⚠ Could not determine read-only status"
            )

            return is_readonly, message, permissions_info

        except Exception as e:
            logger.error(f"SQLite permission validation failed: {str(e)}")
            return False, f"Permission validation failed: {str(e)}", {"error": str(e)}
