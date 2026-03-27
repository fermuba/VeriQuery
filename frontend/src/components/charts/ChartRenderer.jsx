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
import { ChevronDown, BarChart3 } from 'lucide-react'
import { useState } from 'react'

// Paleta de colores sobria y profesional (gris y tonos neutros)
const COLORS = [
  '#37474f', // Gris oscuro principal
  '#546e7a', // Gris medio
  '#78909c', // Gris claro
  '#90caf9', // Azul suave
  '#66bb6a', // Verde suave
  '#ffa726', // Naranja suave
  '#ef5350', // Rojo suave
  '#ab47bc', // Púrpura suave
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
    if (data.length <= 10 && numericColumns.length === 1) {
      return 'pie' // Pocas categorías con un valor
    }
    return 'bar' // Categorías vs valores
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
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 50 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
        <XAxis
          dataKey={xAxis}
          angle={-45}
          textAnchor="end"
          height={100}
          tick={{ fontSize: 12, fill: '#9e9e9e' }}
          axisLine={{ stroke: '#e0e0e0' }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#9e9e9e' }}
          axisLine={{ stroke: '#e0e0e0' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
          formatter={(value) => [value.toLocaleString?.() || value, '']}
          labelStyle={{ color: '#37474f', fontWeight: 600 }}
        />
        <Bar dataKey={actualYAxis} fill="#37474f" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/**
 * Componente para gráfico de líneas
 */
function LineChartComponent({ data, xAxis, yAxis }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 50 }}>
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
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={COLORS[idx % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
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
    <ResponsiveContainer width="100%" height={300}>
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
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value.toLocaleString?.() || value}`}
            outerRadius={100}
            fill="#8884d8"
            dataKey={value}
            nameKey={label}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            formatter={(value) => value.toLocaleString?.() || value}
          />
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
    <div className="rounded-lg bg-card space-y-3">
      {title && (
        <button
          onClick={() => setShowChart(!showChart)}
          className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors w-full"
        >
          <BarChart3 className="w-4 h-4 text-foreground" strokeWidth={2.5} />
          <span>{title}</span>
          <ChevronDown className={`w-4 h-4 transition-transform ml-auto ${showChart ? 'rotate-180' : ''}`} />
        </button>
      )}

      {showChart && (
        <div className="w-full overflow-x-auto">
          {chartType === 'bar' && <BarChartComponent data={data} {...columns} />}
          {chartType === 'line' && <LineChartComponent data={data} {...columns} />}
          {chartType === 'area' && <AreaChartComponent data={data} {...columns} />}
          {chartType === 'pie' && <PieChartComponent data={data} {...columns} />}
          {chartType === 'table' && <TableComponent data={data} />}

          {/* Información descriptiva */}
          <div className="text-xs text-muted-foreground mt-3 px-4 pb-2">
            {chartType === 'bar' && 'Gráfico de barras — Compara valores entre categorías'}
            {chartType === 'line' && 'Gráfico de líneas — Muestra tendencias en el tiempo'}
            {chartType === 'area' && 'Gráfico de área — Visualiza cambios acumulativos'}
            {chartType === 'pie' && 'Gráfico de pastel — Muestra proporciones del total'}
            {chartType === 'table' && 'Tabla — Datos estructurados en filas y columnas'}
          </div>
        </div>
      )}
    </div>
  )
}
