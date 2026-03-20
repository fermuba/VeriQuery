param(
    [string]$VaultName = "guardian-vault-2026"
)

Write-Host "Verificando autenticacion en Azure..." -ForegroundColor Cyan

$accountInfo = az account show 2>$null
if (-not $accountInfo) {
    Write-Host "ERROR: No estas autenticado en Azure" -ForegroundColor Red
    Write-Host "Ejecuta: az login" -ForegroundColor Yellow
    exit 1
}

$account = $accountInfo | ConvertFrom-Json
Write-Host "✓ Autenticado como: $($account.user.name)" -ForegroundColor Green
Write-Host "✓ Suscripción: $($account.name)" -ForegroundColor Green
Write-Host ""

# PASO 2: Obtener información del Key Vault
Write-Host "🔑 Obteniendo información del Key Vault..." -ForegroundColor Cyan

$vaultName = "guardian-vault-2026"
$vaultInfo = az keyvault show --name $vaultName 2>$null | ConvertFrom-Json

if (-not $vaultInfo) {
    Write-Host "❌ No se encontró el Key Vault: $vaultName" -ForegroundColor Red
    Write-Host "Asegúrate de que existe y que tienes acceso." -ForegroundColor Yellow
    exit 1
}

$vaultUrl = $vaultInfo.properties.vaultUri
Write-Host "✓ Key Vault encontrado: $vaultName" -ForegroundColor Green
Write-Host "✓ Vault URI: $vaultUrl" -ForegroundColor Green
Write-Host ""

# PASO 3: Verificar acceso al Key Vault
Write-Host "🔐 Verificando permisos en Key Vault..." -ForegroundColor Cyan

$secrets = az keyvault secret list --vault-name $vaultName 2>$null | ConvertFrom-Json

if (-not $secrets) {
    Write-Host "⚠️  No tienes permisos de lectura en el Key Vault" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Necesitas agregar el rol 'Key Vault Secrets Officer':" -ForegroundColor Yellow
    Write-Host "1. Ve a: Azure Portal > $vaultName > Access Control (IAM)" -ForegroundColor Yellow
    Write-Host "2. Click: Add Role Assignment" -ForegroundColor Yellow
    Write-Host "3. Role: Key Vault Secrets Officer" -ForegroundColor Yellow
    Write-Host "4. Select: Tu usuario" -ForegroundColor Yellow
    Write-Host "5. Save" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Después, vuelve a ejecutar este script." -ForegroundColor Yellow
} else {
    Write-Host "✓ Tienes acceso al Key Vault" -ForegroundColor Green
    Write-Host "✓ Secretos guardados: $(($secrets | Measure-Object).Count)" -ForegroundColor Green
}

Write-Host ""

# PASO 4: Generar contenido del .env
Write-Host "📝 Generando contenido para .env" -ForegroundColor Cyan
Write-Host ""

$envContent = @"
# ========================================
# Forensic Data Guardian - Environment Variables
# ========================================

# AZURE KEY VAULT CONFIGURATION
# ========================================

# ✅ VALOR OBTENIDO AUTOMÁTICAMENTE
KEYVAULT_URL=$vaultUrl

# ℹ️  OPCIONAL: Solo si DefaultAzureCredential no funciona
# (Para desarrollo local, usar: az login)
AZURE_KEYVAULT_SP_CLIENT_ID=
AZURE_KEYVAULT_SP_CLIENT_SECRET=
AZURE_KEYVAULT_SP_TENANT_ID=


# AZURE OPENAI CONFIGURATION
# ========================================

AZURE_OPENAI_ENDPOINT=https://<your-resource>.services.ai.azure.com/
AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI=gpt-4o-mini-deployment
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# DATABASE CONFIGURATION
# ========================================

ACTIVE_DATABASE=ContosoV210k
DATABASE_DIR=./databases


# API CONFIGURATION
# ========================================

API_HOST=0.0.0.0
API_PORT=8888
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
API_TIMEOUT=30


# LOGGING
# ========================================

LOG_LEVEL=INFO
LOG_FILE=./logs/backend.log
ERROR_LOG_FILE=./logs/backend_err.log
DEBUG_SQL=false


# SECURITY
# ========================================

JWT_SECRET=your-super-secret-key-change-this
JWT_EXPIRATION_HOURS=24
HTTPS_ONLY=false


# DEVELOPMENT
# ========================================

DEBUG=false
RELOAD=true
INCLUDE_TEST_ENDPOINTS=false
"@

# PASO 5: Mostrar y guardar el contenido
Write-Host "📋 Contenido para .env.local:" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host $envContent -ForegroundColor White
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# PASO 6: Opción para guardar
Write-Host "💾 ¿Quieres guardar esto en .env.local?" -ForegroundColor Cyan
$saveChoice = Read-Host "  [S]í / [N]o (default: S)"

if ($saveChoice -ne "N") {
    $envContent | Out-File -FilePath ".env.local" -Encoding UTF8
    Write-Host "✓ Guardado en: .env.local" -ForegroundColor Green
    Write-Host ""
    Write-Host "ℹ️  .env.local está en .gitignore (no se subirá a Git)" -ForegroundColor Cyan
}

Write-Host ""

# PASO 7: Instrucciones siguientes
Write-Host "📖 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "1. ✓ Key Vault configurado" -ForegroundColor Green
Write-Host "2. ⏳ Asegúrate de que .env.local tiene KEYVAULT_URL" -ForegroundColor Cyan
Write-Host "3. ⏳ Ejecuta: az login (si no usas Service Principal)" -ForegroundColor Cyan
Write-Host "4. ⏳ Inicia la API: python -m uvicorn src.backend.api.main:app" -ForegroundColor Cyan
Write-Host "5. ⏳ Prueba: POST http://localhost:8888/api/databases/keyvault/status" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

# PASO 8: Verificar conexión
Write-Host "🧪 ¿Quieres verificar que funciona?" -ForegroundColor Cyan
$testChoice = Read-Host "  [S]í / [N]o (default: N)"

if ($testChoice -eq "S") {
    Write-Host ""
    Write-Host "Ejecuta esto en Python:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host 'python -c "' -NoNewline
    Write-Host 'import os; os.environ[' -NoNewline
    Write-Host "'" -NoNewline
    Write-Host 'KEYVAULT_URL' -NoNewline
    Write-Host "']='" -NoNewline
    Write-Host "$vaultUrl" -NoNewline
    Write-Host "'; from tools.secure_credential_store import SecureCredentialStore; store = SecureCredentialStore(); print(" -NoNewline
    Write-Host "'" -NoNewline
    Write-Host '✓ Key Vault conectado' -NoNewline
    Write-Host "'" -NoNewline
    Write-Host ')"' -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "✅ Configuración completada" -ForegroundColor Green
