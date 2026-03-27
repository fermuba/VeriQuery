import { useState } from 'react'
import { ChevronDown, Code, BookOpen, Table as TableIcon, AlertCircle } from 'lucide-react'
import ConfidenceBadge from './ConfidenceBadge'
import ClarificationOptions from './ClarificationOptions'
import ChartRenderer from '../charts/ChartRenderer'
import { useAppStore } from '../../store/useAppStore'

export default function MessageItem({ message }) {
  const [sqlOpen, setSqlOpen] = useState(false)
  const [explOpen, setExplOpen] = useState(false)
  const [dataOpen, setDataOpen] = useState(false)
  const { sendQuery, isLoading } = useAppStore()
  const { role, text, confidence, sql, explanation, data, clarification_options, decision } = message

  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] px-5 py-3.5 rounded-xl rounded-br-sm bg-primary text-primary-foreground text-sm leading-relaxed">
          {text}
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center shrink-0 mt-1">
        <span className="text-xs font-bold text-primary">VQ</span>
      </div>
      <div className="flex-1 space-y-2">
        <div className="flex items-start gap-3">
          <div className="bento-card px-5 py-3.5 text-sm text-foreground leading-relaxed flex-1">
            {text}
          </div>
          {confidence != null && <ConfidenceBadge score={confidence} />}
        </div>

        {/* Mostrar opciones de desambiguación si existen */}
        {decision === 'NECESITA_ACLARACION' && clarification_options && (
          <ClarificationOptions
            question={text}
            options={clarification_options}
            onSelect={(option) => {
              const clarificationText = typeof option === 'string' ? option : option.title
              sendQuery(clarificationText)
            }}
            loading={isLoading}
          />
        )}

        {sql && (
          <div className="rounded-lg overflow-hidden">
            <button
              onClick={() => setSqlOpen(!sqlOpen)}
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-primary transition-colors px-1 py-1.5"
            >
              <Code className="w-4 h-4" strokeWidth={1.5} />
              Ver SQL
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${sqlOpen ? 'rotate-180' : ''}`} />
            </button>
            {sqlOpen && (
              <div className="bg-muted/60 rounded-md px-4 py-3 mt-1">
                <pre className="text-sm font-mono text-foreground/80 whitespace-pre-wrap">{sql}</pre>
              </div>
            )}
          </div>
        )}

        {explanation && (
          <div className="rounded-lg overflow-hidden">
            <button
              onClick={() => setExplOpen(!explOpen)}
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-primary transition-colors px-1 py-1.5"
            >
              <BookOpen className="w-4 h-4" strokeWidth={1.5} />
              Explicación Técnica
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${explOpen ? 'rotate-180' : ''}`} />
            </button>
            {explOpen && (
              <div className="bg-muted/60 rounded-md px-4 py-3 mt-1">
                <p className="text-sm text-foreground/80 leading-relaxed">{explanation}</p>
              </div>
            )}
          </div>
        )}

        {data && Array.isArray(data) && data.length > 0 && (
          <div className="rounded-lg overflow-hidden">
            <ChartRenderer 
              data={data}
              title={`Datos (${data.length} registros)`}
            />
          </div>
        )}
      </div>
    </div>
  )
}
