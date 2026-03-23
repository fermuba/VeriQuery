# 🔐 Azure Key Vault - Configuración para VeriQuery

## ✅ Pasos para Configurar .env

### PASO 1: Autenticarse con Azure CLI

```powershell
# En PowerShell, ejecuta:
az logout
az login --tenant "f53e7656-1a12-45c1-88f3-8cc6366854cf"
```

Esto abrirá un navegador. Inicia sesión con tu cuenta Azure.

### PASO 2: Obtener la URL del Key Vault

```powershell
# Ejecuta esto en PowerShell:
az keyvault show --name guardian-vault-2026 | ConvertFrom-Json | Select-Object -ExpandProperty properties | Select-Object -ExpandProperty vaultUri
```

**Copiar el valor que devuelve (formato: `https://guardian-vault-2026.vault.azure.net/`)**

### PASO 3: Crear .env.local

Crea un archivo llamado `.env.local` en la raíz del proyecto con este contenido:

```env
# AZURE KEY VAULT CONFIGURATION
KEYVAULT_URL=https://guardian-vault-2026.vault.azure.net/

# OPCIONAL: Solo si DefaultAzureCredential no funciona
AZURE_KEYVAULT_SP_CLIENT_ID=
AZURE_KEYVAULT_SP_CLIENT_SECRET=
AZURE_KEYVAULT_SP_TENANT_ID=

# AZURE OPENAI (completa con tus valores)
AZURE_OPENAI_ENDPOINT=https://your-resource.services.ai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI=gpt-4o-mini-deployment
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# DATABASE
ACTIVE_DATABASE=ContosoV210k
DATABASE_DIR=./databases

# API
API_HOST=0.0.0.0
API_PORT=8888
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
API_TIMEOUT=30

# LOGGING
LOG_LEVEL=INFO
LOG_FILE=./logs/backend.log
ERROR_LOG_FILE=./logs/backend_err.log
DEBUG_SQL=false

# SECURITY
JWT_SECRET=change-this-to-random-string
JWT_EXPIRATION_HOURS=24
HTTPS_ONLY=false

# DEVELOPMENT
DEBUG=false
RELOAD=true
```

**⚠️ IMPORTANTE:**
- Reemplaza `KEYVAULT_URL` con la URL que obtuviste en PASO 2
- El archivo `.env.local` está en `.gitignore` (no se subirá a Git)
- Nunca hagas commit de credenciales

### PASO 4: Verificar que funciona

```bash
# En PowerShell
python -m uvicorn src.backend.api.main:app --reload
```

Luego prueba:

```bash
# En otra terminal
curl -X POST http://localhost:8888/api/databases/keyvault/status
```

Deberías recibir:
```json
{
  "enabled": true,
  "status": "✓ Connected",
  "vault_url": "https://guardian-vault-2026.vault.azure.net/"
}
```

---

## 📊 Variables por Sección

### 🔐 AZURE KEY VAULT (REQUERIDO)

| Variable | Valor | Dónde Obtenerlo |
|----------|-------|-----------------|
| `KEYVAULT_URL` | `https://guardian-vault-2026.vault.azure.net/` | Azure Portal > Key Vault > Overview > Vault URI |

### 🤖 AZURE OPENAI (PARA NL2SQL)

| Variable | Ejemplo | Dónde Obtenerlo |
|----------|---------|-----------------|
| `AZURE_OPENAI_ENDPOINT` | `https://your-resource.services.ai.azure.com/` | Azure Portal > AI Foundry > Deployment URI |
| `AZURE_OPENAI_API_KEY` | `abc123xyz...` | Azure Portal > AI Foundry > Keys |
| `AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI` | `gpt-4o-mini-deployment` | Nombre exacto de tu deployment |
| `AZURE_OPENAI_API_VERSION` | `2024-08-01-preview` | Usar valor por defecto |

### 🗄️ DATABASE

| Variable | Valor | Notas |
|----------|-------|-------|
| `ACTIVE_DATABASE` | `ContosoV210k` | Nombre de la config guardada |
| `DATABASE_DIR` | `./databases` | Directorio para configs locales |

