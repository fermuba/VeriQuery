/**
 * ChartRenderer - Renderiza gráficos automáticamente basado en los datos
 * Detecta el tipo de datos y muestra el gráfico más adecuado
 * 
 * Tipos soportados:
 * - Barras: Datos con categoría + valor numérico
 * - Líneas: Series de tiempo o progresiones
 * - Pie/Donut: Distribuciones y porcentajes
 * - Tabla: Datos complejos que no caben en otros gráficos
 */

import { useMemo } from 'react'
import {
  BarChart, Bar,
  LineChart, Line,
  PieChart, Pie, Cell,
  AreaChart, Area,
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts'
import { ChevronDown, BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, Activity, Table as TableIcon } from 'lucide-react'
import { useState } from 'react'

// Paleta de colores sobria, monocromática y profesional (escala de grises)
const COLORS = [
  '#1e293b', // slate-800 (Gris muy oscuro)
  '#334155', // slate-700 (Gris oscuro)
  '#475569', // slate-600 (Gris medio-oscuro)
  '#64748b', // slate-500 (Gris medio)
  '#94a3b8', // slate-400 (Gris claro)
  '#cbd5e1', // slate-300 (Gris muy claro)
]

/**
 * Detecta el tipo de datos y retorna el tipo de gráfico recomendado
 */
function detectChartType(data) {
  if (!data || data.length === 0) return null

  const keys = Object.keys(data[0])
  if (keys.length === 0) return null

  // Caso especial: 1 sola columna numérica → barra con key como categoría
  if (keys.length === 1) {
    const values = data.map(row => row[keys[0]]).filter(v => v != null)
    if (values.every(v => !isNaN(v) && v !== '')) return 'bar'
    return 'table'
  }

  // Contar columnas numéricas y de texto
  const numericColumns = []
  const textColumns = []
  const dateColumns = []

  keys.forEach(key => {
    const values = data.map(row => row[key]).filter(v => v != null)

    if (values.length === 0) return

    const allNumeric = values.every(v => !isNaN(v) && v !== '')
    const allDates = values.every(v => !isNaN(Date.parse(v)))
    const allText = values.every(v => typeof v === 'string')

    if (allDates) {
      dateColumns.push(key)
    } else if (allNumeric) {
      numericColumns.push(key)
    } else if (allText) {
      textColumns.push(key)
    }
  })

  // Lógica para detectar tipo de gráfico
  if (dateColumns.length > 0 && numericColumns.length > 0) {
    return 'line' // Series de tiempo
  }

  if (textColumns.length > 0 && numericColumns.length > 0) {
    if (data.length >= 2 && data.length <= 10 && numericColumns.length === 1) {
      return 'pie' // Pocas categorías con un valor (mínimo 2 para que el pie tenga sentido)
    }
    return 'bar' // Categorías vs valores (incluye 1 solo registro)
  }

  // Solo columnas numéricas sin texto → barra (usa keys como categorías)
  if (numericColumns.length > 0 && textColumns.length === 0 && dateColumns.length === 0) {
    return 'bar'
  }

  if (numericColumns.length >= 2 && data.length <= 12) {
    return 'pie' // Distribución
  }

  if (numericColumns.length >= 2 && data.length > 12) {
    return 'area' // Datos complejos
  }

  return 'table' // Fallback: tabla
}

/**
 * Extrae las columnas clave para el gráfico
 */
function extractChartColumns(data, chartType) {
  const keys = Object.keys(data[0])

  // Caso especial: 1 sola columna → xAxis sintético con el nombre de la key
  if (keys.length === 1 && chartType === 'bar') {
    return { xAxis: '__label__', yAxis: keys[0], singleColumn: true }
  }

  const numericColumns = []
  const textColumns = []
  const dateColumns = []

  keys.forEach(key => {
    const values = data.map(row => row[key]).filter(v => v != null)
    if (values.length === 0) return

    const allNumeric = values.every(v => !isNaN(v) && v !== '')
    const allDates = values.every(v => !isNaN(Date.parse(v)))
    const allText = values.every(v => typeof v === 'string')

    if (allDates) dateColumns.push(key)
    else if (allNumeric) numericColumns.push(key)
    else if (allText) textColumns.push(key)
  })

  if (chartType === 'pie') {
    return {
      label: textColumns[0] || numericColumns[0],
      value: numericColumns[0] || textColumns[0],
    }
  }

  if (chartType === 'line' || chartType === 'area') {
    return {
      xAxis: dateColumns[0] || textColumns[0] || numericColumns[0],
      yAxis: numericColumns.slice(0, 2),
    }
  }

  if (chartType === 'bar') {
    // Solo columnas numéricas sin texto → pivotar keys como categorías
    if (textColumns.length === 0 && dateColumns.length === 0 && numericColumns.length > 0) {
      return { xAxis: '__label__', yAxis: '__value__', pivotKeys: true }
    }
    return {
      xAxis: textColumns[0] || dateColumns[0] || numericColumns[0],
      yAxis: numericColumns[0],
    }
  }

  return {}
}

/**
 * Componente para gráfico de barras
 */
function BarChartComponent({ data, xAxis, yAxis, singleColumn, pivotKeys }) {
  // Formatear nombre de columna para mostrar como label legible
  const formatLabel = (key) =>
    key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())

  // Pre-procesar data según el caso
  const chartData = useMemo(() => {
    if (singleColumn) {
      const originalKey = Object.keys(data[0]).find(k => k !== '__label__') || 'valor'
      return data.map((row, i) => ({
        __label__: data.length === 1 ? formatLabel(originalKey) : `${formatLabel(originalKey)} #${i + 1}`,
        [originalKey]: Number(row[originalKey]) || 0,
      }))
    }
    if (pivotKeys) {
      const numericKeys = Object.keys(data[0]).filter(k => {
        const val = data[0][k]
        return val != null && !isNaN(val) && val !== ''
      })
      return numericKeys.map(key => ({
        __label__: formatLabel(key),
        __value__: Number(data[0][key]) || 0,
      }))
    }
    return data
  }, [data, singleColumn, pivotKeys])

  const actualYAxis = singleColumn
    ? Object.keys(data[0]).find(k => k !== '__label__') || 'valor'
    : yAxis

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 50 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey={xAxis}
          angle={-45}
          textAnchor="end"
          height={100}
          tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
          axisLine={{ stroke: '#cbd5e1' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
          axisLine={{ stroke: '#cbd5e1' }}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1)',
            padding: '12px'
          }}
          formatter={(value) => [value.toLocaleString?.() || value, '']}
          labelStyle={{ color: '#1e293b', fontWeight: 700, marginBottom: '4px' }}
          itemStyle={{ color: '#475569', fontWeight: 500 }}
          cursor={{ fill: '#f8fafc' }}
        />
        <Bar 
          dataKey={actualYAxis} 
          fill="#1e293b" 
          radius={[6, 6, 0, 0]} 
          activeBar={{ fill: '#475569' }}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

