#!/usr/bin/env python
"""
Quick startup script for ForensicGuardian Backend with Authentication

Este script:
1. Activa el venv
2. Instala dependencias si es necesario
3. Inicia el servidor FastAPI en puerto 8000

Uso:
    python start_backend.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def activate_venv():
    """Activa el ambiente virtual"""
    venv_path = Path(".venv")
    
    if not venv_path.exists():
        print("📦 Creando ambiente virtual...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    
    if platform.system() == "Windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        if activate_script.exists():
            print("✅ Ambiente virtual activado (Windows)")
            return str(activate_script)
    else:
        activate_script = venv_path / "bin" / "activate"
        if activate_script.exists():
            print("✅ Ambiente virtual activado (Unix)")
            return str(activate_script)
    
    return None

def start_backend():
    """Inicia el servidor backend"""
    print("\n" + "="*70)
    print("🚀 ForensicGuardian Backend - Starting with Authentication")
    print("="*70 + "\n")
    
    # Verificar que requirements.txt existe
    if not Path("requirements.txt").exists():
        print("❌ Error: requirements.txt no encontrado")
        sys.exit(1)
    
    # Instalar dependencias
    print("📥 Instalando/actualizando dependencias...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], check=True)
    print("✅ Dependencias instaladas\n")
    
    # Iniciar servidor
    print("🔧 Iniciando FastAPI con Auth...")
    print("📡 Backend en: http://localhost:8000")
    print("📖 Docs en: http://localhost:8000/docs")
    print("🏥 Health check: http://localhost:8000/api/health")
    print("\n⏹️  Presiona Ctrl+C para detener\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "src.backend.api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n✅ Servidor detenido correctamente")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        activate_venv()
        start_backend()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
