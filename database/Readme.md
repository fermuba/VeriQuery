## Base de datos local con SQL Server en Docker

Para trabajar con la base de datos en local, se recomienda crear una carpeta específica para el entorno de SQL Server. Por ejemplo:

`~/sqlserver-contoso`

Dentro de esa carpeta se debe guardar el archivo `compose.yaml`, que será el encargado de levantar el contenedor de SQL Server con Docker Compose.

### Estructura recomendada

```text
sqlserver-contoso/
├── compose.yaml
└── assets/


### ¿Qué contiene cada elemento?

- `compose.yaml`: define el servicio de SQL Server, el puerto expuesto y los volúmenes necesarios.
- `assets/`: carpeta pensada para guardar archivos auxiliares relacionados con la base de datos.

Dentro de `assets/` se pueden colocar:

- el archivo `.bak` de la base de datos
- scripts `.sql`
- cualquier archivo adicional necesario para restaurar o trabajar con la base

### ¿Por qué usar esta estructura?

Esta organización permite:

- mantener separado el entorno de base de datos del resto del proyecto
- tener una carpeta clara para ubicar backups y scripts
- facilitar que otra persona del equipo replique el mismo entorno
- evitar perder datos al recrear el contenedor, siempre que se use persistencia con volúmenes

### Flujo general de uso

1. Crear la carpeta del entorno local de SQL Server.
2. Colocar dentro el archivo `compose.yaml`.
3. Guardar el backup `.bak` en la carpeta `assets/`.
4. Levantar el contenedor con Docker Compose.
5. Restaurar la base desde el archivo `.bak`.

### Nota importante

La imagen de Docker de SQL Server no incluye la base de datos Contoso cargada.  
La base debe descargarse por separado y luego restaurarse dentro del contenedor.


Y si querés dejar indicado cuál archivo bajar:

### Archivo de respaldo de la base de datos

El archivo `.bak` no se versiona en el repositorio.  
Debe descargarse manualmente y colocarse dentro de la carpeta `assets/`.

Ruta esperada:

```text
sqlserver-contoso/assets/

### Archivo requerido

Descargar el archivo `ContosoV2100k.bak` desde el siguiente enlace y copiarlo dentro de `assets/`:

[Descargar `ContosoV2100k.bak`](https://drive.google.com/drive/folders/1rA7L35jf9htn2sNo78RZ-mbsey6JLJWG?usp=sharing)
