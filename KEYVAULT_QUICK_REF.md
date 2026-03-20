# 🚀 Azure Key Vault - Quick Reference Card

## 5-Minute Setup

```bash
# 1. Create Azure Key Vault (if not exists)
# → Azure Portal > Create Resource > Key Vault
# → Name: forensic-guardian-kv
# → Region: Same as your app
# → Note: Vault URI from Overview page

# 2. Install Python packages
pip install azure-keyvault-secrets azure-identity

# 3. Set environment variable (PowerShell)
$env:KEYVAULT_URL="https://your-vault.vault.azure.net/"

# 4. Authenticate with Azure
az login

# 5. Test connection
python -c "
from tools.secure_credential_store import SecureCredentialStore
store = SecureCredentialStore()
print('✓ Key Vault connected')
"
```

## API Quick Reference

### Validate Credentials (Before Saving)
```bash
curl -X POST http://localhost:8888/api/databases/credentials/validate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_db",
    "db_type": "sqlserver",
    "host": "server.database.windows.net",
    "port": 1433,
    "database": "MyDB",
    "username": "readonly_user",
    "password": "YourPassword"
  }'
```
**Look for:** `is_readonly: true` in response

### Save to Key Vault
```bash
curl -X POST http://localhost:8888/api/databases/save \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_db",
    "db_type": "sqlserver",
    "host": "server.database.windows.net",
    "port": 1433,
    "database": "MyDB",
    "username": "readonly_user",
    "password": "YourPassword"
  }'
```
**Success:** `stored_in_keyvault: true`

### List Stored Credentials
```bash
curl http://localhost:8888/api/databases/credentials/list
```
**Returns:** `["my_db", "prod_db", "staging_db"]`

### Get Credential Info (Safe to Share)
```bash
curl http://localhost:8888/api/databases/credentials/my_db/metadata
```
**Returns:** Database type, host, name (NO password)

### Verify Credentials Work
```bash
curl -X POST http://localhost:8888/api/databases/credentials/my_db/verify
```
**Success:** `success: true`

### Delete Credentials
```bash
curl -X DELETE http://localhost:8888/api/databases/credentials/my_db
```
**Success:** `success: true`

### Check Key Vault Status
```bash
curl -X POST http://localhost:8888/api/databases/keyvault/status
```
**Success:** `enabled: true, status: "✓ Connected"`

## Python Usage

```python
from tools.secure_credential_store import SecureCredentialStore
from tools.permission_validator import PermissionValidator

# Initialize
cred_store = SecureCredentialStore()
permission_validator = PermissionValidator()

# Save credentials
config = {
    "db_type": "sqlserver",
    "host": "server.database.windows.net",
    "port": 1433,
    "database": "MyDB",
    "username": "readonly_user",
    "password": "SecurePass123"
}

success, message = cred_store.save_credentials("my_db", config)

# Get credentials
creds, error = cred_store.get_credentials("my_db")
if not error:
    print(f"Connected to {creds['database']} on {creds['host']}")

# List all
creds_list, _ = cred_store.list_credentials()
print(f"Stored: {', '.join(creds_list)}")

# Check if exists
exists = cred_store.credential_exists("my_db")

# Delete
success, msg = cred_store.delete_credentials("my_db")

# Get metadata (safe)
metadata, error = cred_store.get_secret_metadata("my_db")
```

## Common Database Setup

### SQL Server (Read-Only User)
```sql
-- Create read-only login
CREATE LOGIN [readonly_user] WITH PASSWORD = 'StrongPassword123!';

-- Create database user
CREATE USER [readonly_user] FOR LOGIN [readonly_user];

-- Grant read-only permissions
ALTER ROLE [db_datareader] ADD MEMBER [readonly_user];
```

### PostgreSQL (Read-Only User)
```sql
-- Create read-only user
CREATE USER readonly_user WITH PASSWORD 'StrongPassword123!';

-- Grant read access
GRANT CONNECT ON DATABASE mydb TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

### MySQL (Read-Only User)
```sql
-- Create read-only user
CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'StrongPassword123!';

-- Grant read access
GRANT SELECT ON mydb.* TO 'readonly_user'@'%';
FLUSH PRIVILEGES;
```

## Environment Variables

| Variable | Example | Required |
|----------|---------|----------|
| `KEYVAULT_URL` | `https://my-vault.vault.azure.net/` | ✅ Yes |
| `AZURE_KEYVAULT_SP_CLIENT_ID` | `12345678-...` | ❌ No* |
| `AZURE_KEYVAULT_SP_CLIENT_SECRET` | `abc123xyz...` | ❌ No* |
| `AZURE_KEYVAULT_SP_TENANT_ID` | `87654321-...` | ❌ No* |

*Only needed if DefaultAzureCredential doesn't work

## Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Operation completed |
| 400 | Bad request | Check JSON format |
| 401 | Not authenticated | Run `az login` |
| 403 | Forbidden | Check Key Vault permissions |
| 404 | Not found | Credential doesn't exist |
| 500 | Server error | Check logs |
| 503 | Key Vault unavailable | Check connection/URL |

## Permission Validation Output

### SQL Server Example
```json
{
  "checks": [
    {"name": "User Identity", "status": "✓ PASS"},
    {"name": "CREATE TABLE", "status": "✗ FAIL (Read-only)"},
    {"name": "INSERT Permission", "status": "✗ FAIL (Read-only)"},
    {"name": "SELECT Permission", "status": "✓ PASS"}
  ],
  "is_readonly": true
}
```

### PostgreSQL Example
```json
{
  "checks": [
    {"name": "List Tables", "status": "✓ PASS"},
    {"name": "Create Temporary Table", "status": "✓ PASS (Read-only)"},
    {"name": "User Identity", "status": "✓ PASS"}
  ],
  "is_readonly": true
}
```

## Troubleshooting Checklist

- [ ] KEYVAULT_URL set? `echo $env:KEYVAULT_URL` (PowerShell)
- [ ] Azure CLI installed? `az --version`
- [ ] Logged in? `az account show`
- [ ] Correct subscription? `az account set --subscription <id>`
- [ ] Key Vault exists? `az keyvault show --name your-vault`
- [ ] Have access? `az keyvault secret list --vault-name your-vault`
- [ ] User is "Secrets Officer"? Check Azure Portal > Key Vault > Access Control
- [ ] Dependencies installed? `pip list | grep azure`

## Where to Get Help

1. **Setup Issues:** `docs/KEYVAULT_SETUP.md`
2. **Full Guide:** `docs/AZURE_KEYVAULT_INTEGRATION.md`
3. **Code Examples:** `examples/example_keyvault_usage.py`
4. **Implementation Details:** `KEYVAULT_IMPLEMENTATION.md`

## Key Vault Limits

- Secret names: 1-127 characters (alphanumeric + hyphens)
- Max 25 secrets per vault by default
- Max secret size: 25 KB
- Free tier: 10K reads/month included

## Security Checklist

- [ ] Using read-only database users
- [ ] Permissions validated before saving
- [ ] Different credentials per environment
- [ ] Never commit credentials to Git
- [ ] KEYVAULT_URL only in docs, not secrets
- [ ] Service principal rotated every 90 days
- [ ] Key Vault logging enabled
- [ ] HTTPS_ONLY=true in production

---

**Forensic Data Guardian | Azure Key Vault v1.0**

For detailed info: See documentation files in `docs/`
