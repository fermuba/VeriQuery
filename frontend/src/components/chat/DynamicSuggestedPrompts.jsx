import { Sparkles, TrendingUp, BarChart3, Users, Clock } from 'lucide-react'
import { motion } from 'framer-motion'

/**
 * DynamicSuggestedPrompts - Genera sugerencias dinámicas basadas en el schema
 * Las preguntas varían según qué tablas están disponibles
 */
export default function DynamicSuggestedPrompts({ tables = [], onSelect }) {
  
  // Generar sugerencias dinámicas basadas en tablas disponibles
  const generatePrompts = () => {
    const prompts = []
    
    // Detección de tipo de tabla y generación de preguntas relevantes
    const hasTableName = (name) => 
      tables.some(t => t.name.toLowerCase().includes(name.toLowerCase()))
    
    // Preguntas sobre VENTAS
    if (hasTableName('sales') || hasTableName('venta') || hasTableName('transaction')) {
      prompts.push({
        text: '¿Cuáles fueron las ventas del último año?',
        icon: TrendingUp,
        category: 'Ventas'
      })
      prompts.push({
        text: '¿Qué producto se vendió más?',
        icon: BarChart3,
        category: 'Ventas'
      })
    }
    
    // Preguntas sobre CLIENTES
    if (hasTableName('customer') || hasTableName('cliente')) {
      prompts.push({
        text: '¿Cuántos clientes nuevos en el último mes?',
        icon: Users,
        category: 'Clientes'
      })
      prompts.push({
        text: '¿Quién es el cliente que más gastó?',
        icon: Users,
        category: 'Clientes'
      })
    }
    
    // Preguntas sobre TENDENCIAS
    if (hasTableName('sales') || hasTableName('date') || hasTableName('time')) {
      prompts.push({
        text: '¿Cómo varían las ventas mes a mes?',
        icon: TrendingUp,
        category: 'Tendencias'
      })
    }
    
    // Preguntas sobre PRODUCTOS
    if (hasTableName('product')) {
      prompts.push({
        text: '¿Cuáles son los 10 productos más rentables?',
        icon: BarChart3,
        category: 'Productos'
      })
    }
    
    // Si no hay sugerencias específicas, mostrar genéricas
    if (prompts.length === 0) {
      prompts.push(
        { text: 'Resumen de datos', icon: BarChart3, category: 'General' },
        { text: 'Análisis de tendencias', icon: TrendingUp, category: 'General' },
        { text: 'Estadísticas principales', icon: Users, category: 'General' }
      )
    }
    
    return prompts
  }
  
  const prompts = generatePrompts()
  
  if (prompts.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-1">
        💡 Preguntas que puedes hacer:
      </div>
      
      <div className="flex flex-wrap gap-2">
        {prompts.map((prompt, index) => {
          const IconComponent = prompt.icon
          return (
            <motion.button
              key={prompt.text}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onSelect(prompt.text)}
              className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-border bg-card hover:bg-muted/60 hover:border-primary/40 hover:text-foreground transition-all duration-200 group cursor-pointer"
            >
              <IconComponent className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
              <span className="font-medium">{prompt.text}</span>
              <span className="text-xs text-muted-foreground/50 group-hover:text-primary/50">
                →
              </span>
            </motion.button>
          )
        })}
      </div>
      
      <div className="text-xs text-muted-foreground/60 px-1">
        O escribe tu propia pregunta abajo
      </div>
    </div>
  )
}
