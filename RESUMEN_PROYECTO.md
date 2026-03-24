# 📊 VeriQuery - Resumen del Proyecto

## 🎯 ¿Qué es VeriQuery?

**VeriQuery** es una aplicación full-stack que convierte **preguntas en lenguaje natural a SQL** y las ejecuta automáticamente en bases de datos.

### Ejemplo de flujo:
```
Usuario escribe: "Cuántos clientes hay?"
                    ↓
        Backend genera SQL automático
                    ↓
       SQL ejecuta: SELECT COUNT(*) FROM clientes
                    ↓
      Frontend muestra: "Hay 42 clientes"
```

---

## 🏗️ Arquitectura General

### Backend (Python FastAPI)
```
┌─────────────────────────────────────────────────────┐
│  USUARIO FRONTEND                                   │
│  Chat: "¿Cuántos clientes?"                        │
└────────────────────┬────────────────────────────────┘
                     ↓ POST /api/query
┌─────────────────────────────────────────────────────┐
│  QUERY SERVICE                                      │
│  • Valida input de usuario (seguridad)             │
│  • Controla flujo general                          │
│  • Coordina con otras services                     │
└────────┬──────────────┬──────────────┬──────────────┘
         ↓              ↓              ↓
    ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
    │ SCHEMA      │ │ AMBIGUITY   │ │ NL2SQL       │
    │ SERVICE     │ │ SERVICE     │ │ GENERATOR    │
    │             │ │             │ │              │
    │ • Carga     │ │ • Detecta   │ │ • Prompt     │
    │   tablas y  │ │   frases    │ │   + LLM      │
    │   esquema   │ │   ambiguas  │ │   (Azure)    │
    │ • Cachea    │ │   (mejor,   │ │ • Genera     │
    │   datos     │ │   peor,     │ │   SQL        │
    │ • Sincro    │ │   más)      │ │ • Valida     │
    │   con LLM   │ │             │ │   seguridad  │
    └─────────────┘ └─────────────┘ └──────────────┘
                     ↓
    ┌─────────────────────────────────────────────┐
    │  MULTI-DATABASE CONNECTOR                   │
    │  • Detecta qué base de datos usar          │
    │  • Ejecuta SQL en la BD correcta           │
    │  • Soporta: PostgreSQL, SQL Server, MySQL  │
    └─────────────────────────────────────────────┘
                     ↓
    ┌─────────────────────────────────────────────┐
    │  BASES DE DATOS REALES                      │
    │  • PostgreSQL (Supabase Cloud)             │
    │  • SQL Server (Azure SQL)                  │
    │  • MySQL (configurable)                    │
    └─────────────────────────────────────────────┘
```

### Frontend (React + Vite)
```
┌─────────────────────────────────────────────────────┐
│  APP.JSX (Punto de entrada)                         │
│  • Verifica conexión al backend                    │
│  • Routing: WelcomeScreen → ChatContainer          │
└────────────────────┬────────────────────────────────┘
                     ↓
        ┌────────────────────────────────┐
        │  ZUSTAND STORE (State)         │
        │  • selectedDatabase            │
        │  • sessionId                   │
        │  • messages[]                  │
        │  • conversationHistory         │
        └────────────────────────────────┘
                     ↓
        ┌────────────────────────────────┐
        │  COMPONENTES                   │
        │                                │
        │  • ChatContainer               │
        │    └─ Input + Messages         │
        │                                │
        │  • DatabaseConfigPanel         │
        │    └─ Seleccionar/Agregar BD  │
        │                                │
        │  • DataPreviewPanel            │
        │    └─ Mostrar resultados SQL   │
        │                                │
        │  • AmbiguityResolver           │
        │    └─ Preguntas aclaratorias   │
        └────────────────────────────────┘
```

---

## 🔧 Componentes Principales

### 1. **Query Service** (`src/backend/services/query_service.py`)
- **Responsabilidad:** Orquestar todo el flujo de una pregunta
- **Flujo:**
  1. Recibe pregunta + sesión + base de datos
  2. Valida seguridad
  3. Obtiene schema de la BD
  4. Detecta ambigüedad
  5. Genera SQL con LLM
  6. Ejecuta SQL
  7. Retorna resultado

### 2. **Schema Service** (`src/backend/services/schema_service.py`)
- **Responsabilidad:** Leer tablas y estructura de BDs
- **Características:**
  - Cachea esquema por BD (evita múltiples scans)
  - Soporta PostgreSQL, SQL Server, MySQL
  - Retorna: nombre de tablas, columnas, tipos de datos

