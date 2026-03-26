import { motion } from 'framer-motion'
import { AlertCircle, HelpCircle } from 'lucide-react'

/**
 * ClarificationOptions - Muestra opciones cuando la pregunta es ambigua
 * Permite al usuario seleccionar cuál de las opciones quiere explorar
 */
export default function ClarificationOptions({ 
  question, 
  reason,
  options,
  onSelect,
  loading = false 
}) {
  if (!options || options.length === 0) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 rounded-lg p-4 space-y-3"
    >
      {/* Header */}
      <div className="flex items-start gap-2">
        <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-500 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="font-semibold text-amber-900 dark:text-amber-100 text-sm">
            Ambigüedad Detectada
          </h3>
          <p className="text-xs text-amber-800 dark:text-amber-200 mt-0.5">
            {reason || "Tu pregunta puede significar varias cosas. ¿Cuál de estas opciones te interesa?"}
          </p>
        </div>
      </div>

      {/* Opciones */}
      <div className="space-y-2 mt-3">
        {options.map((option, index) => (
          <motion.button
            key={index}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            onClick={() => onSelect(option)}
            disabled={loading}
            className="w-full p-3 text-left rounded-lg border border-amber-300 dark:border-amber-700/50 bg-white dark:bg-amber-950/30 hover:bg-amber-50 dark:hover:bg-amber-900/40 hover:border-amber-400 dark:hover:border-amber-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-amber-500 dark:bg-amber-400 mt-2 group-hover:bg-amber-600 dark:group-hover:bg-amber-300 transition-colors flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                  {typeof option === 'string' ? option : option.title}
                </p>
                {typeof option === 'object' && option.description && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {option.description}
                  </p>
                )}
              </div>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Helper text */}
      <div className="flex items-center gap-2 pt-2 border-t border-amber-200 dark:border-amber-900/50">
        <HelpCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-500 flex-shrink-0" />
        <p className="text-xs text-amber-700 dark:text-amber-200">
          Selecciona una opción para continuar
        </p>
      </div>
    </motion.div>
  )
}
