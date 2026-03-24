@echo off
REM ============================================================
REM ForensicGuardian Frontend Startup Script
REM ============================================================

title ForensicGuardian Frontend - Port 5173

echo.
echo ========================================================
echo  🚀 ForensicGuardian Frontend - Starting
echo ========================================================
echo.

REM Instalar dependencias si es necesario
if not exist "node_modules" (
    echo 📥 Installing dependencies...
    call npm install
)

REM Iniciar servidor
echo.
echo ✅ Frontend initialized
echo.
echo 🔧 Starting Vite with MSAL Authentication...
echo 🌐 Frontend: http://localhost:5173
echo 🔐 Login: http://localhost:5173/login
echo 📊 Dashboard: http://localhost:5173/dashboard
echo.
echo ⏹️  Press Ctrl+C to stop
echo.

call npm run dev

pause
