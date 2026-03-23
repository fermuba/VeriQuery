# Azure Key Vault Integration - VeriQuery

## 🔐 Overview

The VeriQuery API now includes secure credential storage using **Azure Key Vault**. This ensures that all database credentials are encrypted and managed centrally, rather than stored in plain text files.

### Key Features

- ✅ **Secure Credential Storage** - Credentials encrypted in Azure Key Vault
- ✅ **Read-Only Permission Validation** - Automatic detection of write permissions
- ✅ **Multi-Database Support** - PostgreSQL, SQL Server, MySQL, SQLite
- ✅ **Audit Trail** - Full logging of credential access
- ✅ **Zero-Trust Architecture** - No passwords stored locally
- ✅ **Flexible Authentication** - DefaultAzureCredential or Service Principal

## 📋 Quick Start

### 1. Environment Setup

```powershell
# Set your Azure Key Vault URL
$env:KEYVAULT_URL = "https://your-vault.vault.azure.net/"

# Authenticate with Azure
az login
```

### 2. Save Database Credentials

```bash
# HTTP Request
POST /api/databases/save
Content-Type: application/json

{
  "name": "production_db",
  "db_type": "sqlserver",
  "host": "server.database.windows.net",
  "port": 1433,
  "database": "ContosoV210k",
  "username": "readonly_user",
  "password": "YourSecurePassword"
}
```

**Response:**
```json
{
  "success": true,
  "message": "✓ Database 'production_db' configured successfully (credentials secured in Azure Key Vault)",
  "stored_in_keyvault": true,
  "is_readonly": true,
  "readonly_message": "✓ Read-only permissions confirmed",
  "permission_details": {
    "checks": [
      {
        "name": "User Identity",
        "status": "✓ PASS",
        "has_permission": true
      },
      {
        "name": "INSERT Permission",
        "status": "✗ FAIL (Read-only confirmed)",
        "has_permission": false
      }
    ]
  }
}
```

### 3. Verify Credentials

```bash
POST /api/databases/credentials/production_db/verify

Response:
{
  "success": true,
  "message": "✓ Test passed",
  "database_name": "production_db",
  "verified_at": "2026-03-20T14:30:00.000000"
}
```

## 🔧 API Endpoints

### Database Configuration

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/databases/save` | POST | Save database config with Key Vault integration |
| `/api/databases/test` | POST | Test connection without saving |
| `/api/databases` | GET | List all configured databases |
| `/api/databases/{name}` | GET | Get database details |
| `/api/databases/{name}` | DELETE | Delete configuration |
| `/api/databases/{name}/activate` | POST | Set as active database |

### Credential Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/databases/credentials/validate` | POST | Validate credentials & check permissions |
| `/api/databases/credentials/list` | GET | List all stored credentials |
| `/api/databases/credentials/{db}/metadata` | GET | Get credential metadata (no password) |
| `/api/databases/credentials/{db}/verify` | POST | Verify stored credentials still work |
| `/api/databases/credentials/{db}` | DELETE | Delete credentials from Key Vault |
| `/api/databases/keyvault/status` | POST | Check Key Vault connection status |

## 🛡️ Permission Validation

The system automatically validates database permissions:

### SQL Server
- Uses `HAS_PERMS_BY_NAME()` function
- Checks: CREATE TABLE, INSERT, SELECT permissions
- Confirms read-only access

### PostgreSQL
- Attempts to create temporary table
- Verifies user cannot create permanent tables
- Checks information_schema access

### MySQL
- Analyzes `SHOW GRANTS` output
- Detects INSERT, UPDATE, DELETE permissions
- Verifies temporary table creation restrictions

### SQLite
- Checks file system permissions
- Verifies database file is read-only
- Checks journal file permissions

## 📦 Technical Architecture

```
┌─────────────────┐
│   API Request   │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│ Database Management      │
│ Router                   │
└────────┬─────────────────┘
         │
    ┌────┴───────────────┐
    ▼                    ▼
┌─────────────────┐  ┌────────────────┐
│ Permission      │  │ Secure         │
│ Validator       │  │ Credential     │
│                 │  │ Store          │
│ - PostgreSQL    │  │                │
│ - SQL Server    │  │ Azure Key      │
│ - MySQL         │  │ Vault Client   │
│ - SQLite        │  └────────────────┘
└─────────────────┘
```

## 🔒 Security Best Practices

### ✅ DO

1. **Use Read-Only Database Users**
   ```sql
   -- SQL Server Example
   CREATE USER [readonly_user] FOR LOGIN [readonly_login];
   ALTER ROLE [db_datareader] ADD MEMBER [readonly_user];
   ```

2. **Enable Key Vault Logging**
   - Monitor all credential access
   - Track who and when credentials are retrieved

3. **Rotate Credentials Regularly**
   - Update passwords in Key Vault periodically
   - Use Key Vault versioning for rollback

