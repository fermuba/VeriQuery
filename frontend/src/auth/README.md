# Frontend Authentication with Azure AD (Entra ID)

Este módulo proporciona una capa de autenticación lista para producción utilizando Microsoft Entra ID (Azure AD) con MSAL para React.

##  Tabla de Contenidos

- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [API Reference](#api-reference)
- [Ejemplos](#ejemplos)

##  Instalación

Las dependencias ya están instaladas:

```bash
npm install @azure/msal-browser @azure/msal-react react-router-dom
```

##  Configuración

### 1. Variables de Entorno

Actualiza tu `.env` con las credenciales de Azure AD:

```env
VITE_AZURE_CLIENT_ID=your-client-id
VITE_AZURE_TENANT_ID=your-tenant-id
VITE_AZURE_REDIRECT_URI=http://localhost:5173/callback
```

Obtén estos valores de tu Azure AD app registration:
- **Client ID**: "Application (client) ID"
- **Tenant ID**: "Directory (tenant) ID"
- **Redirect URI**: URL de callback (debe coincidir en Azure AD)

### 2. Envuelve tu App con MsalAuthProvider

**`main.jsx`:**

```jsx
import React from "react";
import ReactDOM from "react-dom/client";
import { MsalAuthProvider } from "@/auth";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <MsalAuthProvider>
      <App />
    </MsalAuthProvider>
  </React.StrictMode>
);
```

##  Uso

### Hook `useAuth()`

Accede al estado y métodos de autenticación:

```jsx
import { useAuth } from "@/auth";

export function MyComponent() {
  const { 
    user,              // Usuario autenticado
    isAuthenticated,   // true/false
    isLoading,         // Cargando
    login,             // Función para login
    logout,            // Función para logout
    getAccessToken,    // Obtener token para API
    error              // Mensaje de error
  } = useAuth();

  return (
    <div>
      {isLoading && <p>Cargando...</p>}
      {!isAuthenticated ? (
        <button onClick={login}>Iniciar Sesión</button>
      ) : (
        <>
          <p>Bienvenido, {user.name}!</p>
          <p>Email: {user.email}</p>
          <p>Roles: {user.roles.join(", ")}</p>
          <button onClick={logout}>Cerrar Sesión</button>
        </>
      )}
    </div>
  );
}
```

### Componente `AuthGuard`

Protege rutas requiriendo autenticación:

```jsx
import { AuthGuard } from "@/auth";
import Dashboard from "./Dashboard";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        }
      />
    </Routes>
  );
}
```

#### Con Control de Roles

```jsx
<AuthGuard requiredRoles={["admin", "moderator"]}>
  <AdminPanel />
</AuthGuard>
```

### Hook `useApi()`

Realiza llamadas a la API con token automático:

```jsx
import { useApi } from "@/auth";

export function QueryBuilder() {
  const { post, get, error } = useApi();

  const handleQuery = async () => {
    // POST request
    const response = await post("/api/queries", {
      query: "SELECT * FROM evidence",
    });

    if (response.ok) {
      console.log("Resultado:", response.data);
    } else {
      console.error("Error:", response.error);
    }
  };

  const fetchProfile = async () => {
    // GET request
    const response = await get("/api/profile");
    
    if (response.ok) {
      console.log("Perfil:", response.data);
    }
  };

  return (
    <>
      <button onClick={handleQuery}>Ejecutar Query</button>
      <button onClick={fetchProfile}>Cargar Perfil</button>
    </>
  );
}
```

## 📚 API Reference

### `useAuth()`

**Retorna:**

```javascript
{
  user: {
    id: string,           // ID local
    email: string,        // Email del usuario
    name: string,         // Nombre del usuario
    roles: string[],      // Roles (extraídos del token)
    tenantId: string,     // Tenant ID
    oid: string          // Azure Object ID
  },
  isAuthenticated: boolean,
  isLoading: boolean,
  login: () => Promise<void>,
  logout: () => Promise<void>,
  getAccessToken: () => Promise<string | null>,
  error: string | null
}
```

### `useApi()`

**Retorna:**

```javascript
{
  request: (endpoint, options) => Promise<ApiResponse>,
  get: (endpoint, options?) => Promise<ApiResponse>,
  post: (endpoint, body?, options?) => Promise<ApiResponse>,
  put: (endpoint, body?, options?) => Promise<ApiResponse>,
  delete: (endpoint, options?) => Promise<ApiResponse>
}
```

**ApiResponse:**

```javascript
{
  ok: boolean,           // Éxito de la request
  status: number,        // HTTP status code
  data?: any,           // Respuesta parseada (JSON)
  error?: string        // Mensaje de error
}
```

### `AuthGuard`

**Props:**

- `children: React.ReactNode` - Componentes a mostrar si autenticado
- `requiredRoles?: string[]` - Roles requeridos
- `fallback?: React.ReactNode` - UI personalizada mientras carga

##  Ejemplos

### Ejemplo 1: Dashboard Protegido

```jsx
import { useAuth, AuthGuard } from "@/auth";

function Dashboard() {
  const { user, logout } = useAuth();

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Usuario: {user.name}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/dashboard"
        element={
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        }
      />
    </Routes>
  );
}
```

### Ejemplo 2: API Call con Autenticación

```jsx
import { useApi } from "@/auth";

export function EvidenceUpload() {
  const { post, isLoading } = useApi();

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await post("/api/evidence/upload", formData);

    if (response.ok) {
      alert("Archivo subido exitosamente");
    } else {
      alert(`Error: ${response.error}`);
    }
  };

  return (
    <input
      type="file"
      onChange={(e) => handleUpload(e.target.files[0])}
      disabled={isLoading}
    />
  );
}
```

### Ejemplo 3: Navbar con Estado de Auth

```jsx
import { useAuth } from "@/auth";
import { Link } from "react-router-dom";

export function Navbar() {
  const { user, isAuthenticated, login, logout, isLoading } = useAuth();

  if (isLoading) {
    return <nav>Cargando...</nav>;
  }

  return (
    <nav className="flex justify-between items-center p-4 bg-gray-800 text-white">
      <Link to="/">ForensicGuardian</Link>

      <div className="flex gap-4">
        {isAuthenticated ? (
          <>
            <span>{user.name}</span>
            <Link to="/profile">Perfil</Link>
            <button onClick={logout}>Logout</button>
          </>
        ) : (
          <button onClick={login}>Login</button>
        )}
      </div>
    </nav>
  );
}
```

##  Características de Seguridad

✅ **JWT Signature Verification**: Validado en backend  
✅ **JWKS Caching**: Optimización de rendimiento  
✅ **Role-Based Access Control**: Control granular de acceso  
✅ **Multi-Tenant Support**: Validación de tenant (backend)  
✅ **Token Expiration Handling**: Refresco automático  
✅ **Secure Token Storage**: localStorage con HTTPS  

## 🐛 Troubleshooting

### Error: "No access token available"
- Verifica que el usuario esté autenticado: `isAuthenticated === true`
- Comprueba que las variables de entorno estén configuradas

### Error: "CORS"
- El backend debe incluir los headers CORS correctos
- Verifica que `VITE_API_URL` sea correcto

### Error: "Unauthorized (401)"
- El token puede haber expirado
- El backend está rechazando el token
- Verifica que el backend esté validando correctamente

### Error: "Access Denied (403)"
- El usuario no tiene los roles requeridos
- Verifica que el token contenga los roles correctos

## 📖 Más Información

- [Microsoft MSAL Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-js)
- [Azure AD Documentation](https://docs.microsoft.com/en-us/azure/active-directory/)
- [OAuth 2.0 Flow](https://oauth.net/2/)

## 📄 Licencia

Parte de ForensicGuardian Project.
