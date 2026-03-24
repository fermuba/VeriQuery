#!/usr/bin/env powershell
"""
Quick startup script for ForensicGuardian Frontend with Authentication

Este script:
1. Instala dependencias si es necesario
2. Inicia el servidor Vite en puerto 5173

Uso:
    npm run dev
    o
    node start_frontend.js
"""

import os
import sys
import subprocess
from pathlib import Path

def start_frontend():
    """Inicia el servidor frontend"""
    print("\n" + "="*70)
    print("🚀 ForensicGuardian Frontend - Starting with MSAL Authentication")
    print("="*70 + "\n")
    
    # Verificar que package.json existe
    if not Path("package.json").exists():
        print("❌ Error: package.json no encontrado")
        print("   Asegúrate de estar en la carpeta 'frontend'")
        sys.exit(1)
    
    # Instalar dependencias si es necesario
    node_modules = Path("node_modules")
    if not node_modules.exists():
        print("📥 Instalando dependencias...")
        result = subprocess.run(["npm", "install"], cwd=".")
        if result.returncode != 0:
            print("❌ Error instalando dependencias")
            sys.exit(1)
        print("✅ Dependencias instaladas\n")
    
    # Iniciar servidor
    print("🔧 Iniciando Vite con MSAL...")
    print("🌐 Frontend en: http://localhost:5173")
    print("🔐 Login: http://localhost:5173/login")
    print("📊 App: http://localhost:5173/dashboard")
    print("\n⏹️  Presiona Ctrl+C para detener\n")
    
    try:
        subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido correctamente")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        start_frontend()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
