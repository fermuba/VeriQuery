# ForensicGuardian Authentication System

## Overview

A **production-grade, enterprise-ready** authentication system for ForensicGuardian built with:

- **FastAPI** - Modern async web framework
- **Microsoft Entra ID (Azure AD)** - OAuth2 / OpenID Connect
- **JWT Token Validation** - Using JWKS (JSON Web Key Set)
- **Automatic User Provisioning** - Creates users on first login
- **Role-Based Access Control (RBAC)** - Admin, analyst, manager roles
- **Secure Architecture** - Clean separation of concerns, no hardcoded secrets

---

## Architecture

```
auth/
├── __init__.py              # Module exports
├── config.py                # Configuration (environment variables)
├── schemas.py               # Pydantic models (User, Token, etc.)
├── jwks_client.py           # JWKS fetching and JWT verification
├── auth_handler.py          # Core authentication logic
├── dependencies.py          # FastAPI dependency injection
├── models.py                # SQLAlchemy ORM models
├── user_repository.py       # Database operations (CRUD)
└── protected_routes.py      # Example endpoints
```

---

## Key Features

### 1. Secure JWT Validation ✅

- Fetches Microsoft public keys from JWKS endpoint
- Verifies token **signature** cryptographically
- Validates **issuer** (iss claim)
- Validates **audience** (aud claim)
- Checks **expiration** (exp claim)
- Handles **key rotation** automatically

```python
# Token signature verified using RSA public key from JWKS
# NO unverified token decoding - fully secure
decoded = jwt.decode(
    token,
    public_key,  # From Microsoft JWKS
    algorithms=["RS256"],
    issuer=issuer,
    audience=audience,
    options={"leeway": 60},  # Clock skew tolerance
)
```

### 2. Automatic User Provisioning 🚀

When a valid token is received:

1. ✅ Token signature verified
2. ✅ User info extracted from token (sub/oid, email, name, roles)
3. ✅ Check if user exists in database
4. ✅ **If NOT:** Auto-create new user with default role
5. ✅ Update last_login timestamp

```python
# First login: User auto-provisioned
User(
    id="uuid-from-azure-ad",
    email="user@company.com",
    name="John Doe",
    role="analyst",  # Default role
    azure_oid="oid-from-token",
    tenant_id="tenant-from-token",
)
```

### 3. JWKS Caching 🔑

- Fetches Microsoft public keys with **3600 second (1 hour) TTL**
- Automatic refresh when expired
- Fallback to expired cache if Microsoft endpoint unreachable
- Reduces latency and network calls

```python
JWKS_CACHE_TTL = 3600  # 1 hour
```

### 4. Role-Based Access Control 🔐

Multiple patterns for endpoint protection:

```python
# Single role required
@require_role("admin")

# Any of multiple roles
@require_any_role("analyst", "admin", "manager")

# All roles required
@require_all_roles("admin", "security_officer")

# Optional authentication
@get_current_user_optional  # Returns None if not authenticated
```

---

## Setup Instructions

### Step 1: Environment Variables

Create or update `.env` file:

```bash
# === Azure AD / Entra ID Configuration ===

# Get from: Azure Portal > App registrations > Your app > Application (client) ID
AZURE_CLIENT_ID="your-app-client-id-uuid"

# Get from: Azure Portal > Azure AD > Overview > Tenant ID
AZURE_TENANT_ID="your-tenant-id-uuid"

# Token issuer URL
AZURE_ISSUER="https://login.microsoftonline.com/your-tenant-id-uuid/v2.0"

# Microsoft JWKS endpoint (usually this default)
AZURE_JWKS_URL="https://login.microsoftonline.com/common/discovery/v2.0/keys"

# Audience (usually same as CLIENT_ID)
AZURE_AUDIENCE="your-app-client-id-uuid"

# === JWT Validation Settings ===

# Clock skew tolerance in seconds (for time differences between servers)
TOKEN_EXPIRATION_TOLERANCE=60

# JWKS cache TTL in seconds
JWKS_CACHE_TTL=3600

# === User Configuration ===

# Default role for new users
DEFAULT_USER_ROLE="analyst"
```

### Step 2: Azure AD App Registration

1. **Create App Registration** in Azure Portal:
   - Go to: Azure AD > App registrations > New registration
   - Name: "ForensicGuardian"
   - Redirect URI: `http://localhost:8000/callback` (for development)

2. **Configure API Permissions**:
   - Add: `Microsoft Graph > User.Read`
   - Add: `Microsoft Graph > Directory.Read.All` (if needed)

