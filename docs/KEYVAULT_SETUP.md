"""
Azure Key Vault Configuration Guide for VeriQuery

This file documents how to set up Azure Key Vault integration for secure
credential storage.

SETUP INSTRUCTIONS:
===================

1. CREATE AZURE KEY VAULT (if not already created)
   - Go to Azure Portal: https://portal.azure.com
   - Create a new "Key Vault" resource
   - Choose a name (e.g., forensic-guardian-kv)
   - Region: Same as your app deployment
   - Note your Key Vault URL: https://{vault-name}.vault.azure.net/

2. AUTHENTICATION OPTIONS

   Option A: DefaultAzureCredential (Recommended for Local Development)
   ====================================================================
   Prerequisites:
   - Azure CLI installed: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
   - PowerShell or bash terminal
   
   Steps:
   a) Install Azure CLI
   b) Run: az login
   c) Select subscription if multiple: az account set --subscription <id>
   d) Grant yourself Key Vault permissions:
      - Go to Azure Portal > Key Vault > Access Control (IAM)
      - Add Role Assignment > "Key Vault Secrets Officer"
      - Select your user account
   e) Set environment variable in your terminal:
      - Windows (PowerShell): $env:KEYVAULT_URL="https://your-vault.vault.azure.net/"
      - Linux/Mac: export KEYVAULT_URL="https://your-vault.vault.azure.net/"

   Option B: Service Principal (Recommended for Production)
   =========================================================
   Prerequisites:
   - Azure App Registration created
   - Service Principal credentials available
   
   Steps:
   a) Create App Registration in Azure Portal:
      - Azure Portal > Azure Active Directory > App registrations > New registration
      - Name: ForensicGuardianAPI
      - Account type: Single tenant
      - Note: Application (client) ID
      - Note: Directory (tenant) ID
   
   b) Create Client Secret:
      - In App registration > Certificates & secrets > New client secret
      - Description: ForensicGuardianSecret
      - Expires: As per your policy
      - Note: Client secret value (only shown once!)
   
   c) Grant Key Vault Permissions:
      - Azure Portal > Key Vault > Access Control (IAM)
      - Add Role Assignment > "Key Vault Secrets Officer"
      - Select the app registration
   
   d) Set environment variables:
      - KEYVAULT_URL="https://your-vault.vault.azure.net/"
      - AZURE_KEYVAULT_SP_CLIENT_ID="your-client-id"
      - AZURE_KEYVAULT_SP_CLIENT_SECRET="your-client-secret"
      - AZURE_KEYVAULT_SP_TENANT_ID="your-tenant-id"


3. PYTHON CODE SETUP
   ==================

   Using DefaultAzureCredential (auto-detects credentials):
   ```python
   from tools.secure_credential_store import SecureCredentialStore
   
   cred_store = SecureCredentialStore()
   ```
   
   Using Service Principal explicitly:
   ```python
   from tools.secure_credential_store import SecureCredentialStore
   
   cred_store = SecureCredentialStore(
       key_vault_url="https://your-vault.vault.azure.net/",
       use_service_principal=True,
       sp_client_id="your-client-id",
       sp_client_secret="your-client-secret",
       sp_tenant_id="your-tenant-id"
   )
   ```


4. API ENDPOINTS AVAILABLE
   =======================

   Health Check:
   - GET /api/databases/keyvault/status
     Returns: Key Vault connection status

   Save Credentials:
   - POST /api/databases/save
     Request:
     {
       "name": "production_db",
       "db_type": "sqlserver",
       "host": "server.database.windows.net",
       "port": 1433,
       "database": "ContosoV210k",
       "username": "readonly_user",
       "password": "SecurePassword123!"
     }
     Response includes:
     - success: bool
     - stored_in_keyvault: bool
     - is_readonly: bool
     - warnings: list of security warnings if any

   Validate Credentials:
   - POST /api/databases/credentials/validate
     Same request format as /save
     Returns permission checks without saving

   List Stored Credentials:
   - GET /api/databases/credentials/list
     Returns: List of stored credential names

   Get Credential Metadata:
   - GET /api/databases/credentials/{database_name}/metadata
     Returns: Metadata (without password)

   Verify Credentials:
   - POST /api/databases/credentials/{database_name}/verify
     Tests stored credentials are still valid

   Delete Credentials:
   - DELETE /api/databases/credentials/{database_name}
     Removes credentials from Key Vault


5. PERMISSION VALIDATION
   =====================

   The system validates read-only access for:
   - PostgreSQL: Attempts to create temp table
   - SQL Server: Uses HAS_PERMS_BY_NAME function
   - MySQL: Checks SHOW GRANTS output
   - SQLite: Verifies file permissions

   Warnings are shown if write permissions are detected.


6. SECURITY BEST PRACTICES
   =======================

   ✓ DO:
   - Use read-only database users for all connections
   - Rotate service principal secrets regularly
   - Store credentials ONLY in Key Vault, never in files
   - Use separate credentials for dev/staging/production
   - Enable Key Vault logging for audit trails
   - Use network restrictions (Key Vault firewalls)

   ✗ DON'T:
   - Commit credentials to version control
   - Use admin/superuser accounts for read-only access
   - Disable Key Vault authentication checks
   - Reuse credentials across environments
   - Store unencrypted passwords


7. TROUBLESHOOTING
   ================

   Error: "Key Vault URL not provided"
   - Set KEYVAULT_URL environment variable
   - Verify Azure CLI is logged in: az account show

   Error: "Cannot connect to Key Vault"
   - Check Key Vault URL format (must end with /)
   - Verify credentials have Key Vault "Secrets Officer" role
   - Check network/firewall rules if using restrictions

   Error: "Secret not found"
   - Database name may be transformed (spaces/special chars become hyphens)
   - Verify credentials were saved: GET /api/databases/credentials/list

   Error: "Access denied"
   - Verify Azure CLI token: az account get-access-token
   - Re-authenticate: az login


8. ENVIRONMENT VARIABLES REFERENCE
   ===============================

   Required:
   - KEYVAULT_URL: https://your-vault.vault.azure.net/

   Optional (Service Principal):
   - AZURE_KEYVAULT_SP_CLIENT_ID
   - AZURE_KEYVAULT_SP_CLIENT_SECRET
   - AZURE_KEYVAULT_SP_TENANT_ID

   Optional (Logging):
   - AZURE_LOG_LEVEL: DEBUG|INFO|WARNING|ERROR (default: INFO)


9. EXAMPLE USAGE FLOW
   ==================

   # 1. Validate credentials before saving
   POST /api/databases/credentials/validate
   {
     "name": "prod_db",
     "db_type": "sqlserver",
     "host": "prod.database.windows.net",
     "port": 1433,
     "database": "MainDB",
     "username": "readonly_user",
     "password": "TempPassword123"
   }

   # 2. Check result - verify read-only is confirmed
   # If warnings shown, you're not using a read-only user

   # 3. Save to Key Vault
   POST /api/databases/save
   # Same request as validate

   # 4. Verify stored credentials work
   POST /api/databases/credentials/prod_db/verify

   # 5. Use application with secured credentials
   # Application retrieves from Key Vault as needed


10. PRODUCT INFORMATION
    ===================
    Product: VeriQuery
    Component: Secure Credential Store with Azure Key Vault
    Version: 1.0
    Last Updated: March 2026
"""
