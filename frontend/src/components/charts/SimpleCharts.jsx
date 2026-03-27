/**
 * SimpleCharts - Componentes de gráficos simples y bonitos con Recharts
 * Tonos sobrios que combinan con el diseño de la app
 * 
 * Componentes incluidos:
 * - BarChart: Gráfico de barras
 * - LineChart: Gráfico de líneas  
 * - AreaChart: Gráfico de área con gradiente
 * - PieChart: Gráfico de pie/donut
 */

import {
  BarChart, Bar,
  LineChart, Line,
  AreaChart, Area,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'

// Paleta de colores monocromática (escala de grises)
const PALETTE = {
  primary: '#1e293b',      // slate-800
  secondary: '#334155',    // slate-700
  tertiary: '#475569',     // slate-600
  accent: '#64748b',       // slate-500
  success: '#94a3b8',      // slate-400 (repurposed for grayscale)
  warning: '#cbd5e1',      // slate-300 (repurposed for grayscale)
  danger: '#e2e8f0',       // slate-200 (repurposed for grayscale)
}

// Array de colores escala de grises para gráficos con múltiples series
const COLORS_ARRAY = [
  '#1e293b', '#334155', '#475569', '#64748b',
  '#94a3b8', '#cbd5e1', '#e2e8f0', '#f1f5f9'
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  
  return (
    <div className="bg-white/95 backdrop-blur-sm border border-slate-200 rounded-xl p-3 shadow-lg">
      <p className="text-xs font-bold text-slate-800 mb-1">{label}</p>
      {payload.map((entry, index) => (
        <p key={index} className="text-sm font-medium text-slate-600 flex items-center gap-2">
          <span style={{ color: entry.color }}>●</span> {entry.name}: <strong className="text-slate-900">{entry.value.toLocaleString?.() || entry.value}</strong>
        </p>
      ))}
    </div>
  )
}

/**
 * SimpleBarChart - Gráfico de barras
 * 
 * @param {Array} data - Datos a graficar
 * @param {String} xKey - Clave del eje X
 * @param {String|Array} yKey - Clave(s) del eje Y (puede ser string o array)
 * @param {String} title - Título del gráfico
 * @param {Number} height - Altura en píxeles (default: 300)
 * @param {String} color - Color personalizado (default: primary)
 */
export function SimpleBarChart({ data, xKey, yKey, title, height = 300, color = PALETTE.primary }) {
  const isMultiple = Array.isArray(yKey)
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      {title && <h3 className="text-sm font-semibold mb-4 text-foreground">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis 
            dataKey={xKey} 
            tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
            angle={-45}
            textAnchor="end"
            height={80}
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} 
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {isMultiple && <Legend />}
          {isMultiple ? (
            yKey.map((key, idx) => (
              <Bar key={key} dataKey={key} fill={COLORS_ARRAY[idx % COLORS_ARRAY.length]} radius={[4, 4, 0, 0]} />
            ))
          ) : (
            <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * SimpleLineChart - Gráfico de líneas
 * 
 * @param {Array} data - Datos a graficar
 * @param {String} xKey - Clave del eje X
 * @param {String|Array} yKey - Clave(s) del eje Y
 * @param {String} title - Título del gráfico
 * @param {Number} height - Altura en píxeles
 * @param {String} color - Color personalizado
 */
export function SimpleLineChart({ data, xKey, yKey, title, height = 300, color = PALETTE.primary }) {
  const isMultiple = Array.isArray(yKey)
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      {title && <h3 className="text-sm font-semibold mb-4 text-foreground">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis 
            dataKey={xKey}
            tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
            angle={-45}
            textAnchor="end"
            height={80}
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {isMultiple && <Legend />}
          {isMultiple ? (
            yKey.map((key, idx) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={COLORS_ARRAY[idx % COLORS_ARRAY.length]}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))
          ) : (
            <Line
              type="monotone"
              dataKey={yKey}
              stroke={color}
              strokeWidth={2.5}
              dot={{ fill: color, r: 4 }}
              activeDot={{ r: 6 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * SimpleAreaChart - Gráfico de área con gradiente
 * 
 * @param {Array} data - Datos a graficar
 * @param {String} xKey - Clave del eje X
 * @param {String|Array} yKey - Clave(s) del eje Y
 * @param {String} title - Título del gráfico
 * @param {Number} height - Altura en píxeles
 * @param {String} color - Color personalizado
 */
export function SimpleAreaChart({ data, xKey, yKey, title, height = 300, color = PALETTE.primary }) {
  const isMultiple = Array.isArray(yKey)
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      {title && <h3 className="text-sm font-semibold mb-4 text-foreground">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
          <defs>
            {isMultiple ? (
              yKey.map((key, idx) => (
                <linearGradient key={`grad-${key}`} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS_ARRAY[idx % COLORS_ARRAY.length]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS_ARRAY[idx % COLORS_ARRAY.length]} stopOpacity={0} />
                </linearGradient>
              ))
            ) : (
              <linearGradient id="gradArea" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            )}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis 
            dataKey={xKey}
            tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }}
            angle={-45}
            textAnchor="end"
            height={80}
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 12, fill: '#64748b', fontWeight: 500 }} 
            axisLine={{ stroke: '#cbd5e1' }}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          {isMultiple && <Legend />}
          {isMultiple ? (
            yKey.map((key, idx) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={COLORS_ARRAY[idx % COLORS_ARRAY.length]}
                fill={`url(#grad-${key})`}
                strokeWidth={2}
              />
            ))
          ) : (
            <Area
              type="monotone"
              dataKey={yKey}
              stroke={color}
              fill="url(#gradArea)"
              strokeWidth={2}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * SimplePieChart - Gráfico de pie/donut
 * 
 * @param {Array} data - Datos a graficar
 * @param {String} nameKey - Clave del nombre
 * @param {String} valueKey - Clave del valor
 * @param {String} title - Título del gráfico
 * @param {Number} height - Altura en píxeles
 * @param {Boolean} donut - Si es true, muestra como donut (default: true)
 */
export function SimplePieChart({ data, nameKey, valueKey, title, height = 300, donut = true }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      {title && <h3 className="text-sm font-semibold mb-4 text-foreground">{title}</h3>}
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={donut ? 60 : 0}
            outerRadius={100}
            paddingAngle={2}
            dataKey={valueKey}
            nameKey={nameKey}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS_ARRAY[index % COLORS_ARRAY.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>
      
      {/* Leyenda personalizada debajo */}
      <div className="mt-4 grid grid-cols-2 gap-2">
        {data.map((item, idx) => (
          <div key={item[nameKey]} className="flex items-center gap-2 text-xs">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: COLORS_ARRAY[idx % COLORS_ARRAY.length] }}
            />
            <span className="text-muted-foreground">{item[nameKey]}</span>
            <span className="font-semibold text-foreground ml-auto">{item[valueKey]}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Exportar paleta de colores para uso en otros componentes
 */
export { PALETTE, COLORS_ARRAY }