### 🌐 API

| Variable | Valor | Notas |
|----------|-------|-------|
| `API_HOST` | `0.0.0.0` | Escuchar en todas las interfaces |
| `API_PORT` | `8888` | Puerto FastAPI |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | URLs permitidas (CORS) |
| `API_TIMEOUT` | `30` | Segundos |

### 📝 LOGGING

| Variable | Valor | Notas |
|----------|-------|-------|
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `LOG_FILE` | `./logs/backend.log` | Archivo de logs |
| `ERROR_LOG_FILE` | `./logs/backend_err.log` | Errores |
| `DEBUG_SQL` | `false` | Verbose SQL logging |

### 🔒 SECURITY

| Variable | Valor | Notas |
|----------|-------|-------|
| `JWT_SECRET` | `change-this-to-random-string` | Generar valor fuerte |
| `JWT_EXPIRATION_HOURS` | `24` | Horas hasta expiración |
| `HTTPS_ONLY` | `false` | true en producción |

### 💻 DEVELOPMENT

| Variable | Valor | Notas |
|----------|-------|-------|
| `DEBUG` | `false` | true solo en desarrollo |
| `RELOAD` | `true` | Auto-reload en cambios |

---

## 🚀 Checklist

- [ ] Autenticado con Azure (`az login`)
- [ ] Obtuviste URL del Key Vault
- [ ] Creaste `.env.local` con `KEYVAULT_URL`
- [ ] Verificaste que `.env.local` NO está en Git
- [ ] Completaste variables de OpenAI
- [ ] API inicia sin errores (`python -m uvicorn...`)
- [ ] Endpoint `/api/databases/keyvault/status` devuelve `✓ Connected`

---

## ❓ Troubleshooting

### Error: "invalid_grant" o "session is not valid"

```powershell
az logout
az login --tenant "f53e7656-1a12-45c1-88f3-8cc6366854cf"
```

### Error: "Key Vault URL not provided"

Asegúrate de:
1. `.env.local` existe en la raíz del proyecto
2. `KEYVAULT_URL=https://guardian-vault-2026.vault.azure.net/` está presente
3. El valor es exacto (con `/` al final)

### Error: "Cannot connect to Key Vault"

```powershell
# Verifica acceso:
az keyvault secret list --vault-name guardian-vault-2026
```

Si falla, necesitas el rol "Key Vault Secrets Officer":
1. Azure Portal > guardian-vault-2026 > Access Control (IAM)
2. Add Role Assignment > Key Vault Secrets Officer
3. Select your user > Save

### Error: "secret not found"

Las credenciales se guardan en Key Vault cuando llamas a:
```
POST /api/databases/save
```

### ¿Dónde está el archivo .env?

En la raíz del proyecto:
```
C:\Users\Daniela\Desktop\forensicGuardian\.env.local
```

---

## 📋 Template .env.local (Copiar y Pegar)

```env
KEYVAULT_URL=https://guardian-vault-2026.vault.azure.net/
AZURE_KEYVAULT_SP_CLIENT_ID=
AZURE_KEYVAULT_SP_CLIENT_SECRET=
AZURE_KEYVAULT_SP_TENANT_ID=
AZURE_OPENAI_ENDPOINT=https://your-resource.services.ai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI=gpt-4o-mini-deployment
AZURE_OPENAI_API_VERSION=2024-08-01-preview
ACTIVE_DATABASE=ContosoV210k
DATABASE_DIR=./databases
API_HOST=0.0.0.0
API_PORT=8888
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
API_TIMEOUT=30
LOG_LEVEL=INFO
LOG_FILE=./logs/backend.log
ERROR_LOG_FILE=./logs/backend_err.log
DEBUG_SQL=false
JWT_SECRET=change-this-to-random-string
JWT_EXPIRATION_HOURS=24
HTTPS_ONLY=false
DEBUG=false
RELOAD=true
```

---

**Producto:** VeriQuery  
**Última actualización:** March 20, 2026