### 3. **NL2SQL Generator** (`src/backend/nl2sql_generator.py`)
- **Responsabilidad:** Convertir lenguaje natural a SQL
- **Pasos internos:**
  1. Detecta ambigüedad (palabras como "mejor", "peor")
  2. Enriquece pregunta con contexto
  3. Llama a Azure OpenAI (GPT-4o mini)
  4. Extrae SQL del response del LLM
  5. Valida que sea SELECT (no DELETE, DROP, etc.)
  6. Retorna SQL + razonamiento + explicación amigable

### 4. **Ambiguity Detector** (`src/backend/agents/ambiguity_detector.py`)
- **Responsabilidad:** Detectar preguntas ambiguas
- **Ejemplos de ambigüedad:**
  - "Los **mejores** clientes" → ¿por qué criterio?
  - "Los **peores** productos" → ¿por qué métrica?
  - "**Más** ventas" → ¿vs qué período?
- **Acción:** Si detecta ambigüedad, retorna preguntas aclaratorias al usuario

### 5. **Multi-Database Connector** (`src/backend/database/multi_db_connector.py`)
- **Responsabilidad:** Ejecutar SQL en la BD correcta
- **Soporta:**
  - PostgreSQL (Supabase, Azure PostgreSQL)
  - SQL Server (Azure SQL)
  - MySQL
- **Detecta:** Qué BD usar según el `database_name` en request

### 6. **Query Tracer** (`src/backend/core/tracer.py`)
- **Responsabilidad:** Logging detallado del flujo
- **Registra:**
  - Cada paso del procesamiento
  - Tiempos de ejecución
  - Inputs y outputs de cada componente
  - Razonamiento del LLM
- **Salida:** Logs con formato `[TRACE]` en stderr

### 7. **Security Layer**
- **Prompt Shield:** Detecta inyecciones SQL, XSS, prompt injection
- **Input Validation:** Valida que usuario no envíe comandos peligrosos
- **Output Sanitization:** Limpia resultados antes de retornar

---

## 🤖 Productos Microsoft Usados

### 1. **Azure OpenAI (LLM - Language Model)**
```
Servicio:  Azure OpenAI Service
URL:       https://[tu-recurso].openai.azure.com/
API Key:   Se carga desde .env (AZURE_OPENAI_API_KEY)
Modelo:    GPT-4o mini (gpt-4o-mini-deployment)
```

**¿Qué hace?**
- Recibe pregunta en lenguaje natural
- Recibe schema de BD (estructura de tablas)
- Retorna SQL generada automáticamente
- Retorna razonamiento (por qué eligió esa query)
- Retorna explicación amigable del resultado

**Ejemplo de prompt que enviamos:**
```
Sistema eres un experto en SQL para PostgreSQL
Tablas disponibles: usuarios (id, nombre, email), pedidos (id, usuario_id, monto)
Pregunta del usuario: "¿Cuáles son los 5 mejores clientes por monto?"
Genera: SELECT usuario_id, SUM(monto) FROM pedidos GROUP BY usuario_id ORDER BY SUM(monto) DESC LIMIT 5
```

**Configuración:**
```
AZURE_OPENAI_API_KEY=tu-clave
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_GPT4O_MINI=gpt-4o-mini-deployment
```

### 2. **Azure SQL Database (Base de Datos SQL Server)**
```
Servicio:  Azure SQL Database
Tipo:      SQL Server
Host:      sql-forensic-southcentral.database.windows.net
BD:        db-forensic-data
Puerto:    1433
Estado:    Conectado pero no accesible desde esta red
```

**¿Qué hace?**
- Almacena datos de bases de datos
- Ejecuta queries SQL generadas
- Retorna resultados tabulares

### 3. **Supabase PostgreSQL (Base de Datos PostgreSQL)**
```
Servicio:  Supabase (PostgreSQL en la nube)
Tipo:      PostgreSQL
BD:        supabase_prod (configurada)
Estado:    ✅ CONECTADO Y FUNCIONANDO
```

**¿Qué hace?**
- BD principal del sistema (ya que Azure SQL no es accesible)
- Almacena datos operacionales
- Ejecuta las queries que genera el LLM

---

## 🔄 Flujo Completo de Ejemplo

### Usuario escribe: "¿Cuántos clientes nuevos hay este mes?"

