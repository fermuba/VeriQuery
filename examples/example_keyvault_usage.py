"""
Example Usage: Azure Key Vault Credential Management
VeriQuery - Secure Credential Store

This script demonstrates how to use the SecureCredentialStore
and PermissionValidator in your application.
"""

import asyncio
import sys
from pathlib import Path

# Add paths for imports
tools_path = str(Path(__file__).parent.parent.parent / "tools")
if tools_path not in sys.path:
    sys.path.insert(0, tools_path)

from secure_credential_store import SecureCredentialStore
from permission_validator import PermissionValidator
from database.multi_db_connector import MultiDatabaseConnector
from connection_manager import DatabaseConfig


async def example_1_basic_storage():
    """Example 1: Basic credential storage in Key Vault"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Credential Storage")
    print("="*70)

    try:
        # Initialize credential store
        cred_store = SecureCredentialStore()

        # Save credentials
        config = {
            "db_type": "sqlserver",
            "host": "myserver.database.windows.net",
            "port": 1433,
            "database": "ForensicDB",
            "username": "readonly_user",
            "password": "SecurePassword123!",
        }

        success, message = cred_store.save_credentials("forensic_prod", config)
        print(f"\nSave Result: {message}")

        if success:
            # Retrieve credentials
            creds, error = cred_store.get_credentials("forensic_prod")
            if error:
                print(f"Error retrieving: {error}")
            else:
                print(f"\nRetrieved Database Type: {creds.get('db_type')}")
                print(f"Retrieved Host: {creds.get('host')}")
                print(f"Retrieved Username: {creds.get('username')}")
                print("✓ Password successfully retrieved from Key Vault")

    except Exception as e:
        print(f"Error: {str(e)}")


async def example_2_permission_validation():
    """Example 2: Validate read-only permissions"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Permission Validation")
    print("="*70)

    try:
        db_connector = MultiDatabaseConnector()
        permission_validator = PermissionValidator()

        # Create config
        config = DatabaseConfig(
            name="test_db",
            db_type="sqlserver",
            host="myserver.database.windows.net",
            port=1433,
            database="TestDB",
            username="test_user",
            password="TestPassword123",
        )

        # Test connection
        print("\n1. Testing connection...")
        success, message = db_connector.test_connection(config)
        print(f"   Connection test: {message}")

        if success:
            # Get connection for validation
            conn = db_connector.get_connection(config)
            if conn:
                # Validate permissions
                print("\n2. Validating permissions...")
                is_readonly, readonly_message, details = permission_validator.validate_readonly_permissions(
                    "sqlserver", conn
                )

                print(f"   Read-only Status: {readonly_message}")
                print(f"   Is Read-Only: {is_readonly}")
                
                if details.get("checks"):
                    print("\n   Permission Checks:")
                    for check in details["checks"]:
                        print(f"   - {check.get('name')}: {check.get('status')}")

                db_connector.close_connection(conn)

    except Exception as e:
        print(f"Error: {str(e)}")


async def example_3_list_credentials():
    """Example 3: List stored credentials"""
    print("\n" + "="*70)
    print("EXAMPLE 3: List Stored Credentials")
    print("="*70)

    try:
        cred_store = SecureCredentialStore()

        credentials, error = cred_store.list_credentials()
        if error:
            print(f"Error: {error}")
        else:
            print(f"\nStored Credentials ({len(credentials)} total):")
            for cred in credentials:
                print(f"  - {cred}")

    except Exception as e:
        print(f"Error: {str(e)}")


async def example_4_credential_metadata():
    """Example 4: Get credential metadata without password"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Get Credential Metadata (Secure)")
    print("="*70)

    try:
        cred_store = SecureCredentialStore()

        metadata, error = cred_store.get_secret_metadata("forensic_prod")
        if error:
            print(f"Error: {error}")
        else:
            print("\nCredential Metadata (password NOT included):")
            for key, value in metadata.items():
                if key != "version_id":
                    print(f"  {key}: {value}")
                else:
                    print(f"  version: {value[:8]}...")  # Truncate version ID

    except Exception as e:
        print(f"Error: {str(e)}")


async def example_5_delete_credentials():
    """Example 5: Delete credentials from Key Vault"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Delete Credentials")
    print("="*70)

    try:
        cred_store = SecureCredentialStore()

        success, message = cred_store.delete_credentials("forensic_prod")
        print(f"\nDelete Result: {message}")

    except Exception as e:
        print(f"Error: {str(e)}")


async def example_6_update_credentials():
    """Example 6: Update existing credentials"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Update Credentials")
    print("="*70)

    try:
        cred_store = SecureCredentialStore()

        # Original config
        original_config = {
            "db_type": "sqlserver",
            "host": "myserver.database.windows.net",
            "port": 1433,
            "database": "ForensicDB",
            "username": "readonly_user",
            "password": "OriginalPassword123!",
        }

        print("\n1. Saving original credentials...")
        success, message = cred_store.save_credentials("forensic_prod", original_config)
        print(f"   {message}")

        # Updated config (e.g., password changed)
        updated_config = original_config.copy()
        updated_config["password"] = "NewPassword456!"

        print("\n2. Updating credentials...")
        success, message = cred_store.update_credentials("forensic_prod", updated_config)
        print(f"   {message}")

        print("\n3. Verifying update...")
        creds, error = cred_store.get_credentials("forensic_prod")
        if not error and creds.get("password") == "NewPassword456!":
            print("   ✓ Credentials successfully updated")
        else:
            print("   ✗ Update verification failed")

    except Exception as e:
        print(f"Error: {str(e)}")


async def example_7_credential_exists():
    """Example 7: Check if credentials exist"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Check Credential Existence")
    print("="*70)

    try:
        cred_store = SecureCredentialStore()

        exists = cred_store.credential_exists("forensic_prod")
        print(f"\nCredentials 'forensic_prod' exist: {exists}")

        exists_fake = cred_store.credential_exists("nonexistent_db")
        print(f"Credentials 'nonexistent_db' exist: {exists_fake}")

    except Exception as e:
        print(f"Error: {str(e)}")


async def main():
    """Run all examples"""
    print("\n" + "█"*70)
    print("█ VeriQuery - Azure Key Vault Integration Examples")
    print("█"*70)

    try:
        # Uncomment examples you want to run
        # await example_1_basic_storage()
        # await example_2_permission_validation()
        # await example_3_list_credentials()
        # await example_4_credential_metadata()
        # await example_5_delete_credentials()
        # await example_6_update_credentials()
        # await example_7_credential_exists()

        print("\n" + "="*70)
        print("NOTE: Examples are commented out by default.")
        print("Uncomment in main() to run specific examples.")
        print("="*70)

    except Exception as e:
        print(f"\n✗ Error running examples: {str(e)}")


if __name__ == "__main__":
    print("\nTo use these examples:")
    print("1. Set KEYVAULT_URL environment variable")
    print("2. Authenticate with Azure (az login)")
    print("3. Uncomment desired examples in main()")
    print("4. Run: python example_keyvault_usage.py")
    
    asyncio.run(main())
