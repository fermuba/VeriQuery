#!/usr/bin/env python
import sys
sys.path.insert(0, 'tools')
sys.path.insert(0, 'src/backend')

from secure_credential_store import SecureCredentialStore
from bd_config_manager import BDConfigManager

print("=" * 60)
print("SUPABASE CREDENTIALS DIAGNOSTIC")
print("=" * 60)

# 1. Check local config
print("\n1. LOCAL CONFIG (databases.json):")
mgr = BDConfigManager()
config = mgr.get_database('supabase_prod')
if config:
    print(f"   ✓ Found in local config")
    print(f"     - Host: {config.host}")
    print(f"     - Username: {config.username}")
    print(f"     - Password: {'SET' if config.password else 'NULL'}")
    print(f"     - Database: {config.database}")
else:
    print("   ✗ Not found in local config")

# 2. Check Key Vault
print("\n2. AZURE KEY VAULT:")
try:
    store = SecureCredentialStore()
    creds, error = store.get_credentials('supabase_prod')
    if creds and not error:
        print(f"   ✓ Found in Key Vault")
        print(f"     - Host: {creds.get('host')}")
        print(f"     - Username: {creds.get('username')}")
        print(f"     - Password: {'SET' if creds.get('password') else 'NULL'}")
        print(f"     - Database: {creds.get('database')}")
    else:
        print(f"   ✗ Not found: {error}")
except Exception as e:
    print(f"   ✗ Error accessing Key Vault: {e}")

print("\n" + "=" * 60)
