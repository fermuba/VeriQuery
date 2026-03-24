#!/usr/bin/env python3
"""
Quick startup script for ForensicGuardian with Auth.

Run this to start the API with proper authentication.
"""

import subprocess
import sys
from pathlib import Path

# Colors for terminal
GREEN = '\033[92m'
BLUE = '\033[94m'
RED = '\033[91m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def check_requirements():
    """Check if all required packages are installed."""
    print_header("📦 Checking Requirements")
    
    required = [
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "pyjwt",
        "cryptography",
        "httpx",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"{GREEN}✅{RESET} {package}")
        except ImportError:
            print(f"{RED}❌{RESET} {package}")
            missing.append(package)
    
    if missing:
        print(f"\n{RED}Missing packages: {', '.join(missing)}{RESET}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print(f"\n{GREEN}✅ All requirements met{RESET}")
    return True

def check_env():
    """Check if .env has Azure AD config."""
    print_header("🔐 Checking Environment Configuration")
    
    env_file = Path(".env")
    if not env_file.exists():
        print(f"{RED}❌ .env file not found{RESET}")
        return False
    
    with open(env_file) as f:
        content = f.read()
    
    required_vars = [
        "AZURE_CLIENT_ID",
        "AZURE_TENANT_ID",
        "AZURE_ISSUER",
    ]
    
    all_set = True
    for var in required_vars:
        if var in content and not f'"{var}"' in content.split(var)[0][-5:]:
            print(f"{GREEN}✅{RESET} {var}")
        else:
            print(f"{RED}❌{RESET} {var} not configured")
            all_set = False
    
    return all_set

def start_server():
    """Start the FastAPI server."""
    print_header("🚀 Starting ForensicGuardian API")
    
    print(f"{BLUE}Starting uvicorn...{RESET}\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.backend.api.main_auth:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
        ])
    except KeyboardInterrupt:
        print(f"\n{BLUE}Server stopped{RESET}")
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return False
    
    return True

def main():
    """Main startup routine."""
    
    print(f"\n{GREEN}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║          ForensicGuardian API - Authentication Ready               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Check environment
    if not check_env():
        print(f"\n{RED}❌ Environment not properly configured{RESET}")
        print("Update .env with Azure AD credentials and try again")
        return 1
    
    # Start server
    start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
