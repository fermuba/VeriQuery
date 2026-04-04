-- Script para restaurar ContosoV210k desde el backup
-- Ejecutar esto dentro del contenedor de SQL Server después de levantarlo

-- Restaurar la base de datos desde el archivo .bak
RESTORE DATABASE [ContosoV210k] 
FROM DISK = N'/assets/ContosoV210k.bak' 
WITH FILE = 1, 
NOUNLOAD, 
REPLACE,
STATS = 5;

-- Verificar que se restauró correctamente
SELECT name, state_desc FROM sys.databases WHERE name = 'ContosoV210k';
