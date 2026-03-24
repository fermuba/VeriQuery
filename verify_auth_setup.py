#!/usr/bin/env python3
"""
Validation script to verify the authentication system is properly set up.
Run this to ensure all components are in place.

Usage:
    python verify_auth_setup.py
"""

import os
import sys
from pathlib import Path

# Add src/backend to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend"))


def check_file(path: str, description: str) -> bool:
    """Check if a file exists."""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}")
    return exists


def check_import(module_name: str, description: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}: {str(e)}")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("🔐 ForensicGuardian Authentication System - Verification")
    print("=" * 70 + "\n")
    
    # ============================================================
    # Check file structure
    # ============================================================
    print("📁 Checking file structure...")
    print("-" * 70)
    
    files_to_check = [
        ("src/backend/auth/__init__.py", "Auth module __init__"),
        ("src/backend/auth/config.py", "Configuration module"),
        ("src/backend/auth/schemas.py", "Pydantic schemas"),
        ("src/backend/auth/jwks_client.py", "JWKS client"),
        ("src/backend/auth/auth_handler.py", "Auth handler"),
        ("src/backend/auth/dependencies.py", "FastAPI dependencies"),
        ("src/backend/auth/models.py", "SQLAlchemy models"),
        ("src/backend/auth/user_repository.py", "User repository"),
        ("src/backend/auth/protected_routes.py", "Protected routes"),
        ("src/backend/auth/README.md", "Auth documentation"),
        ("tests/test_auth.py", "Auth tests"),
    ]
    
    files_ok = all(check_file(f, d) for f, d in files_to_check)
    
    # ============================================================
    # Check environment configuration
    # ============================================================
    print("\n⚙️  Checking environment configuration...")
    print("-" * 70)
    
    env_vars = [
        "AZURE_CLIENT_ID",
        "AZURE_TENANT_ID",
        "AZURE_ISSUER",
    ]
    
    env_ok = True
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} is NOT set (required for auth)")
            env_ok = False
    
    # ============================================================
    # Check imports
    # ============================================================
    print("\n🔌 Checking Python imports...")
    print("-" * 70)
    
    try:
        from auth.config import auth_config
        print("✅ auth.config imported")
    except Exception as e:
        print(f"❌ Failed to import auth.config: {str(e)}")
    
    try:
        from auth.schemas import User, TokenData
        print("✅ auth.schemas imported")
    except Exception as e:
        print(f"❌ Failed to import auth.schemas: {str(e)}")
    
    try:
        from auth.jwks_client import JWKSClient
        print("✅ auth.jwks_client imported")
    except Exception as e:
        print(f"❌ Failed to import auth.jwks_client: {str(e)}")
    
    try:
        from auth.auth_handler import auth_handler
        print("✅ auth.auth_handler imported")
    except Exception as e:
        print(f"❌ Failed to import auth.auth_handler: {str(e)}")
    
    try:
        from auth.dependencies import get_current_user, require_role
        print("✅ auth.dependencies imported")
    except Exception as e:
        print(f"❌ Failed to import auth.dependencies: {str(e)}")
    
    # ============================================================
    # Check external dependencies
    # ============================================================
    print("\n📦 Checking required packages...")
    print("-" * 70)
    
    packages = [
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("jwt", "PyJWT"),
        ("cryptography", "Cryptography"),
        ("httpx", "HTTPX"),
    ]
    
    all_packages_ok = True
    for package, name in packages:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_packages_ok = False
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    print(f"✅ File structure: {'OK' if files_ok else 'MISSING FILES'}")
    print(f"⚙️  Environment: {'OK' if env_ok else 'MISSING ENV VARS'}")
    print(f"📦 Packages: {'OK' if all_packages_ok else 'MISSING PACKAGES'}")
    
    # ============================================================
    # Next steps
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 NEXT STEPS")
    print("=" * 70)
    
    if not env_ok:
        print("""
1. Set up environment variables in .env:
   
   AZURE_CLIENT_ID="your-app-client-id"
   AZURE_TENANT_ID="your-tenant-id"
   AZURE_ISSUER="https://login.microsoftonline.com/your-tenant-id/v2.0"
   AZURE_AUDIENCE="your-app-client-id"
   
   See: AUTH_ENV_EXAMPLE.txt for full template
""")
    
    if not all_packages_ok:
        print("""
2. Install missing packages:
   
   pip install fastapi pydantic sqlalchemy pyjwt cryptography httpx
""")
    
    print("""
3. Review documentation:
   
   - AUTH_IMPLEMENTATION_COMPLETE.md (overview)
   - src/backend/auth/README.md (detailed guide)
   - src/backend/auth/FASTAPI_INTEGRATION.py (integration example)
   
4. Integrate with your FastAPI app:
   
   See: src/backend/auth/FASTAPI_INTEGRATION.py

5. Run tests:
   
   pytest tests/test_auth.py -v

6. Create database tables:
   
   from sqlalchemy import create_engine
   from auth.models import Base
   
   engine = create_engine("sqlite:///./guardian.db")
   Base.metadata.create_all(bind=engine)
""")
    
    print("=" * 70)
    
    # Return exit code
    if files_ok and all_packages_ok:
        print("\n✅ Setup looks good! Ready to integrate with FastAPI.\n")
        return 0
    else:
        print("\n⚠️  Please fix missing files or packages above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