/**
 * Componente para gráfico de líneas
 */
function LineChartComponent({ data, xAxis, yAxis }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 50 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis
          dataKey={xAxis}
          angle={-45}
          textAnchor="end"
          height={100}
          tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
          axisLine={{ stroke: '#cbd5e1' }}
          tickLine={false}
        />
        <YAxis 
          tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} 
          axisLine={{ stroke: '#cbd5e1' }}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
            padding: '12px'
          }}
          labelStyle={{ color: '#1e293b', fontWeight: 700 }}
          itemStyle={{ fontWeight: 500 }}
          formatter={(value) => value.toLocaleString?.() || value}
        />
        <Legend iconType="circle" wrapperStyle={{ paddingTop: '20px' }} />
        {yAxis.map((key, idx) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={COLORS[idx % COLORS.length]}
            strokeWidth={3}
            dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
            activeDot={{ r: 6, strokeWidth: 0 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

/**
 * Componente para gráfico de área
 */
function AreaChartComponent({ data, xAxis, yAxis }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 50 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey={xAxis}
          angle={-45}
          textAnchor="end"
          height={100}
          tick={{ fontSize: 12 }}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
          formatter={(value) => value.toLocaleString?.() || value}
        />
        <Legend />
        {yAxis.map((key, idx) => (
          <Area
            key={key}
            type="monotone"
            dataKey={key}
            fill={COLORS[idx % COLORS.length]}
            stroke={COLORS[idx % COLORS.length]}
            fillOpacity={0.3}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  )
}

/**
 * Componente para gráfico de pie/donut
 */
function PieChartComponent({ data, label, value }) {
  // Limitar a máximo 8 segmentos para legibilidad
  const chartData = data.slice(0, 8)
  const hasMore = data.length > 8

  return (
    <div className="flex flex-col items-center gap-4">
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            labelLine={false}
            label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
            dataKey={value}
            nameKey={label}
            stroke="none"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e2e8f0',
              borderRadius: '12px',
              boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
              padding: '12px'
            }}
            labelStyle={{ color: '#1e293b', fontWeight: 700, display: 'none' }}
            itemStyle={{ color: '#1e293b', fontWeight: 600 }}
            formatter={(value, name) => [value.toLocaleString?.() || value, name]}
          />
          <Legend iconType="circle" />
        </PieChart>
      </ResponsiveContainer>
      {hasMore && (
        <p className="text-xs text-muted-foreground">
          Mostrando 8 de {data.length} categorías
        </p>
      )}
    </div>
  )
}

/**
 * Componente tabla simple (fallback)
 */
function TableComponent({ data }) {
  const [showAll, setShowAll] = useState(false)
  const displayData = showAll ? data : data.slice(0, 5)

  return (
    <div className="space-y-2">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              {Object.keys(data[0]).map(key => (
                <th key={key} className="px-4 py-2 text-left font-semibold text-foreground/80">
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, idx) => (
              <tr key={idx} className="border-b hover:bg-muted/60 transition-colors">
                {Object.values(row).map((val, vidx) => (
                  <td key={vidx} className="px-4 py-2 text-foreground/70">
                    {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="text-xs text-primary hover:text-primary/80 font-medium"
        >
          {showAll ? 'Ver menos' : `Ver ${data.length - 5} más`}
        </button>
      )}
    </div>
  )
}

/**
 * ChartRenderer - Componente principal
 */
export default function ChartRenderer({ data, title = 'Visualización de datos' }) {
  const [showChart, setShowChart] = useState(true)

  const chartType = useMemo(() => detectChartType(data), [data])
  const columns = useMemo(() => extractChartColumns(data, chartType), [data, chartType])

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No hay datos para visualizar
      </div>
    )
  }

  return (
    <div className="bg-slate-100 rounded-xl border border-slate-200 p-4 space-y-3 mt-2 transition-all duration-300">
      {title && (
        <button
          onClick={() => setShowChart(!showChart)}
          className="flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors w-full pb-2 border-b border-slate-100"
        >
          <BarChart3 className="w-5 h-5 text-slate-700" strokeWidth={2} />
          <span>{title}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ml-auto ${showChart ? 'rotate-180' : ''}`} />
        </button>
      )}

      {showChart && (
        <div className="w-full overflow-x-auto overflow-y-hidden pb-2">
          {chartType === 'bar' && <BarChartComponent data={data} {...columns} />}
          {chartType === 'line' && <LineChartComponent data={data} {...columns} />}
          {chartType === 'area' && <AreaChartComponent data={data} {...columns} />}
          {chartType === 'pie' && <PieChartComponent data={data} {...columns} />}
          {chartType === 'table' && <TableComponent data={data} />}

          {/* Información descriptiva */}
          <div className="text-sm font-medium text-slate-500 mt-6 pt-4 border-t border-slate-100 flex items-center justify-center">
            {chartType === 'bar' && <span className="flex items-center gap-2"><BarChart3 className="w-5 h-5 text-slate-900" /> Compara valores categóricos de tu consulta.</span>}
            {chartType === 'line' && <span className="flex items-center gap-2"><LineChartIcon className="w-5 h-5 text-slate-900" /> Evolución de los datos a lo largo del tiempo o progresión.</span>}
            {chartType === 'area' && <span className="flex items-center gap-2"><Activity className="w-5 h-5 text-slate-900" /> Volumen acumulativo de los resultados.</span>}
            {chartType === 'pie' && <span className="flex items-center gap-2"><PieChartIcon className="w-5 h-5 text-slate-900" /> Distribución porcentual sobre el total de la respuesta.</span>}
            {chartType === 'table' && <span className="flex items-center gap-2"><TableIcon className="w-5 h-5 text-slate-900" /> Tabla estructurada con todos los registros encontrados.</span>}
          </div>
        </div>
      )}
    </div>
  )
}