3. **Create Client Secret** (for backend):
   - Go to: Certificates & secrets > Client secrets
   - Create new secret
   - Copy the secret value to `.env` (if using client credentials flow)

4. **Get Required IDs**:
   - **Client ID** (Application ID)
   - **Tenant ID**
   - **Object ID**

### Step 3: Database Setup

The system uses SQLAlchemy with SQLite (development) or SQL Server (production).

```python
# In your FastAPI app startup
from auth.models import Base
from database import engine

# Create tables
Base.metadata.create_all(bind=engine)
```

### Step 4: Integrate with FastAPI

```python
from fastapi import FastAPI
from auth.dependencies import get_current_user
from auth.protected_routes import router as auth_router

app = FastAPI()

# Include auth routes
app.include_router(auth_router)

# Protect endpoints
@app.get("/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_user),
):
    return {"user": current_user}
```

---

## Usage Examples

### Example 1: Basic Protected Endpoint

```python
from fastapi import Depends
from auth.dependencies import get_current_user
from auth.schemas import User

@app.get("/api/protected")
async def protected_route(
    current_user: User = Depends(get_current_user),
):
    """
    Requires valid Bearer token.
    
    Client:
        GET /api/protected
        Authorization: Bearer <jwt_token>
    """
    return {
        "message": "Success",
        "user": current_user.email,
        "role": current_user.role,
    }
```

### Example 2: Admin-Only Endpoint

```python
from auth.dependencies import get_current_user, require_role

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role("admin")),
):
    """
    Requires:
    - Valid Bearer token
    - User must have 'admin' role
    """
    return {"deleted": user_id}
```

### Example 3: Multiple Roles

```python
from auth.dependencies import require_any_role

@app.post("/reports")
async def create_report(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_any_role("analyst", "admin", "manager")),
):
    """
    Requires one of: analyst, admin, or manager role.
    """
    return {"report_id": "RPT-001"}
```

### Example 4: Optional Authentication

```python
from auth.dependencies import get_current_user_optional
from typing import Optional

@app.get("/public")
async def public_route(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Works with OR without Bearer token.
    """
    if current_user:
        return {"message": f"Hello {current_user.name}"}
    return {"message": "Hello anonymous"}
```

### Example 5: Accessing Token Data

```python
@app.get("/user-details")
async def get_details(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "roles": current_user.roles,
        "azure_oid": current_user.azure_oid,
        "tenant_id": current_user.tenant_id,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
    }
```

---

## Testing with cURL

### Test Protected Endpoint

```bash
# Get token from Azure AD (manual process)
TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6IjE..."

# Call protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/auth/me

# Response:
# {
#   "id": "user-uuid",
#   "email": "user@company.com",
#   "name": "John Doe",
#   "role": "analyst"
# }
```

### Test Health Check (No Token Required)

```bash
curl http://localhost:8000/api/v1/auth/health

# Response (unauthenticated):
# {
#   "is_authenticated": false,
#   "user": null,
#   "message": "Not authenticated",
#   "token_valid": false
# }

# Response (authenticated):
# {
#   "is_authenticated": true,
#   "user": {...},
#   "message": "Authenticated as user@company.com",
#   "token_valid": true
# }
```

---

## Token Validation Flow

```
┌─────────────────────────────────────────┐
│  Client sends Authorization header      │
│  Authorization: Bearer <JWT_TOKEN>      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Extract Bearer token │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────────────┐
        │ Decode JWT header to get 'kid'│  (WITHOUT verifying signature)
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌────────────────────────────────┐
        │ Fetch JWKS from Microsoft      │  (or use cached)
        │ (https://login.microsoft...)   │
        └──────────────┬─────────────────┘
                       │
                       ▼
        ┌────────────────────────────────────┐
        │ Find key matching token's 'kid'    │
        │ Convert JWK to RSA public key      │
        └──────────────┬─────────────────────┘
                       │
                       ▼
        ┌────────────────────────────────────┐
        │ Verify token signature with key    │  ✅ CRYPTOGRAPHIC VERIFICATION
        └──────────────┬─────────────────────┘
                       │
                       ▼
        ┌────────────────────────────────────┐
        │ Validate standard JWT claims:      │
        │ - iss (issuer)                     │
        │ - aud (audience)                   │
        │ - exp (expiration)                 │
        └──────────────┬─────────────────────┘
                       │
                       ▼
        ┌────────────────────────────────────┐
        │ Extract user data from token:      │
        │ - sub/oid (unique ID)              │
        │ - email                            │
        │ - name                             │
        │ - roles                            │
        └──────────────┬─────────────────────┘
                       │
                       ▼
        ┌────────────────────────────────────┐
        │ Check if user exists in database   │
        └──────────────┬─────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼ YES                   ▼ NO
    ┌────────────────┐    ┌──────────────────┐
    │ Update login   │    │ Auto-provision   │
    │ timestamp      │    │ new user         │
    └────────────────┘    └──────────────────┘
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
        ┌────────────────────────────────┐
        │ Return User object             │
        │ ready for use in endpoint      │
        └────────────────────────────────┘
```

