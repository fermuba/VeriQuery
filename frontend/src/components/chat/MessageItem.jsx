import { useState } from 'react'
import { ChevronDown, Code, BookOpen, Table as TableIcon } from 'lucide-react'
import ConfidenceBadge from './ConfidenceBadge'

export default function MessageItem({ message }) {
  const [sqlOpen, setSqlOpen] = useState(false)
  const [explOpen, setExplOpen] = useState(false)
  const [dataOpen, setDataOpen] = useState(false)
  const { role, text, confidence, sql, explanation, data } = message

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
            <button
              onClick={() => setDataOpen(!dataOpen)}
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-primary transition-colors px-1 py-1.5"
            >
              <TableIcon className="w-4 h-4" strokeWidth={1.5} />
              Datos ({data.length} registros)
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${dataOpen ? 'rotate-180' : ''}`} />
            </button>
            {dataOpen && (
              <div className="bg-muted/40 rounded-md overflow-x-auto mt-1">
                <table className="w-full text-sm">
                  <thead className="bg-muted border-b">
                    <tr>
                      {data.length > 0 && Object.keys(data[0]).map(key => (
                        <th key={key} className="px-4 py-2 text-left font-semibold text-foreground/80">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.slice(0, 10).map((row, idx) => (
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
                {data.length > 10 && (
                  <div className="px-4 py-2 text-xs text-muted-foreground text-center">
                    Mostrando 10 de {data.length} registros
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
