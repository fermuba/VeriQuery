import { Sparkles } from 'lucide-react'

const PROMPTS = [
  'Resumen de asistencias',
  'Detectar anomalías',
  'Verificar integridad de datos',
  'Análisis de patrones de acceso',
  'Transacciones sospechosas',
]

export default function SuggestedPrompts({ onSelect }) {
  return (
    <div className="flex flex-wrap gap-2">
      {PROMPTS.map(p => (
        <button
          key={p}
          onClick={() => onSelect(p)}
          className="px-3.5 py-2 text-sm font-medium rounded-md border border-border text-muted-foreground hover:border-primary/40 hover:text-primary transition-all duration-200"
        >
          <Sparkles className="w-3.5 h-3.5 inline mr-1.5" strokeWidth={1.5} />
          {p}
        </button>
      ))}
    </div>
  )
}
