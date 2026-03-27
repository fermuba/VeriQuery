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

// Paleta de colores sobria y coherente con el diseño
const PALETTE = {
  primary: '#37474f',      // Gris oscuro
  secondary: '#546e7a',    // Gris medio
  tertiary: '#78909c',     // Gris claro
  accent: '#90caf9',       // Azul claro
  success: '#66bb6a',      // Verde
  warning: '#ffa726',      // Naranja
  danger: '#ef5350',       // Rojo
}

// Array de colores para gráficos con múltiples series
const COLORS_ARRAY = [
  '#37474f', '#546e7a', '#78909c', '#90caf9',
  '#66bb6a', '#ffa726', '#ef5350', '#ab47bc'
]

/**
 * CustomTooltip - Tooltip personalizado para todos los gráficos
 */
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg">
      <p className="text-xs font-semibold text-gray-900 mb-1">{label}</p>
      {payload.map((entry, index) => (
        <p key={index} className="text-xs text-gray-700">
          <span style={{ color: entry.color }}>●</span> {entry.name}: <strong>{entry.value.toLocaleString?.() || entry.value}</strong>
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
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
          <XAxis 
            dataKey={xKey} 
            tick={{ fontSize: 12, fill: '#9e9e9e' }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12, fill: '#9e9e9e' }} />
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
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
          <XAxis 
            dataKey={xKey}
            tick={{ fontSize: 12, fill: '#9e9e9e' }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12, fill: '#9e9e9e' }} />
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
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
          <XAxis 
            dataKey={xKey}
            tick={{ fontSize: 12, fill: '#9e9e9e' }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12, fill: '#9e9e9e' }} />
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
