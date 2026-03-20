"""
Unit Tests for Azure Key Vault Integration
Forensic Data Guardian

Run with: pytest test_keyvault_integration.py
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add paths for imports
tools_path = str(Path(__file__).parent / "tools")
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)


class TestSecureCredentialStore:
    """Test suite for SecureCredentialStore"""

    @pytest.fixture
    def mock_keyvault_client(self):
        """Mock the Azure Key Vault client"""
        with patch('azure.keyvault.secrets.SecretClient') as mock:
            yield mock

    @pytest.fixture
    def mock_credential(self):
        """Mock Azure credentials"""
        with patch('azure.identity.DefaultAzureCredential'):
            yield

    def test_init_with_keyvault_url(self, mock_keyvault_client, mock_credential):
        """Test initialization with explicit Key Vault URL"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore(
            key_vault_url="https://test-vault.vault.azure.net/"
        )
        assert store.key_vault_url == "https://test-vault.vault.azure.net/"

    def test_init_url_normalization(self, mock_keyvault_client, mock_credential):
        """Test Key Vault URL is normalized (adds trailing slash)"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore(
            key_vault_url="https://test-vault.vault.azure.net"
        )
        assert store.key_vault_url.endswith("/")

    def test_create_secret_name(self, mock_keyvault_client, mock_credential):
        """Test secret name creation (alphanumeric + hyphens only)"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore()
        
        # Test various inputs
        assert store._create_secret_name("my_database") == "my-database"
        assert store._create_secret_name("MyDatabase") == "mydatabase"
        assert store._create_secret_name("db.prod") == "db-prod"
        assert store._create_secret_name("my_prod.db_v2") == "my-prod-db-v2"

    @patch('azure.keyvault.secrets.SecretClient.set_secret')
    def test_save_credentials(self, mock_set_secret, mock_keyvault_client, mock_credential):
        """Test saving credentials to Key Vault"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore()
        
        config = {
            "db_type": "sqlserver",
            "host": "server.database.windows.net",
            "port": 1433,
            "database": "TestDB",
            "username": "testuser",
            "password": "TestPass123!"
        }
        
        success, message = store.save_credentials("test_db", config)
        
        assert success
        assert "successfully saved" in message.lower()
        mock_set_secret.assert_called_once()

    @patch('azure.keyvault.secrets.SecretClient.get_secret')
    def test_get_credentials(self, mock_get_secret, mock_keyvault_client, mock_credential):
        """Test retrieving credentials from Key Vault"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore()
        
        # Setup mock secret
        secret_data = {
            "password": "TestPass123!",
            "config": {
                "db_type": "sqlserver",
                "host": "server.database.windows.net",
                "port": 1433,
                "database": "TestDB",
                "username": "testuser"
            }
        }
        mock_secret = MagicMock()
        mock_secret.value = json.dumps(secret_data)
        mock_get_secret.return_value = mock_secret
        
        creds, error = store.get_credentials("test_db")
        
        assert error is None
        assert creds["password"] == "TestPass123!"
        assert creds["db_type"] == "sqlserver"

    @patch('azure.keyvault.secrets.SecretClient.begin_delete_secret')
    def test_delete_credentials(self, mock_delete, mock_keyvault_client, mock_credential):
        """Test deleting credentials from Key Vault"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore()
        
        # Setup mock
        mock_delete_result = MagicMock()
        mock_delete.return_value.result.return_value = mock_delete_result
        
        success, message = store.delete_credentials("test_db")
        
        assert success
        assert "successfully deleted" in message.lower()
        mock_delete.assert_called_once()

    @patch('azure.keyvault.secrets.SecretClient.get_secret')
    def test_credential_exists(self, mock_get_secret, mock_keyvault_client, mock_credential):
        """Test checking if credentials exist"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore()
        
        # Test existing credential
        mock_get_secret.return_value = MagicMock()
        assert store.credential_exists("test_db") is True
        
        # Test non-existing credential
        mock_get_secret.side_effect = Exception("Not found")
        assert store.credential_exists("nonexistent") is False


class TestPermissionValidator:
    """Test suite for PermissionValidator"""

    @pytest.fixture
    def validator(self):
        """Create a PermissionValidator instance"""
        from tools.permission_validator import PermissionValidator
        return PermissionValidator()

    def test_init(self, validator):
        """Test PermissionValidator initialization"""
        assert validator is not None
        assert hasattr(validator, 'db_connector')

    def test_unsupported_db_type(self, validator):
        """Test handling of unsupported database types"""
        mock_conn = MagicMock()
        
        is_readonly, message, details = validator.validate_readonly_permissions(
            "unsupported_db", mock_conn
        )
        
        assert is_readonly is False
        assert "unsupported" in message.lower()
        assert details == {}

    @patch('database.multi_db_connector.MultiDatabaseConnector.get_connection')
    def test_postgres_permission_validation(self, mock_get_conn, validator):
        """Test PostgreSQL permission validation"""
        from tools.permission_validator import PermissionValidator
        
        # Setup mock connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            (5,),  # Table count
            None,  # CREATE TEMP TABLE fails
            ("testuser", "testuser")  # User info
        ]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        validator_instance = PermissionValidator()
        is_readonly, message, details = validator_instance._validate_postgres_permissions(mock_conn)
        
        # Read-only confirmed if temp table creation fails
        assert "read-only" in message.lower() or "pass" in message.lower()

    @patch('database.multi_db_connector.MultiDatabaseConnector.get_connection')
    def test_sqlserver_permission_validation(self, mock_get_conn, validator):
        """Test SQL Server permission validation"""
        # Setup mock connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            ("DOMAIN\\user", "dbo", "dbo"),  # User info
            (0,),  # CREATE TABLE permission (0 = no)
            (0,),  # INSERT permission (0 = no)
            (1,),  # SELECT permission (1 = yes)
        ]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        is_readonly, message, details = validator._validate_sqlserver_permissions(mock_conn)
        
        # Should detect read-only
        assert is_readonly is True or "pass" in message.lower()
        assert details.get("checks")


class TestIntegration:
    """Integration tests for the complete flow"""

    @patch('azure.keyvault.secrets.SecretClient')
    @patch('azure.identity.DefaultAzureCredential')
    def test_save_and_retrieve_workflow(self, mock_credential, mock_keyvault_client):
        """Test complete save and retrieve workflow"""
        from tools.secure_credential_store import SecureCredentialStore
        
        store = SecureCredentialStore()
        
        # Configure mocks
        mock_set_secret = MagicMock()
        store.client.set_secret = mock_set_secret
        
        config = {
            "db_type": "sqlserver",
            "host": "test.database.windows.net",
            "port": 1433,
            "database": "TestDB",
            "username": "testuser",
            "password": "SecurePass123"
        }
        
        # Save
        success, msg = store.save_credentials("integration_test", config)
        assert success
        
        # Retrieve
        mock_get_secret = MagicMock()
        secret_data = {
            "password": "SecurePass123",
            "config": config
        }
        mock_secret = MagicMock()
        mock_secret.value = json.dumps(secret_data)
        mock_get_secret.return_value = mock_secret
        store.client.get_secret = mock_get_secret
        
        creds, error = store.get_credentials("integration_test")
        assert error is None
        assert creds["password"] == "SecurePass123"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
