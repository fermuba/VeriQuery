/**
 * EJEMPLOS DE USO - SimpleCharts
 * 
 * Copia y pega estos ejemplos en tus componentes
 */

import { SimpleBarChart, SimpleLineChart, SimpleAreaChart, SimplePieChart } from './SimpleCharts'

/**
 * EJEMPLO 1: Gráfico de Barras Simple
 */
export function BarChartExample() {
  const data = [
    { mes: 'Enero', ventas: 4000, gastos: 2400 },
    { mes: 'Febrero', ventas: 3000, gastos: 1398 },
    { mes: 'Marzo', ventas: 2000, gastos: 9800 },
    { mes: 'Abril', ventas: 2780, gastos: 3908 },
    { mes: 'Mayo', ventas: 1890, gastos: 4800 },
    { mes: 'Junio', ventas: 2390, gastos: 3800 },
  ]

  return (
    <SimpleBarChart 
      data={data}
      xKey="mes"
      yKey="ventas"
      title="Ventas por Mes"
      height={300}
    />
  )
}

/**
 * EJEMPLO 2: Gráfico de Barras con Múltiples Series
 */
export function MultiBarChartExample() {
  const data = [
    { mes: 'Enero', ventas: 4000, gastos: 2400, ganancias: 1600 },
    { mes: 'Febrero', ventas: 3000, gastos: 1398, ganancias: 1602 },
    { mes: 'Marzo', ventas: 2000, gastos: 9800, ganancias: -7800 },
    { mes: 'Abril', ventas: 2780, gastos: 3908, ganancias: -1128 },
  ]

  return (
    <SimpleBarChart 
      data={data}
      xKey="mes"
      yKey={['ventas', 'gastos', 'ganancias']}
      title="Análisis Financiero"
      height={350}
    />
  )
}

/**
 * EJEMPLO 3: Gráfico de Líneas - Series de Tiempo
 */
export function LineChartExample() {
  const data = [
    { día: 'Lun', usuarios: 420, sesiones: 240 },
    { día: 'Mar', usuarios: 330, sesiones: 221 },
    { día: 'Mié', usuarios: 200, sesiones: 229 },
    { día: 'Jue', usuarios: 278, sesiones: 200 },
    { día: 'Vie', usuarios: 189, sesiones: 218 },
    { día: 'Sáb', usuarios: 239, sesiones: 250 },
    { día: 'Dom', usuarios: 349, sesiones: 210 },
  ]

  return (
    <SimpleLineChart 
      data={data}
      xKey="día"
      yKey={['usuarios', 'sesiones']}
      title="Actividad de Usuarios esta Semana"
      height={300}
    />
  )
}

/**
 * EJEMPLO 4: Gráfico de Área - Tendencias
 */
export function AreaChartExample() {
  const data = [
    { fecha: '01 Mar', accesos: 142 },
    { fecha: '02 Mar', accesos: 165 },
    { fecha: '03 Mar', accesos: 134 },
    { fecha: '04 Mar', accesos: 167 },
    { fecha: '05 Mar', accesos: 149 },
    { fecha: '06 Mar', accesos: 143 },
    { fecha: '07 Mar', accesos: 121 },
  ]

  return (
    <SimpleAreaChart 
      data={data}
      xKey="fecha"
      yKey="accesos"
      title="Accesos Diarios - Última Semana"
      height={280}
    />
  )
}

/**
 * EJEMPLO 5: Gráfico de Pie - Distribuciones
 */
export function PieChartExample() {
  const data = [
    { nombre: 'Crítico', valor: 2 },
    { nombre: 'Alto', valor: 5 },
    { nombre: 'Medio', valor: 12 },
    { nombre: 'Bajo', valor: 31 },
  ]

  return (
    <SimplePieChart 
      data={data}
      nameKey="nombre"
      valueKey="valor"
      title="Distribución de Riesgos"
      height={280}
      donut={true}
    />
  )
}

/**
 * CÓMO USAR EN TUS COMPONENTES:
 * 
 * 1. Importa el componente que necesites:
 *    import { SimpleBarChart, SimpleLineChart, SimpleAreaChart, SimplePieChart } from '@/components/charts/SimpleCharts'
 * 
 * 2. Prepara tus datos (array de objetos):
 *    const data = [
 *      { categoria: 'A', valor: 100 },
 *      { categoria: 'B', valor: 200 },
 *    ]
 * 
 * 3. Usa el componente:
 *    <SimpleBarChart 
 *      data={data}
 *      xKey="categoria"    // Campo para el eje X
 *      yKey="valor"        // Campo para el eje Y (o array de campos)
 *      title="Mi Gráfico"  // Opcional
 *      height={300}        // Opcional, default 300px
 *      color="#37474f"     // Opcional, color personalizado
 *    />
 * 
 * NOTAS:
 * - Los datos DEBEN ser un array de objetos
 * - xKey y yKey deben ser strings que correspondan a keys en los objetos
 * - Para múltiples series en bar/line/area, pasa un array en yKey
 * - Los colores se aplican automáticamente y son sobrios
 * - El componente es responsive (se adapta al ancho del contenedor)
 */
