#!/usr/bin/env python3
"""
Load .env file and run auth tests.
"""

import os
import sys
from pathlib import Path

# Load .env file from parent directory
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes if present
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

# Now run the tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

print("\n" + "="*70)
print("🧪 ForensicGuardian Authentication System - Test Suite")
print("="*70 + "\n")

# ============================================================
# Test 1: Import modules
# ============================================================
print("📦 Test 1: Importing modules...")
try:
    from auth.config import auth_config
    from auth.schemas import User, TokenData
    from auth.jwks_client import JWKSClient
    from auth.auth_handler import auth_handler
    from auth.user_repository import UserRepository
    print("✅ All modules imported successfully\n")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    sys.exit(1)

# ============================================================
# Test 2: Config validation
# ============================================================
print("⚙️  Test 2: Validating configuration...")
try:
    auth_config.validate()
    print(f"✅ Configuration valid")
    print(f"   - Client ID: {auth_config.CLIENT_ID[:30]}...")
    print(f"   - Tenant ID: {auth_config.TENANT_ID[:30]}...")
    print(f"   - Tenant mode: {'multi-tenant ⚠️' if auth_config.ALLOW_MULTI_TENANT else 'single-tenant ✅'}\n")
except Exception as e:
    print(f"❌ Config validation failed: {e}\n")
    sys.exit(1)

# ============================================================
# Test 3: JWKS Client
# ============================================================
print("🔑 Test 3: JWKS Client...")
try:
    client = JWKSClient()
    print(f"✅ JWKS Client created")
    print(f"   - Cache TTL: {client.cache.ttl_seconds} seconds")
    print(f"   - JWKS URL: {client.jwks_url}\n")
except Exception as e:
    print(f"❌ JWKS Client creation failed: {e}\n")
    sys.exit(1)

# ============================================================
# Test 4: TokenData schema
# ============================================================
print("📊 Test 4: TokenData schema...")
try:
    from datetime import datetime
    token_data = TokenData(
        iss=auth_config.ISSUER,
        aud=auth_config.CLIENT_ID,
        exp=int(datetime.utcnow().timestamp()) + 3600,
        iat=int(datetime.utcnow().timestamp()),
        nbf=int(datetime.utcnow().timestamp()),
        oid="test-oid",
        email="test@example.com",
        name="Test User",
        tid=auth_config.TENANT_ID,
    )
    print(f"✅ TokenData schema valid")
    print(f"   - Email: {token_data.email}")
    print(f"   - OID: {token_data.oid}\n")
except Exception as e:
    print(f"❌ TokenData schema failed: {e}\n")
    sys.exit(1)

# ============================================================
# Test 5: User schema
# ============================================================
print("👤 Test 5: User schema...")
try:
    user = User(
        id="test-user-id",
        email="user@example.com",
        name="Test User",
        role="analyst",
    )
    print(f"✅ User schema valid")
    print(f"   - ID: {user.id}")
    print(f"   - Email: {user.email}")
    print(f"   - Role: {user.role}\n")
except Exception as e:
    print(f"❌ User schema failed: {e}\n")
    sys.exit(1)

# ============================================================
# Test 6: Tenant validation
# ============================================================
print("🔐 Test 6: Tenant validation...")
try:
    token_data_same_tenant = TokenData(
        iss=auth_config.ISSUER,
        aud=auth_config.CLIENT_ID,
        exp=int(datetime.utcnow().timestamp()) + 3600,
        iat=int(datetime.utcnow().timestamp()),
        nbf=int(datetime.utcnow().timestamp()),
        tid=auth_config.TENANT_ID,  # Same as configured
    )
    
    is_valid, error = auth_handler.validate_tenant(token_data_same_tenant)
    
    if is_valid:
        print(f"✅ Tenant validation passed (same tenant)")
    else:
        print(f"❌ Tenant validation failed: {error}")
        sys.exit(1)
    
    # Test different tenant (should fail if not multi-tenant)
    if not auth_config.ALLOW_MULTI_TENANT:
        token_data_diff_tenant = TokenData(
            iss=auth_config.ISSUER,
            aud=auth_config.CLIENT_ID,
            exp=int(datetime.utcnow().timestamp()) + 3600,
            iat=int(datetime.utcnow().timestamp()),
            nbf=int(datetime.utcnow().timestamp()),
            tid="different-tenant-id",
        )
        
        is_valid, error = auth_handler.validate_tenant(token_data_diff_tenant)
        
        if not is_valid:
            print(f"✅ Tenant validation correctly rejected different tenant")
            print(f"   - Error: {error[:60]}...\n")
        else:
            print(f"❌ Tenant validation should have rejected different tenant\n")
            sys.exit(1)
    else:
        print(f"⚠️  Multi-tenant mode enabled - skipping rejection test\n")
        
except Exception as e:
    print(f"❌ Tenant validation test failed: {e}\n")
    sys.exit(1)

# ============================================================
# Summary
# ============================================================
print("="*70)
print("✅ ALL TESTS PASSED")
print("="*70)
print(f"""
Your authentication system is ready!

Next steps:
1. Start the API:
   python start_auth_api.py

2. Get a token from Azure AD (manually or via your frontend)

3. Test a protected endpoint:
   curl -H "Authorization: Bearer YOUR_TOKEN" \\
        http://localhost:8000/api/profile

4. View API docs:
   http://localhost:8000/docs
""")
print("="*70 + "\n")
