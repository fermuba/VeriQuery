@echo off
REM ============================================================
REM ForensicGuardian Backend Startup Script
REM ============================================================

title ForensicGuardian Backend - Port 8000

echo.
echo ========================================================
echo  🚀 ForensicGuardian Backend - Starting
echo ========================================================
echo.

REM Crear venv si no existe
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activar venv
call .venv\Scripts\activate.bat

REM Instalar dependencias
echo 📥 Installing dependencies...
python -m pip install -q -r requirements.txt

REM Iniciar servidor
echo.
echo ✅ Backend initialized
echo.
echo 🔧 Starting FastAPI with Authentication...
echo 📡 Backend: http://localhost:8000
echo 📖 API Docs: http://localhost:8000/docs
echo 🏥 Health: http://localhost:8000/api/health
echo.
echo ⏹️  Press Ctrl+C to stop
echo.

python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8000 --reload

pause