4. **Use Separate Credentials per Environment**
   - dev_db, staging_db, prod_db (different passwords)
   - Different Azure subscriptions for prod

5. **Enable Key Vault Firewalls**
   - Restrict access by IP/VNET
   - Use managed identities in production

### ❌ DON'T

1. **Never Store Passwords in Files**
   - Even if encrypted locally
   - Key Vault is the single source of truth

2. **Never Commit Credentials to Git**
   - Use `.gitignore` for local config files
   - All creds must be in Key Vault

3. **Never Use Admin Accounts**
   - Always use least-privilege read-only users
   - Even for development/testing

4. **Never Share Credentials Directly**
   - Use Key Vault URL sharing instead
   - Let users authenticate with their own Azure identity

5. **Never Disable Security Checks**
   - Always validate read-only permissions
   - Fix permission issues, don't ignore warnings

## 🔑 Authentication Methods

### Method 1: DefaultAzureCredential (Recommended for Development)

```python
from secure_credential_store import SecureCredentialStore

# Automatically uses:
# 1. Environment variables (if AZURE_SUBSCRIPTION_ID set)
# 2. Azure CLI credentials (from az login)
# 3. Visual Studio credentials
# 4. Visual Studio Code credentials
# 5. PowerShell credentials
# 6. Managed identity (if running in Azure)

cred_store = SecureCredentialStore()
```

### Method 2: Service Principal (Recommended for Production)

```python
from secure_credential_store import SecureCredentialStore

cred_store = SecureCredentialStore(
    key_vault_url="https://your-vault.vault.azure.net/",
    use_service_principal=True,
    sp_client_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    sp_client_secret="your-secret-value",
    sp_tenant_id="yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
)
```

## 📊 Workflow Example

```
┌─ User wants to add SQL Server database
│
├─ POST /api/databases/credentials/validate
│  │
│  ├─ Test connection
│  ├─ Validate read-only permissions
│  └─ Return permission checks
│
├─ Review warnings (if any write permissions)
│
├─ POST /api/databases/save
│  │
│  ├─ Test connection again
│  ├─ Validate permissions again
│  ├─ Save to Azure Key Vault ✓
│  └─ Save config reference locally
│
└─ Application retrieves credentials from Key Vault on demand
   (Never stored in memory longer than needed)
```

## 🐛 Troubleshooting

### Error: "Key Vault URL not provided"
```powershell
# Solution: Set environment variable
$env:KEYVAULT_URL = "https://your-vault.vault.azure.net/"

# Verify
[Environment]::GetEnvironmentVariable("KEYVAULT_URL")
```

### Error: "Cannot connect to Key Vault"
```powershell
# Solution: Authenticate with Azure
az login

# Verify:
az account show

# Check Key Vault access
az keyvault secret list --vault-name your-vault
```

### Error: "Access Denied"
```
Solution: Add yourself to Key Vault access policies
1. Azure Portal > Key Vault > Access Control (IAM)
2. Add Role Assignment > "Key Vault Secrets Officer"
3. Select your user/app
4. Re-authenticate: az login
```

### Error: "Secret not found"
```
Solution: Verify credential name transformation
1. GET /api/databases/credentials/list
2. Check if your database name appears (spaces → hyphens)
3. Use exact name from the list
```

## 📈 Monitoring & Audit

### Enable Key Vault Diagnostics

```powershell
# In Azure Portal:
# 1. Key Vault > Diagnostic settings > + Add diagnostic setting
# 2. Enable: AuditEvent, AzurePolicyEvaluationDetails
# 3. Send to: Log Analytics, Storage Account, or Event Hub
```

### Query Audit Logs

```kusto
// Azure Monitor KQL
AzureDiagnostics
| where ResourceType == "VAULTS"
| where OperationName == "SecretGet"
| project TimeGenerated, OperationName, Identity, CallerIPAddress
```

## 🚀 Deployment

### Local Development
```bash
az login
export KEYVAULT_URL="https://your-vault.vault.azure.net/"
python -m uvicorn src.backend.api.main:app --reload
```

### Docker Container
```dockerfile
FROM python:3.13-slim

# Build args from secrets
ARG KEYVAULT_URL
ENV KEYVAULT_URL=$KEYVAULT_URL

# Container will use DefaultAzureCredential
# Mount Azure CLI credentials or use Managed Identity
```

### Azure App Service
```json
{
  "name": "forensic-guardian-api",
  "identity": {
    "type": "SystemAssigned"
  },
  "appSettings": [
    {
      "name": "KEYVAULT_URL",
      "value": "https://your-vault.vault.azure.net/"
    }
  ]
}
```

## 📝 License & Support

**Product:** VeriQuery
**Component:** Azure Key Vault Integration
**Version:** 1.0
**Last Updated:** March 2026

For support, see: [KEYVAULT_SETUP.md](../docs/KEYVAULT_SETUP.md)
