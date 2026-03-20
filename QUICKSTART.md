# 🚀 Guía Rápida - Forensic Guardian# ⚡ QUICK START - Forensic Guardian



## ⚡ Iniciar el Sistema en 3 Pasos## Para tu compañero: 3 comandos y listo



### 1️⃣ Base de Datos (Docker SQL Server)### **Terminal 1 - Docker + BD**

```bash```powershell

# La BD debe estar corriendo. Verificar con:cd forensicGuardian\database

docker ps | grep mssqldocker-compose up -d

```

# Si no está corriendo:✅ Esperar 30 segundos

docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=YourPassword123!' \

  -p 1433:1433 -d --name sql-server mcr.microsoft.com/mssql/server:latest---

```

### **Terminal 2 - Backend**

### 2️⃣ Backend (FastAPI)```powershell

```bashcd forensicGuardian

cd c:\Users\Daniela\Desktop\forensicGuardianpython -m pip install -r requirements.txt  # Solo 1ra vez

python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8888 --reload

# Configurar python environment```

python -m venv venv✅ Esperar "Application startup complete"

venv\Scripts\activate

---

# Instalar dependencias

pip install -r requirements.txt### **Terminal 3 - Frontend**

```powershell

# Iniciar servidorcd forensicGuardian\frontend

python -m uvicorn src.backend.api.main:app --host 0.0.0.0 --port 8888 --reloadnpm run dev

``````

✅ Esperar "Local: http://localhost:5173/"

El backend estará en: `http://localhost:8888`

---

### 3️⃣ Frontend (React + Vite)

```bash## 🌐 Acceder

cd frontend

- **UI:** http://localhost:5173

# Instalar dependencias- **API Docs:** http://localhost:8888/docs

npm install- **Health:** http://localhost:8888/api/health



# Iniciar desarrollo---

npm run dev

```## 🧪 Primera Query



El frontend estará en: `http://localhost:5173`1. Ir a: http://localhost:8888/docs

2. Click en `/api/query` → "Try it out"

---3. Pegar:

```json

## 📊 Verificar que Todo Funciona{"query": "¿Cuántos clientes tenemos?"}

```

### Test Backend4. Execute ✅

```bash

curl http://localhost:8888/api/health---

```

## 🛑 Detener

Debería retornar: `{"status": "ok"}`

Cada terminal: **Ctrl+C**

### Test Frontend

Abrir: `http://localhost:5173`---



Debería mostrar: Chat interface con logo de Forensic Guardian**¡Listo! Ver SETUP.md para más detalles**


---

## 🔗 Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/health` | GET | Estado del servidor |
| `/api/query` | POST | Enviar pregunta en lenguaje natural |
| `/api/schema` | GET | Obtener schema de BD |

---

## ❓ Hacer una Pregunta

### Vía Frontend
1. Escribir pregunta en el chat
2. Click en enviar
3. Ver respuesta con SQL y gráfico

### Vía cURL
```bash
curl -X POST http://localhost:8888/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuántos beneficiarios tenemos?",
    "context": {}
  }'
```

---

## 🐛 Troubleshooting

### Backend no inicia
- Verificar puerto 8888 no esté en uso
- Verificar BD está corriendo
- Verificar variables de ambiente en `.env`

### Frontend no carga
- Verificar puerto 5173 no esté en uso
- Ejecutar `npm install` nuevamente
- Limpiar caché: `npm run clean` + `npm install`

### Preguntas retornan SQL erróneo
- Verificar schema en BD es correcto
- Ver logs del backend: `tail -f logs/*.log`
- Ejecutar: `python src/backend/test_query_crafter.py`

---

## 📚 Documentación Completa

Ver [`SETUP.md`](./SETUP.md) para configuración detallada.

---

## 🎯 Próximos Pasos

- [ ] Ejecutar tests: `pytest src/backend/tests/`
- [ ] Verificar seguridad: `python src/backend/test_security.py`
- [ ] Ver logs: `tail -f src/backend/logs/*.log`
- [ ] Hacer deploy en Azure: Ver `DEPLOY.md`
