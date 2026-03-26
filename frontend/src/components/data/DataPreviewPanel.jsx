import { motion } from 'framer-motion'
import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import AuditLog from './AuditLog'
import { Activity, BarChart3 } from 'lucide-react'
import { SimpleAreaChart, SimpleBarChart, SimplePieChart } from '../charts/SimpleCharts'

function Section({ title, children }) {
  return (
    <div className="flex flex-col gap-2">
      <p className="label-xs">{title}</p>
      {children}
    </div>
  )
}

export default function DataPreviewPanel() {
  const [activeTab, setActiveTab] = useState('audit')
  const { auditEvents, queryResult } = useAppStore()

  // ============================================================================
  // CALCULAR DATOS DINÁMICOS DEL AUDIT LOG
  // ============================================================================

  // Últimos 7 días de eventos
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - i))
    return date.toLocaleDateString('es-ES', { weekday: 'short' }).substring(0, 3)
  })

  // Contar eventos por día
  const accessDataByDay = last7Days.map(dia => {
    const dayEvents = auditEvents.filter(e => {
      const eventDate = new Date(e.timestamp)
      const eventDay = eventDate.toLocaleDateString('es-ES', { weekday: 'short' }).substring(0, 3)
      return eventDay === dia
    })
    
    const normal = dayEvents.filter(e => e.status === 'success').length
    const anomalo = dayEvents.filter(e => e.status === 'failed' || e.type === 'error').length
    
    return { dia, normal, anomalo: anomalo || 0 }
  })

  // Contar eventos por tipo para distribución de riesgo
  const riskDistribution = [
    { 
      nombre: 'Crítico', 
      valor: auditEvents.filter(e => e.type === 'error' || (e.status === 'failed' && e.error?.includes('seguridad'))).length || 0 
    },
    { 
      nombre: 'Alto', 
      valor: auditEvents.filter(e => e.status === 'failed').length || 0 
    },
    { 
      nombre: 'Medio', 
      valor: auditEvents.filter(e => e.status === 'processing').length || 0 
    },
    { 
      nombre: 'Bajo', 
      valor: auditEvents.filter(e => e.status === 'success').length * 0.3 || 0
    },
  ]

  // Accesos por hora (simular con eventos)
  const hourlyAccessData = Array.from({ length: 8 }, (_, i) => {
    const hora = (i * 3).toString().padStart(2, '0')
    const accesos = auditEvents.filter(e => {
      const eventHour = new Date(e.timestamp).getHours()
      return eventHour >= i * 3 && eventHour < (i + 1) * 3
    }).length || 0
    return { hora, accesos }
  })

  // KPI: Total de anomalías en últimos 7 días
  const totalAnomalies = auditEvents.filter(e => {
    const eventDate = new Date(e.timestamp)
    const daysAgo = Math.floor((Date.now() - eventDate) / (1000 * 60 * 60 * 24))
    return daysAgo <= 7 && (e.status === 'failed' || e.type === 'error')
  }).length

  // KPI: Máximo riesgo
  const maxRisk = riskDistribution.reduce((max, r) => r.valor > max ? r.valor : max, 0)
  const riskLevel = maxRisk === 0 ? 'BAJO' : maxRisk <= 5 ? 'BAJO' : maxRisk <= 10 ? 'MEDIO' : 'ALTO'

  // KPI: Total de consultas
  const totalQueries = auditEvents.filter(e => e.type === 'query').length

  // KPI: IPs bloqueadas (simulado)
  const blockedIPs = auditEvents.filter(e => e.status === 'failed' && e.error?.includes('bloqueada')).length

  return (
    <div className="p-4 flex flex-col gap-4 overflow-y-auto scrollbar-thin h-full">
      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        <button 
          onClick={() => setActiveTab('audit')}
          className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === 'audit' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <Activity className="w-4 h-4" />
          Auditoría
        </button>
        <button 
          onClick={() => setActiveTab('analytics')}
          className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === 'analytics' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Análisis
        </button>
      </div>

      {/* Audit Log Tab */}
      {activeTab === 'audit' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex-1 min-h-0 flex flex-col"
        >
          <div className="flex items-center justify-between mb-3">
            <p className="label-xs">Registro de Auditoría</p>
            {auditEvents.length > 0 && (
              <motion.span
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-xs bg-primary/20 text-primary px-2 py-1 rounded"
              >
                {auditEvents.length}
              </motion.span>
            )}
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            <AuditLog />
          </div>
        </motion.div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6 pb-4 overflow-y-auto scrollbar-thin"
        >
          {/* KPIs */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Anomalías', value: totalAnomalies.toString(), sub: 'últimos 7 días', color: 'text-destructive' },
              { label: 'Riesgo Máx.', value: riskLevel, sub: 'evaluado por IA', color: 'text-warning' },
              { label: 'Consultas', value: totalQueries.toString(), sub: 'esta semana', color: 'text-primary' },
              { label: 'IPs bloqueadas', value: blockedIPs.toString(), sub: 'en cuarentena', color: 'text-success' },
            ].map(k => (
              <div key={k.label} className="bento-card p-4">
                <p className="text-xs text-muted-foreground">{k.label}</p>
                <p className={`text-2xl font-bold mt-0.5 ${k.color}`}>{k.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{k.sub}</p>
              </div>
            ))}
          </div>

          {/* Accesos por día */}
          <SimpleAreaChart
            data={accessDataByDay}
            xKey="dia"
            yKey={['normal', 'anomalo']}
            title="Accesos Diarios - Últimos 7 días"
            height={250}
          />

          {/* Distribución de riesgo */}
          <SimplePieChart
            data={riskDistribution}
            nameKey="nombre"
            valueKey="valor"
            title="Distribución de Riesgos"
            height={280}
            donut={true}
          />

          {/* Accesos por hora */}
          <SimpleBarChart
            data={hourlyAccessData}
            xKey="hora"
            yKey="accesos"
            title="Accesos por Hora del Día"
            height={250}
          />
        </motion.div>
      )}
    </div>
  )
}