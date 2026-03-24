# 🔷 Azure AD App Registration Setup Guide

## 🎯 Objetivo

Crear una aplicación en Azure AD (Microsoft Entra ID) para que ForensicGuardian pueda autenticar usuarios.

---

## 📋 Paso 1: Acceder a Azure Portal

1. Ir a https://portal.azure.com
2. Sign in con tu cuenta Microsoft
3. Ir a **Azure Active Directory** (o buscar "Azure AD")

---

## 🔧 Paso 2: Crear Nueva App Registration

### 2.1 Acceder a App Registrations

```
Azure Active Directory
  └─ Manage
     └─ App registrations
        └─ [Click] New registration
```

### 2.2 Rellenar Formulario

```
Name:                 ForensicGuardian
Supported account types:  Accounts in this organizational directory only
Redirect URI:         
  - Platform: Web
  - URI: http://localhost:8000/callback
```

**Para Desarrollo:**
- Redirect URI: `http://localhost:8000/callback`
- Redirect URI: `http://localhost:3000/auth/callback` (if frontend)

**Para Producción:**
- Redirect URI: `https://api.company.com/callback`
- Redirect URI: `https://app.company.com/auth/callback`

### 2.3 Click "Register"

---

## 📝 Paso 3: Obtener Credenciales

### 3.1 Copiar IDs Importantes

En la página de tu app, verás:

```
Application (client) ID:    ← COPIAR → AZURE_CLIENT_ID
Object ID:                  ← NOTAR
Directory (tenant) ID:      ← COPIAR → AZURE_TENANT_ID
```

**Ejemplo:**
```
Application (client) ID:    550e8400-e29b-41d4-a716-446655440000
Directory (tenant) ID:      550e8400-e29b-41d4-a716-446655441111
```

### 3.2 Calcular ISSUER

Formula:
```
AZURE_ISSUER = https://login.microsoftonline.com/{TENANT_ID}/v2.0
```

Ejemplo:
```
AZURE_ISSUER = https://login.microsoftonline.com/550e8400-e29b-41d4-a716-446655441111/v2.0
```

---

## 🔐 Paso 4: Configurar API Permissions (Opcional)

1. En tu app → **API permissions**
2. Click **Add a permission**
3. Seleccionar **Microsoft Graph**
4. Seleccionar **Delegated permissions**
5. Agregar:
   - `User.Read` (usuario actual)
   - `Directory.Read.All` (opcional, si necesitas listar usuarios)

---

## 🔑 Paso 5: Crear Client Secret (Opcional - para M2M)

Si tu backend necesita llamar a Microsoft APIs:

1. En tu app → **Certificates & secrets**
2. Click **New client secret**
3. Description: "ForensicGuardian Backend"
4. Expires: Seleccionar tiempo (24 months recomendado)
5. Click **Add**
6. **COPIAR** el valor del secret inmediatamente (no se mostrará después)

⚠️ **IMPORTANTE:** El secret es como una contraseña. **Nunca lo pushees a GitHub.**

---

## 📝 Paso 6: Actualizar `.env`

En la raíz de tu proyecto, crear o actualizar `.env`:

```bash
# .env

# Valores que obtuviste en Azure Portal
AZURE_CLIENT_ID="550e8400-e29b-41d4-a716-446655440000"
AZURE_TENANT_ID="550e8400-e29b-41d4-a716-446655441111"
AZURE_ISSUER="https://login.microsoftonline.com/550e8400-e29b-41d4-a716-446655441111/v2.0"
AZURE_AUDIENCE="550e8400-e29b-41d4-a716-446655440000"

# Opcional (solo si usas M2M)
# AZURE_CLIENT_SECRET="xvz..."

# JWT Configuration
TOKEN_EXPIRATION_TOLERANCE=60
JWKS_CACHE_TTL=3600

# Users
DEFAULT_USER_ROLE="analyst"
```

---

## ✅ Paso 7: Verificar Configuración

```bash
# Ejecutar el validador
python verify_auth_setup.py

# Debería mostrar:
# ✅ auth.config imported
# ✅ auth.schemas imported
# ✅ AZURE_CLIENT_ID is set
# etc.
```

