/**
 * SECCIÓN DE AUDITORÍA - QUÉ DEBERÍA VERSE
 * 
 * La sección de Auditoría muestra el registro de todas las operaciones de la aplicación
 * 
 * ============================================================================
 * INFORMACIÓN QUE DEBERÍA APARECER:
 * ============================================================================
 * 
 * Por cada evento de auditoría:
 * 
 * 1. TIMESTAMP (Hora/Fecha)
 *    - Ejemplo: "26 Mar 2026 14:32:15"
 *    - Debe ser legible y cercano
 *    - Formato local (en español)
 * 
 * 2. TIPO DE EVENTO
 *    - query: Cuando el usuario hace una pregunta
 *    - error: Cuando ocurre un error
 *    - login: Cuando se inicia sesión
 *    - database_change: Cuando se cambia de base de datos
 * 
 * 3. DESCRIPCIÓN/ACCIÓN
 *    - El texto de la pregunta (para queries)
 *    - El mensaje de error (para errores)
 *    - "Cambio a base de datos: X" (para cambios de DB)
 * 
 * 4. ESTADO
 *    - success: ✅ Verde - Completado exitosamente
 *    - failed: ❌ Rojo - Falló
 *    - processing: ⏳ Amarillo - En proceso
 * 
 * 5. CONFIANZA (para queries)
 *    - Porcentaje de confianza (0-100%)
 *    - Indicador visual (barra o badge)
 * 
 * 6. RESULTADO (opcional)
 *    - Número de registros procesados
 *    - Error específico si falló
 * 
 * ============================================================================
 * EJEMPLO VISUAL:
 * ============================================================================
 * 
 * [26 Mar 14:32] ✅ Query - Éxito
 * └─ "¿Cuántos clientes tenemos en total?"
 * └─ Confianza: 95% | 1 registro | 125ms
 * 
 * [26 Mar 14:28] ❌ Query - Error
 * └─ "SELECT * FROM tablaNoExiste"
 * └─ Error: Table not found | 0 registros
 * 
 * [26 Mar 14:25] ⏳ Database
 * └─ Cambio a base de datos: supabase_prod
 * └─ Conectando...
 * 
 * [26 Mar 14:20] ✅ Query - Éxito
 * └─ "Últimas 10 compras"
 * └─ Confianza: 87% | 10 registros | 234ms
 * 
 * ============================================================================
 * DATOS QUE DEBERÍA CAPTURAR:
 * ============================================================================
 * 
 * Cada evento debería tener:
 * {
 *   id: timestamp único,
 *   timestamp: "2026-03-26T14:32:15Z",
 *   type: "query" | "error" | "login" | "database_change",
 *   status: "success" | "failed" | "processing",
 *   text: "Descripción o pregunta",
 *   confidence: 95 (0-100),
 *   result_count: 1,
 *   execution_time_ms: 125,
 *   error: "Mensaje de error si aplica",
 *   user: "user@example.com",
 *   database: "supabase_prod"
 * }
 * 
 * ============================================================================
 * CÓMO ESTÁ ACTUALMENTE:
 * ============================================================================
 * 
 * En useAppStore.js tienes:
 * - addAuditEvent() que agrega eventos al array auditEvents
 * - Se llama automáticamente cuando:
 *   - Se envía una query
 *   - Ocurre un error
 *   - Se cambia de base de datos
 * 
 * El componente AuditLog.jsx es responsable de mostrar estos eventos
 * 
 * ============================================================================
 * MEJORAS QUE PODRÍAS HACER:
 * ============================================================================
 * 
 * 1. FILTRAR por tipo de evento:
 *    - Todas
 *    - Solo queries exitosas
 *    - Solo errores
 *    - Solo cambios de BD
 * 
 * 2. ORDENAR por:
 *    - Más reciente primero (actual)
 *    - Más antiguo primero
 *    - Por tipo
 * 
 * 3. BUSCAR/FILTRAR:
 *    - Por texto en la descripción
 *    - Por rango de fechas
 * 
 * 4. EXPORTAR:
 *    - Descargar como CSV
 *    - Descargar como JSON
 * 
 * 5. LIMPIEZA:
 *    - Limpiar audit log
 *    - Borrar eventos antiguos
 * 
 * ============================================================================
 * PRÓXIMOS PASOS:
 * ============================================================================
 * 
 * 1. Revisar AuditLog.jsx para ver cómo se renderiza
 * 2. Mejorar el formato de fecha/hora
 * 3. Agregar más detalles a cada evento
 * 4. Agregar filtros y búsqueda
 * 5. Mejorar indicadores visuales (colores, iconos)
 */