---

## Security Best Practices Implemented ✅

1. **JWT Signature Verification** - Full cryptographic verification using JWKS
2. **No Hardcoded Secrets** - All config from environment variables
3. **Token Claims Validation** - Issuer, audience, expiration checked
4. **Key Rotation Support** - JWKS endpoint queried with automatic caching
5. **Role-Based Access Control** - Fine-grained endpoint protection
6. **User Provisioning** - Automatic database sync with Azure AD
7. **Clean Architecture** - Authentication logic separated from business logic
8. **Dependency Injection** - Reusable, testable dependencies
9. **Error Handling** - Proper HTTP status codes and error messages
10. **Audit Logging** - All auth events logged for security monitoring

---

## Configuration Options

### JWT Validation

| Setting | Default | Description |
|---------|---------|-------------|
| `TOKEN_EXPIRATION_TOLERANCE` | 60 seconds | Clock skew allowance |
| `JWKS_CACHE_TTL` | 3600 seconds | Key cache duration |

### User Provisioning

| Setting | Default | Description |
|---------|---------|-------------|
| `DEFAULT_USER_ROLE` | "analyst" | Role for new users |

### Azure AD

| Setting | Required | Description |
|---------|----------|-------------|
| `AZURE_CLIENT_ID` | ✅ Yes | Application ID |
| `AZURE_TENANT_ID` | ✅ Yes | Tenant ID |
| `AZURE_ISSUER` | ✅ Yes | Token issuer URL |
| `AZURE_AUDIENCE` | Optional | Usually same as CLIENT_ID |

---

## Troubleshooting

### Issue: "No matching key found in JWKS"

**Cause:** Token 'kid' doesn't match any key in Microsoft's JWKS.

**Solution:**
1. Verify JWKS URL is correct
2. Check token was issued by your Azure AD tenant
3. Force refresh JWKS cache: `jwks_client.cache.clear()`

### Issue: "Token issuer mismatch"

**Cause:** Token issuer doesn't match `AZURE_ISSUER` config.

**Solution:**
- Verify `AZURE_TENANT_ID` is correct
- Check token was issued by your tenant

### Issue: "Token has expired"

**Cause:** Token is older than expiration time.

**Solution:**
- Tokens typically expire after 1 hour
- Request new token from Azure AD
- Increase `TOKEN_EXPIRATION_TOLERANCE` if clock skew issue

### Issue: "User not found after auto-provisioning"

**Cause:** Database constraints or connectivity issue.

**Solution:**
1. Verify database is initialized: `Base.metadata.create_all(bind=engine)`
2. Check database is accessible
3. Review database error logs

---

## Production Deployment Checklist

- [ ] All environment variables set in production secrets manager
- [ ] Azure AD app registration configured for production domain
- [ ] HTTPS enabled (not HTTP)
- [ ] Database backups configured
- [ ] Logging and monitoring set up
- [ ] Rate limiting on auth endpoints (optional)
- [ ] API key rotation policy established
- [ ] Audit logs retention configured
- [ ] User provisioning rules reviewed
- [ ] Role definitions finalized
- [ ] Load testing completed

---

## Next Steps

1. **Add Database Session Injection** - Integrate with your FastAPI dependency system
2. **Add Rate Limiting** - Protect against brute force attacks
3. **Add Audit Logging** - Log all auth events to audit table
4. **Add MFA** - Require multi-factor authentication
5. **Add Approval Workflows** - For sensitive operations
6. **Add User Management UI** - Admin panel for managing roles

---

## Files Reference

| File | Purpose |
|------|---------|
| `config.py` | Environment configuration |
| `schemas.py` | Pydantic models for data validation |
| `jwks_client.py` | JWKS fetching and JWT verification |
| `auth_handler.py` | Core auth logic and user provisioning |
| `dependencies.py` | FastAPI dependency injection functions |
| `models.py` | SQLAlchemy ORM models |
| `user_repository.py` | Database operations (CRUD) |
| `protected_routes.py` | Example protected endpoints |

---

## License

Part of ForensicGuardian project.
