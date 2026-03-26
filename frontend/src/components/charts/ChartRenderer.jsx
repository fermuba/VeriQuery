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
import { ChevronDown } from 'lucide-react'
import { useState } from 'react'

// Paleta de colores moderna y accesible
const COLORS = [
  '#8b5cf6', // púrpura
  '#06b6d4', // cyan
  '#f59e0b', // ámbar
  '#ec4899', // rosa
  '#10b981', // esmeralda
  '#6366f1', // índigo
  '#f97316', // naranja
  '#14b8a6', // verde azulado
]

/**
 * Detecta el tipo de datos y retorna el tipo de gráfico recomendado
 */
function detectChartType(data) {
  if (!data || data.length === 0) return null

  const keys = Object.keys(data[0])
  if (keys.length < 2) return null

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
function BarChartComponent({ data, xAxis, yAxis }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 50 }}>
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
        <Bar dataKey={yAxis} fill="#8b5cf6" radius={[8, 8, 0, 0]} />
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
    <div className="rounded-lg border border-border bg-card p-4 space-y-4">
      <button
        onClick={() => setShowChart(!showChart)}
        className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
      >
        <span>📊 {title}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${showChart ? 'rotate-180' : ''}`} />
      </button>

      {showChart && (
        <div className="w-full overflow-x-auto">
          {chartType === 'bar' && <BarChartComponent data={data} {...columns} />}
          {chartType === 'line' && <LineChartComponent data={data} {...columns} />}
          {chartType === 'area' && <AreaChartComponent data={data} {...columns} />}
          {chartType === 'pie' && <PieChartComponent data={data} {...columns} />}
          {chartType === 'table' && <TableComponent data={data} />}
        </div>
      )}
    </div>
  )
}
