# Script para crear SQL Database en Azure
# Ejecutar con: .\create_sql_database.ps1

Write-Host "============================================================"
Write-Host "CREAR SQL DATABASE SERVERLESS EN AZURE"
Write-Host "============================================================"

# 1. Login a Azure
Write-Host "1 - Iniciando sesion en Azure..."
az login

# 2. Crear SQL Server
Write-Host "2 - Creando SQL Server..."
az sql server create `
  --name sql-forensic-southcentral `
  --resource-group rg-danielahomobono81-1463 `
  --location southcentralus `
  --admin-user sqladmin `
  --admin-password "Hackathon2026!Pass"

# 3. Configurar firewall (Azure Services)
Write-Host "3 - Configurando firewall para Azure Services..."
az sql server firewall-rule create `
  --resource-group rg-danielahomobono81-1463 `
  --server sql-forensic-southcentral `
  --name AllowAzureServices `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0

# 4. Obtener tu IP publica
Write-Host "4 - Obteniendo tu IP publica..."
$MI_IP = (Invoke-WebRequest -Uri "https://api.ipify.org").Content
Write-Host "Tu IP: $MI_IP"

# 5. Permitir tu IP local
Write-Host "5 - Permitiendo acceso desde tu IP local..."
az sql server firewall-rule create `
  --resource-group rg-danielahomobono81-1463 `
  --server sql-forensic-southcentral `
  --name AllowMyIP `
  --start-ip-address $MI_IP `
  --end-ip-address $MI_IP

# 6. Crear base de datos SERVERLESS
Write-Host "6 - Creando base de datos serverless..."
az sql db create `
  --resource-group rg-danielahomobono81-1463 `
  --server sql-forensic-southcentral `
  --name db-forensic-data `
  --edition GeneralPurpose `
  --compute-model Serverless `
  --family Gen5 `
  --capacity 1 `
  --auto-pause-delay 60

Write-Host "============================================================"
Write-Host "SQL Database creada exitosamente"
Write-Host "============================================================"