```
1. FRONTEND
   └─ Usuario escribe pregunta
   └─ Click enviar
   └─ Envía POST /api/query con:
      {
        "question": "¿Cuántos clientes nuevos hay este mes?",
        "session_id": "session_test@forensic.guardian",
        "database_name": "supabase_prod"
      }

2. QUERY SERVICE (Backend)
   └─ Recibe request
   └─ Valida seguridad con PromptShield ✅
   └─ Obtiene schema de supabase_prod
      └─ Resultado: "Tablas: usuarios, pedidos, productos..."
   
3. AMBIGUITY DETECTOR
   └─ Analiza pregunta
   └─ NO detecta ambigüedad ✅
   
4. NL2SQL GENERATOR
   └─ Llama a Azure OpenAI con:
      - Pregunta: "¿Cuántos clientes nuevos hay este mes?"
      - Schema: Lista de tablas y columnas
      - BD Type: postgresql
   
5. AZURE OPENAI (LLM)
   └─ Procesa con GPT-4o mini
   └─ Genera SQL:
      SELECT COUNT(*) as nuevos_clientes
      FROM usuarios
      WHERE created_at >= date_trunc('month', CURRENT_DATE)
   
6. VALIDACIÓN
   └─ Valida que sea SELECT ✅
   └─ Valida que no sea inyección SQL ✅
   
7. MULTI-DB CONNECTOR
   └─ Ejecuta SQL en supabase_prod (PostgreSQL)
   └─ Resultado: { nuevos_clientes: 42 }
   
8. QUERY SERVICE
   └─ Retorna respuesta:
      {
        "sql": "SELECT COUNT(*) ...",
        "result": [{ "nuevos_clientes": 42 }],
        "explanation": "Esta consulta cuenta los clientes...",
        "reasoning": "Se eligió la tabla usuarios porque...",
        "trace": {...} con todos los pasos
      }

9. FRONTEND
   └─ Recibe respuesta
   └─ Muestra en chat:
      - Pregunta original
      - Resultado: "42 clientes nuevos"
      - Explicación
      - Botón para ver SQL
   └─ DataPreviewPanel muestra tabla con resultado
```

---

## 📊 Stack Tecnológico

### Backend
- **Framework:** FastAPI (Python)
- **LLM:** Azure OpenAI (GPT-4o mini)
- **Bases de Datos:**
  - PostgreSQL (Supabase - PRIMARY)
  - SQL Server (Azure - SECONDARY)
  - MySQL (Opcional)
- **Seguridad:** Azure Content Safety, Custom Prompt Shield
- **Logging:** Python logging + Custom QueryTracer
- **Async:** asyncio, httpx

### Frontend
- **Framework:** React 19
- **Build:** Vite
- **State Management:** Zustand
- **HTTP Client:** Axios
- **UI:** React hooks, custom CSS

### Infraestructura
- **Backend Host:** Local (0.0.0.0:8000) / Producción (Azure App Service)
- **Frontend Host:** Local (localhost:5173) / Producción (Azure Static Web Apps)
- **BD Cloud:** Supabase (PostgreSQL), Azure SQL
- **LLM:** Azure OpenAI Service

---

## ✨ Características Principales

### ✅ Implementadas
1. **Conversión NL → SQL automática** con Azure OpenAI
2. **Multi-database support** (PostgreSQL, SQL Server, MySQL)
3. **Schema caching** para optimizar performance
4. **Ambiguity detection** para preguntas confusas
5. **Security layer** contra inyecciones y prompt injection
6. **Query tracer** con logging detallado
7. **Session management** para contexto conversacional
8. **Real-time frontend** con React + Vite
9. **Database wizard** para agregar nuevas BDs
10. **Data preview panel** para visualizar resultados

### 🚀 Próximas Mejoras
1. Histórico de conversaciones persistente
2. Explicaciones más detalladas del razonamiento
3. Sugerencias de queries similares
4. Machine learning para mejorar accuracy
5. Integración con más bases de datos
6. Cache de queries frecuentes

---

## 📝 Resumen en Tres Líneas

**VeriQuery** es una aplicación que usa **Azure OpenAI (GPT-4o mini)** para convertir preguntas en lenguaje natural a SQL, ejecutarlas automáticamente en **Supabase PostgreSQL** o **Azure SQL**, y mostrar los resultados en un chat interactivo con **React + FastAPI**.

---

## 🎓 ¿Quién está usando esto?

- **Backend:** Tu equipo (desarrollo Python)
- **Frontend:** Tu equipo (desarrollo React)
- **LLM:** Azure OpenAI (Microsoft Cloud)
- **Datos:** Supabase PostgreSQL (data cloud)

---

## 📌 Rama Actual

- **main:** Versión estable (solo lo de tu amigo)
- **feature/integrate-cloud-db:** Versión en desarrollo (todo lo que trabajamos)
