# 🐳 Levantando SQL Server con Contoso en Docker

## Paso 1: Levanta el contenedor

```bash
cd database/
docker-compose -f compose.yaml up -d
```

**Espera 30-60 segundos** a que el contenedor se inicie completamente.

Verifica que está corriendo:
```bash
docker ps | grep sqlserver-contoso
```

---

## Paso 2: Restaura la base de datos

### Opción A: Desde SQL Server Management Studio (SSMS)
1. Abre SSMS
2. Conecta a: `localhost,1433` con usuario `sa` y contraseña `VeriQuery26!`
3. Click derecho en "Databases" → "Restore Database"
4. En "Device" selecciona el archivo: `/assets/ContosoV210k.bak`
5. Click "OK"

### Opción B: Desde línea de comandos
```bash
# Accede al contenedor
docker exec -it sqlserver-contoso /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P VeriQuery26!

# Ejecuta el script de restauración
1> :r /assets/restore.sql
2> GO
```

### Opción C: Desde PowerShell (Windows)
```bash
docker exec -it sqlserver-contoso /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P VeriQuery26! -i /assets/restore.sql
```

---

## Paso 3: Verifica que funciona

```bash
docker exec -it sqlserver-contoso /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P VeriQuery26! -Q "SELECT name FROM sys.databases"
```

Deberías ver en la salida:
```
name
master
tempdb
model
msdb
ContosoV210k
```

---

## Paso 4: Agrega la BD a ForensicGuardian

En la app, ve a "Agregar Base de Datos" y rellena:

| Campo | Valor |
|-------|-------|
| **Nombre** | `contoso_local` |
| **Tipo** | SQL Server |
| **Host** | `localhost` |
| **Puerto** | `1433` |
| **Database** | `ContosoV210k` |
| **Usuario** | `sa` |
| **Contraseña** | `VeriQuery26!` |

Haz clic en "Probar conexión" ✅

---

## Comandos útiles

### Detener el contenedor
```bash
docker-compose -f database/compose.yaml down
```

### Ver logs del contenedor
```bash
docker logs -f sqlserver-contoso
```

### Acceder a la terminal del contenedor
```bash
docker exec -it sqlserver-contoso bash
```

### Eliminar el volumen (CUIDADO: borra los datos)
```bash
docker volume rm forensicguardian_sqlserver_data
```

---

## 🔧 Troubleshooting

### "Connection refused" al intentar conectar
- Espera 60 segundos después de levantar el contenedor
- Verifica que el puerto 1433 no esté en uso: `netstat -an | findstr 1433`

### "Cannot restore database, file already exists"
- Usa `REPLACE` en el script (ya está incluido en `restore.sql`)

### "Login failed for user 'sa'"
- Verifica la contraseña: debe ser `VeriQuery26!`
- Asegúrate que el contenedor está corriendo: `docker ps`

---

## ✅ Listo para usar

Una vez restaurada la BD, puedes:
1. Activar `contoso_local` desde la app
2. Hacer scan del schema
3. ¡Hacer queries contra Contoso localmente!