---

## 🧪 Paso 8: Test Initial Token (Optional)

### Opción 1: Usar Azure CLI

```bash
# Instalar Azure CLI
# https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

# Login
az login

# Get token
az account get-access-token --resource=550e8400-e29b-41d4-a716-446655440000

# Copiar el "accessToken"
```

### Opción 2: Usar Microsoft Graph Explorer

1. Ir a https://developer.microsoft.com/en-us/graph/graph-explorer
2. Sign in con tu cuenta
3. Copiar el token del header

### Opción 3: Usar tu App Frontend

1. Configurar tu frontend (React, Angular, etc.) con MSAL
2. Login como usuario
3. Obtener token
4. Enviar a tu backend con `Authorization: Bearer <token>`

---

## 🚀 Paso 9: Test con Backend

```bash
# Con un token válido (del paso 8):
export TOKEN="eyJhbGciOiJSUzI1NiI..."

# Llamar endpoint protegido
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/auth/me

# Respuesta esperada:
# {
#   "id": "user-uuid",
#   "email": "user@company.com",
#   "name": "User Name",
#   "role": "analyst"
# }
```

---

## 🔍 Troubleshooting

### Error: "No matching key found in JWKS"

**Causa:** Token no fue emitido por tu tenant.

**Solución:**
1. Verificar que token es del tenant correcto
2. Verificar `AZURE_TENANT_ID` es correcto

```bash
# Decodificar token (sin verificar) para ver claims
python -c "
import jwt
token = 'your-token-here'
print(jwt.decode(token, options={'verify_signature': False}))
"
```

### Error: "Token issuer mismatch"

**Causa:** `AZURE_ISSUER` en `.env` no coincide con issuer en token.

**Solución:**
```bash
# Verificar formato
# Debe ser: https://login.microsoftonline.com/{TENANT_ID}/v2.0

# Verificar TENANT_ID es correcto
```

### Error: "AZURE_CLIENT_ID not set"

**Causa:** Variables de entorno no cargadas.

**Solución:**
1. Verificar `.env` existe en raíz del proyecto
2. Reiniciar terminal o IDE
3. Ejecutar: `python verify_auth_setup.py`

---

## 📚 Referencias Importantes

| Recurso | Enlace |
|---------|--------|
| Azure Portal | https://portal.azure.com |
| Microsoft Docs | https://learn.microsoft.com/en-us/azure/active-directory/ |
| MSAL.js (Frontend) | https://github.com/AzureAD/microsoft-authentication-library-for-js |
| MSAL Python | https://github.com/AzureAD/microsoft-authentication-library-for-python |
| JWT.io | https://jwt.io (para inspeccionar tokens) |
| Graph Explorer | https://developer.microsoft.com/graph/graph-explorer |

---

## ✅ Checklist

- [ ] Accedí a Azure Portal
- [ ] Creé nueva app registration "ForensicGuardian"
- [ ] Copié Application (client) ID
- [ ] Copié Directory (tenant) ID
- [ ] Calculé AZURE_ISSUER
- [ ] Actualicé `.env` con credenciales
- [ ] Ejecuté `verify_auth_setup.py`
- [ ] Probé endpoint protegido con token válido
- [ ] Leí documentación de integración

---

## 🎯 Next Steps

1. **Desarrollo Local:**
   - Todo setup está listo
   - Usa tokens del Azure AD
   - Test con cURL o Postman

2. **Integración con Frontend:**
   - Usa MSAL.js o similar
   - Obtén token de Microsoft
   - Envía en header `Authorization: Bearer <token>`

3. **Producción:**
   - Agregar Redirect URIs para dominio real
   - Usar Azure Key Vault para secrets
   - Habilitar HTTPS
   - Configurar WAF

---

## 📞 Support

Si tienes problemas:

1. Ejecuta `verify_auth_setup.py` y revisa los errores
2. Decodifica el JWT en https://jwt.io para ver los claims
3. Lee `AUTH_IMPLEMENTATION_COMPLETE.md` sección Troubleshooting
4. Revisa logs del servidor para mensajes de error

---

**Azure AD Setup Completado ✅**
