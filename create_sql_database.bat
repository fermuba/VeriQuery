@echo off
REM Script para crear SQL Database en Azure
REM Ejecutar como administrador

echo ============================================================
echo CREAR SQL DATABASE SERVERLESS EN AZURE
echo ============================================================

echo.
echo 1 - Iniciando sesion en Azure...
az login

echo.
echo 2 - Creando SQL Server...
az sql server create ^
  --name sql-forensic-southcentral ^
  --resource-group rg-danielahomobono81-1463 ^
  --location southcentralus ^
  --admin-user sqladmin ^
  --admin-password "Hackathon2026!Pass"

echo.
echo 3 - Configurando firewall para Azure Services...
az sql server firewall-rule create ^
  --resource-group rg-danielahomobono81-1463 ^
  --server sql-forensic-southcentral ^
  --name AllowAzureServices ^
  --start-ip-address 0.0.0.0 ^
  --end-ip-address 0.0.0.0

echo.
echo 4 - Obteniendo tu IP publica...
for /f %%i in ('powershell "(Invoke-WebRequest -Uri 'https://api.ipify.org').Content"') do set MI_IP=%%i
echo Tu IP: %MI_IP%

echo.
echo 5 - Permitiendo acceso desde tu IP local...
az sql server firewall-rule create ^
  --resource-group rg-danielahomobono81-1463 ^
  --server sql-forensic-southcentral ^
  --name AllowMyIP ^
  --start-ip-address %MI_IP% ^
  --end-ip-address %MI_IP%

echo.
echo 6 - Creando base de datos serverless...
az sql db create ^
  --resource-group rg-danielahomobono81-1463 ^
  --server sql-forensic-southcentral ^
  --name db-forensic-data ^
  --edition GeneralPurpose ^
  --compute-model Serverless ^
  --family Gen5 ^
  --capacity 1 ^
  --auto-pause-delay 60

echo.
echo ============================================================
echo SQL Database creada exitosamente
echo ============================================================
pause
