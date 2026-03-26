#!/usr/bin/env python3
"""
Test authentication with a real Azure AD token.

Steps to get a token:
1. Using Azure CLI:
   az login
   az account get-access-token --resource 6aafe3c0-8461-4f73-95ac-c0715f50ee40

2. Using Graph Explorer:
   - Go to https://developer.microsoft.com/en-us/graph/graph-explorer
   - Sign in with your Azure AD account
   - Copy the access token from the "Access token" tab

3. Using PowerShell:
   Connect-MgGraph -Scopes @()
   (Get-MgContext).ContextScope
"""

import os
import sys
import asyncio
from pathlib import Path

# Load .env file from parent directory
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "backend"))

from auth.config import auth_config
from auth.auth_handler import auth_handler
from auth.user_repository import UserRepository
from auth.schemas import User
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from auth.models import Base, UserModel


async def test_with_token(token: str):
    """Test authentication with a real JWT token from Azure AD."""
    
    print("\n" + "="*70)
    print("🔐 Testing Real Azure AD Token")
    print("="*70 + "\n")
    
    # Setup database (in-memory SQLite for testing)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        user_repo = UserRepository(session)
        
        print("📋 Token validation steps:\n")
        
        # Step 1: Bearer token validation
        print("1️⃣  Validating bearer token format...")
        if not token.startswith("Bearer ") and not token.startswith("bearer "):
            token = f"Bearer {token}"
        print(f"   ✅ Token prepared: {token[:50]}...\n")
        
        # Step 2: Authenticate and provision
        print("2️⃣  Authenticating and provisioning user...")
        success, user, error_msg = await auth_handler.authenticate_and_provision_user(
            token=token.replace("Bearer ", "").replace("bearer ", ""),
            user_repository=user_repo,
        )
        
        if not success:
            print(f"   ❌ Authentication failed: {error_msg}\n")
            return False
        
        print(f"   ✅ User authenticated and provisioned:\n")
        print(f"      - ID: {user.id}")
        print(f"      - Email: {user.email}")
        print(f"      - Name: {user.name}")
        print(f"      - Role: {user.role}")
        print(f"      - Roles: {user.roles}")
        print(f"      - Azure OID: {user.azure_oid}")
        print(f"      - Tenant ID: {user.tenant_id}")
        print(f"      - Is Active: {user.is_active}")
        print(f"      - Login Count: {user.login_count}\n")
        
        # Step 3: Database verification
        print("3️⃣  Verifying user in database...")
        stored_user = await user_repo.get_by_email(user.email)
        if stored_user:
            print(f"   ✅ User stored in database\n")
        else:
            print(f"   ❌ User not found in database\n")
            return False
        
        # Step 4: Login again (should increment counter)
        print("4️⃣  Testing second login (should increment counter)...")
        success2, user2, error_msg2 = await auth_handler.authenticate_and_provision_user(
            token=token.replace("Bearer ", "").replace("bearer ", ""),
            user_repository=user_repo,
        )
        
        if success2 and user2.login_count == user.login_count + 1:
            print(f"   ✅ Login count incremented: {user.login_count} → {user2.login_count}\n")
        else:
            print(f"   ❌ Login counter not incremented\n")
            return False
        
        print("="*70)
        print("✅ ALL CHECKS PASSED - System ready for production!")
        print("="*70 + "\n")
        return True


def main():
    """Main entry point."""
    print("\n" + "🔑 Azure AD Token Tester".center(70))
    print("="*70)
    
    # Check for token in command line or environment
    token = None
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
    elif "AZURE_TEST_TOKEN" in os.environ:
        token = os.environ["AZURE_TEST_TOKEN"]
    
    if not token:
        print("\n⚠️  No token provided!\n")
        print("Usage:")
        print("  python test_with_real_token.py <YOUR_AZURE_AD_TOKEN>\n")
        print("Or set environment variable:")
        print("  $env:AZURE_TEST_TOKEN = 'your_token'\n")
        print("How to get a token:\n")
        print("Option 1 - Using Azure CLI:")
        print("  1. az login")
        print("  2. az account get-access-token --resource 6aafe3c0-8461-4f73-95ac-c0715f50ee40")
        print("  3. Copy the 'accessToken' value\n")
        print("Option 2 - Using Graph Explorer:")
        print("  1. Go to https://developer.microsoft.com/graph/graph-explorer")
        print("  2. Sign in with your Azure AD account")
        print("  3. Copy the access token from the top\n")
        print("Option 3 - Using PowerShell:")
        print("  Connect-MgGraph")
        print("  (Get-MgAccessToken)\n")
        return
    
    # Run the async test
    try:
        result = asyncio.run(test_with_token(token))
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
