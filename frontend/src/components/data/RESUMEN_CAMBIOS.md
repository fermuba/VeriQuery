/**
 * RESUMEN DE CAMBIOS - ANÁLISIS DINÁMICO
 * 
 * ============================================================================
 * 1. DATOS AHORA SON DINÁMICOS (NO HARDCODEADOS)
 * ============================================================================
 * 
 * ✅ ANTES (Hardcodeado):
 *    const riskData = [
 *      { nombre: 'Crítico', valor: 2 },
 *      { nombre: 'Alto', valor: 5 },
 *      ...
 *    ]
 * 
 * ✅ AHORA (Dinámico):
 *    const riskDistribution = [
 *      { 
 *        nombre: 'Crítico', 
 *        valor: auditEvents.filter(e => e.type === 'error' || ...).length 
 *      },
 *      ...
 *    ]
 * 
 * ============================================================================
 * 2. KPIs DINÁMICOS
 * ============================================================================
 * 
 * Anomalías:       auditEvents filtrados en últimos 7 días (status === 'failed')
 * Riesgo Máx.:     Calculado automáticamente según eventos
 * Consultas:       Count de eventos tipo 'query'
 * IPs bloqueadas:  Eventos con error que incluye 'bloqueada'
 * 
 * ============================================================================
 * 3. GRÁFICOS QUE AHORA SON DINÁMICOS
 * ============================================================================
 * 
 * Accesos Diarios:
 *   └─ Muestra últimos 7 días (calculados automáticamente)
 *   └─ Separa eventos success vs failed
 *   └─ Se actualiza cuando se agregan nuevos eventos
 * 
 * Distribución de Riesgos (Pie Chart):
 *   └─ Basado en clasificación de eventos
 *   └─ Se actualiza en tiempo real
 * 
 * Accesos por Hora:
 *   └─ Agrupa eventos en franjas horarias de 3 horas
 *   └─ Muestra densidad de actividad
 * 
 * ============================================================================
 * 4. SECCIÓN DE AUDITORÍA
 * ============================================================================
 * 
 * Muestra:
 * - Últimos 10 eventos (ordenados por fecha, más recientes primero)
 * - Tipo de evento (Query, BD, Error)
 * - Texto/descripción
 * - Timestamp
 * - Color según status (success=verde, failed=rojo, processing=azul)
 * 
 * Cada evento captura:
 * {
 *   id: timestamp,
 *   timestamp: ISO string,
 *   type: 'query' | 'error' | 'database',
 *   status: 'success' | 'failed' | 'processing',
 *   text: "Descripción",
 *   confidence?: 95,
 *   error?: "Mensaje de error"
 * }
 * 
 * ============================================================================
 * 5. FLUJO DE DATOS
 * ============================================================================
 * 
 * Usuario escribe pregunta
 *    ↓
 * useAppStore.sendQuery() llamado
 *    ↓
 * addAuditEvent({ type: 'query', text, status: 'processing' })
 *    ↓
 * Backend procesa
 *    ↓
 * Si éxito:
 *   addAuditEvent({ type: 'query', text, status: 'success', confidence: 95 })
 * Si falla:
 *   addAuditEvent({ type: 'error', text, status: 'failed', error: msg })
 *    ↓
 * DataPreviewPanel detecta cambios en auditEvents
 *    ↓
 * Gráficos se actualizan automáticamente
 *    ↓
 * AuditLog muestra nuevos eventos
 * 
 * ============================================================================
 * 6. CÓMO PRUEBAS ESTO
 * ============================================================================
 * 
 * 1. Abre DevTools (F12)
 * 2. Ve a la pestaña Análisis
 * 3. Vuelve al chat y envía una pregunta
 * 4. Los gráficos deberían actualizarse automáticamente
 * 5. El audit log debería mostrar el nuevo evento
 * 
 * ============================================================================
 * 7. SI QUIERES AGREGAR MÁS DATOS
 * ============================================================================
 * 
 * En store/useAppStore.js:
 * - addAuditEvent() acepta cualquier propiedad
 * - Ejemplo: addAuditEvent({ 
 *     type: 'query', 
 *     text, 
 *     status: 'success',
 *     confidence: 95,
 *     row_count: 10,
 *     execution_time_ms: 125,
 *     database: 'supabase_prod',
 *     user_id: 'user@example.com'
 *   })
 * 
 * Luego en DataPreviewPanel, puedes hacer:
 *   const avgExecutionTime = auditEvents
 *     .filter(e => e.execution_time_ms)
 *     .reduce((sum, e) => sum + e.execution_time_ms, 0) / count
 * 
 * ============================================================================
 * 8. POSIBLES MEJORAS FUTURAS
 * ============================================================================
 * 
 * [ ] Filtrar audit log por tipo de evento
 * [ ] Buscar en audit log
 * [ ] Exportar como CSV/JSON
 * [ ] Gráfico de tiempo de ejecución promedio
 * [ ] Estadísticas de confianza promedio
 * [ ] Heatmap de actividad por hora/día
 * [ ] Alerts para eventos críticos
 * [ ] Retención de datos (últimos 30 días, 90 días, etc)
 */
