#!/usr/bin/env python3
"""
Quick validation of Azure AD configuration.
"""

import os
from pathlib import Path

print("\n" + "="*70)
print("🔐 ForensicGuardian - Azure AD Configuration Check")
print("="*70 + "\n")

# Load .env
env_file = Path(".env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"')

# Check Azure AD config
print("📋 Azure AD Configuration:")
print("-" * 70)

checks = {
    "AZURE_CLIENT_ID": "✅ Application (Client) ID",
    "AZURE_TENANT_ID": "✅ Directory (Tenant) ID",
    "AZURE_ISSUER": "✅ Token Issuer",
    "AZURE_AUDIENCE": "✅ Audience",
}

all_ok = True
for key, label in checks.items():
    value = os.getenv(key, "").strip('"')
    if value and value != "PASTE-YOUR":
        print(f"{label}: {value[:20]}...")
    else:
        print(f"❌ {key} NOT SET")
        all_ok = False

print("\n🔒 Tenant Validation:")
print("-" * 70)
allow_multi = os.getenv("ALLOW_MULTI_TENANT", "false").lower() in ("true", "1", "yes")
mode = "multi-tenant (⚠️  less secure)" if allow_multi else "single-tenant (✅ secure)"
print(f"Mode: {mode}")

print("\n" + "="*70)
if all_ok:
    print("✅ Configuration looks good!")
    print("\nNext steps:")
    print("1. Make sure you have a valid Azure AD token")
    print("2. Test with: curl -H 'Authorization: Bearer <TOKEN>' http://localhost:8000/api/v1/auth/me")
else:
    print("❌ Missing configuration. Please update .env file with Azure AD credentials.")
    print("\nRequired values:")
    print("  AZURE_CLIENT_ID = Your Application (Client) ID")
    print("  AZURE_TENANT_ID = Your Directory (Tenant) ID")
    print("  AZURE_ISSUER = https://login.microsoftonline.com/{TENANT_ID}/v2.0")
    print("  AZURE_AUDIENCE = Same as AZURE_CLIENT_ID")

print("="*70 + "\n")
