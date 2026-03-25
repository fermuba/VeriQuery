# VeriQuery: Arquitectura Robusta vs. LLM Tradicional

Este documento resume la madurez técnica y la arquitectura de **VeriQuery**. El objetivo es demostrar por qué este sistema va más allá de un simple "envoltorio" de Inteligencia Artificial y se posiciona como una herramienta *Enterprise-grade* segura, trazable y determinista.

---

## 1. El Problema del "LLM Tradicional" (Aproximación Ingenua)
Cuando se usa un LLM directamente para consultar bases de datos (NL2SQL), el enfoque común es enviar un prompt masivo con el esquema y la pregunta. Esto genera riesgos inaceptables en producción:
- **Alucinaciones:** El modelo inventa columnas o tablas que no existen.
- **Inconsistencia de Dialectos:** Mezcla sintaxis de Postgres (`LIMIT 10`) con SQL Server (`TOP 10`), rompiendo la ejecución.
- **Destrucción:** Puede generar comandos perjudiciales (`DROP`, `DELETE`) si el prompt no está blindado.
- **Falta de razonamiento:** Si la pregunta es ambigua, asume un contexto erróneo y entrega datos incorrectos en lugar de preguntar.

---

## 2. La Solución VeriQuery: Filosofía "Menos es Más"
Bajo la premisa de no usar parches frágiles (como expresiones regulares para código), diseñamos un **Pipeline Multi-Agente**. El sistema divide el problema en capas hiper-especializadas donde cada una hace una sola tarea y valida el resultado de la capa anterior.

### Capas Clave de Seguridad y Estabilidad:
1. **Validador de Intención Avanzado:** Detecta si la pregunta carece de contexto antes de intentar responder. Si la consulta es ambigua, frena y le ofrece opciones de corrección al usuario.
2. **Inyección de Schema Dinámica:** El modelo nunca debe adivinar. La estructura real de la base de datos se inyecta en milisegundos y se fuerza al modelo a atenerse a un contrato de salida estricto.
3. **Normalizador AST (`sqlglot`):** Es el corazón de la robustez. En lugar de procesar el SQL generado como texto plano, el sistema reconstruye el Árbol de Sintaxis Abstracta (AST). Esto significa que comprende genuinamente la consulta y **la traduce en tiempo real** al motor de base de datos activo (ej. intercepta sintaxis fallida de Postgres y la convierte a SQL Server).
4. **Validador Semántico Independiente:** Un segundo LLM revisa exclusivamente si la consulta SQL generada responde realmente a la pregunta original del usuario, garantizando precisión.

---

## 3. Flujo Visual de VeriQuery (Ciclo de Vida de una Consulta)

El siguiente diagrama muestra el tránsito de la pregunta del usuario (en azul) a través de nuestros validadores y normalizadores:

```mermaid
flowchart TD
    %% Estilos
    classDef user fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef agent fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    classDef process fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef db fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef error fill:#ef4444,stroke:#b91c1c,stroke-width:2px,color:#fff

    User([👤 Usuario (Lenguaje Natural)]):::user --> Intent[1. Validador de Intención\n(¿Es claro o ambiguo?)]:::agent
    
    Intent -- "Generar SQL" --> Context[Enriquecimiento con Historial\n(Recupera contexto si hay charla previa)]:::process
    Intent -- "Ambiguo / Falta Info" --> Clarificar([Devuelve Opciones Guiadas al Usuario]):::error
    
    Context --> Schema[Inyección Dinámica de Schema\n(Solo inyecta la BD activa)]:::db
    
    Schema --> Crafter[2. Query Crafter\n(Genera el SQL estricto)]:::agent
    
    Crafter --> Parse{3. Normalizador AST (sqlglot)\nAnaliza la estructura}:::process
    
    Parse -- "Error Sintáctico" --> Error([Rechazo Seguro (No toca la BD)]):::error
    Parse -- "Transpilado Exitosamente" --> Semantica[4. Validador Semántico\n(¿El SQL responde a la pregunta?)]:::agent
    
    Semantica -- "No cuadra" --> Clarificar
    Semantica -- "Validado" --> DBExec[(Ejecución en Base de Datos)]:::db
    
    DBExec --> Res[📊 Respuesta Final\nDatos + Explicación amigable]:::process
```

---

## 4. Conclusión para Presentación
El éxito de VeriQuery no reside en preguntarle a un LLM qué hacer. El diseño arquitectónico garantiza que el LLM está confinado dentro de una "caja de arena" de programación determinista, validaciones de sintaxis estructural y protocolos de aclaración.

Esto nos permite conectar cualquier tipo de base de datos sencilla (Contoso en SQL Server, Supabase en PostgreSQL, etc.) con la garantía de que ninguna consulta malformada afectará la experiencia del usuario o la estabilidad de los datos.
