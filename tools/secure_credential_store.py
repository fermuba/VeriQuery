"""
Secure Credential Store using Azure Key Vault
Manages database credentials securely for VeriQuery
"""

from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from typing import Dict, Optional, Tuple
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class SecureCredentialStore:
    """
    Manages database credentials in Azure Key Vault
    Provides secure save, retrieve, and delete operations
    """

    def __init__(self, key_vault_url: Optional[str] = None, 
                 use_service_principal: bool = False,
                 sp_client_id: Optional[str] = None,
                 sp_client_secret: Optional[str] = None,
                 sp_tenant_id: Optional[str] = None):
        """
        Initialize Azure Key Vault connection

        Args:
            key_vault_url: Azure Key Vault URL (e.g., https://<vault-name>.vault.azure.net/)
                          If None, uses KEYVAULT_URL environment variable
            use_service_principal: If True, uses Service Principal credentials
            sp_client_id: Service Principal Client ID
            sp_client_secret: Service Principal Client Secret
            sp_tenant_id: Service Principal Tenant ID
        """
        self.key_vault_url = key_vault_url or os.getenv("KEYVAULT_URL")
        
        if not self.key_vault_url:
            raise ValueError(
                "Key Vault URL not provided. Set KEYVAULT_URL environment variable "
                "or pass key_vault_url parameter"
            )

        # Ensure URL ends with /
        if not self.key_vault_url.endswith("/"):
            self.key_vault_url += "/"

        # Initialize credential
        try:
            if use_service_principal:
                if not all([sp_client_id, sp_client_secret, sp_tenant_id]):
                    raise ValueError(
                        "Service Principal credentials incomplete. "
                        "Provide client_id, client_secret, and tenant_id"
                    )
                credential = ClientSecretCredential(
                    tenant_id=sp_tenant_id,
                    client_id=sp_client_id,
                    client_secret=sp_client_secret
                )
                logger.info(f"Using Service Principal: {sp_client_id}")
            else:
                credential = DefaultAzureCredential()
                logger.info("Using DefaultAzureCredential")

            self.client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            self._test_connection()
            logger.info(f"✓ Successfully connected to Key Vault: {self.key_vault_url}")

        except Exception as e:
            logger.error(f"✗ Failed to initialize Key Vault: {str(e)}")
            raise

    def _test_connection(self) -> None:
        """Test connection to Key Vault"""
        try:
            self.client.list_properties_of_secrets(max_page_size=1)
            logger.debug("✓ Key Vault connection test passed")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Key Vault: {str(e)}")

    def _create_secret_name(self, db_name: str) -> str:
        """
        Create a safe secret name for Key Vault
        Key Vault names must be alphanumeric and hyphens only
        """
        safe_name = db_name.replace("_", "-").replace(".", "-").lower()
        # Key Vault secret names must be 1-127 characters
        if len(safe_name) > 127:
            safe_name = safe_name[:127]
        return safe_name

    def save_credentials(self, db_name: str, config: Dict) -> Tuple[bool, str]:
        """
        Save database credentials to Azure Key Vault

        Args:
            db_name: Database configuration name
            config: Dictionary containing database configuration
                   Required: db_type, host, port, database, username, password
                   Optional: filepath (for SQLite)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate config
            if not config.get("password"):
                return False, "Password is required"

            # Create secret payload
            secret_data = {
                "db_type": config.get("db_type"),
                "host": config.get("host"),
                "port": config.get("port"),
                "database": config.get("database"),
                "username": config.get("username"),
                "filepath": config.get("filepath"),
                "saved_at": datetime.utcnow().isoformat(),
                "product": "VeriQuery"
            }

            # Store password separately in secret value
            secret_name = self._create_secret_name(db_name)
            secret_value = json.dumps({
                "password": config.get("password"),
                "config": secret_data
            })

            # Save to Key Vault
            self.client.set_secret(name=secret_name, value=secret_value)

            logger.info(f"✓ Credentials saved for database: {db_name}")
            return True, f"Credentials successfully saved to Key Vault for '{db_name}'"

        except Exception as e:
            error_msg = f"Failed to save credentials: {str(e)}"
            logger.error(f"✗ {error_msg}")
            return False, error_msg

    def get_credentials(self, db_name: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Retrieve database credentials from Azure Key Vault

        Args:
            db_name: Database configuration name

        Returns:
            Tuple[Optional[Dict], Optional[str]]: (credentials_dict, error_message)
                If successful: (credentials_dict, None)
                If failed: (None, error_message)
        """
        try:
            secret_name = self._create_secret_name(db_name)
            secret = self.client.get_secret(name=secret_name)
            
            if not secret:
                return None, f"No credentials found for database: {db_name}"

            # Parse secret value
            secret_data = json.loads(secret.value)
            credentials = {
                "password": secret_data.get("password"),
                **secret_data.get("config", {})
            }

            logger.info(f"✓ Credentials retrieved for database: {db_name}")
            return credentials, None

        except Exception as e:
            error_msg = f"Failed to retrieve credentials for '{db_name}': {str(e)}"
            logger.error(f"✗ {error_msg}")
            return None, error_msg

    def delete_credentials(self, db_name: str) -> Tuple[bool, str]:
        """
        Delete database credentials from Azure Key Vault

        Args:
            db_name: Database configuration name

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            secret_name = self._create_secret_name(db_name)
            
            # Begin deletion (may not be immediate if soft-delete enabled)
            self.client.begin_delete_secret(name=secret_name).result()

            logger.info(f"✓ Credentials deleted for database: {db_name}")
            return True, f"Credentials successfully deleted for '{db_name}'"

        except Exception as e:
            error_msg = f"Failed to delete credentials for '{db_name}': {str(e)}"
            logger.error(f"✗ {error_msg}")
            return False, error_msg

    def list_credentials(self) -> Tuple[list, Optional[str]]:
        """
        List all stored credential names (without values)

        Returns:
            Tuple[list, Optional[str]]: (list_of_names, error_message)
        """
        try:
            properties = self.client.list_properties_of_secrets()
            names = [prop.name for prop in properties]
            logger.info(f"✓ Listed {len(names)} stored credentials")
            return names, None

        except Exception as e:
            error_msg = f"Failed to list credentials: {str(e)}"
            logger.error(f"✗ {error_msg}")
            return [], error_msg

    def credential_exists(self, db_name: str) -> bool:
        """
        Check if credentials exist for a database

        Args:
            db_name: Database configuration name

        Returns:
            bool: True if credentials exist, False otherwise
        """
        try:
            secret_name = self._create_secret_name(db_name)
            self.client.get_secret(name=secret_name)
            return True
        except Exception:
            return False

    def update_credentials(self, db_name: str, config: Dict) -> Tuple[bool, str]:
        """
        Update existing database credentials

        Args:
            db_name: Database configuration name
            config: Updated configuration dictionary

        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Delete old credentials and save new ones
        delete_success, delete_msg = self.delete_credentials(db_name)
        if not delete_success:
            return False, f"Failed to update: {delete_msg}"

        return self.save_credentials(db_name, config)

    def get_secret_metadata(self, db_name: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get metadata about stored credentials (saved_at, version, etc.)
        without retrieving the actual password

        Args:
            db_name: Database configuration name

        Returns:
            Tuple[Optional[Dict], Optional[str]]: (metadata_dict, error_message)
        """
        try:
            secret_name = self._create_secret_name(db_name)
            secret = self.client.get_secret(name=secret_name)
            secret_data = json.loads(secret.value)
            config = secret_data.get("config", {})

            metadata = {
                "db_name": db_name,
                "db_type": config.get("db_type"),
                "host": config.get("host"),
                "database": config.get("database"),
                "saved_at": config.get("saved_at"),
                "product": config.get("product"),
                "version_id": secret.properties.version
            }

            return metadata, None

        except Exception as e:
            error_msg = f"Failed to retrieve metadata for '{db_name}': {str(e)}"
            logger.error(f"✗ {error_msg}")
            return None, error_msg
