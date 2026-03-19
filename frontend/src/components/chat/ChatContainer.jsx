import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { useAppStore } from '../../store/useAppStore'
import MessageItem from './MessageItem'
import SuggestedPrompts from './SuggestedPrompts'

const MOCK_MESSAGES = [
  {
    id: 1,
    role: 'assistant',
    text: 'Bienvenido a VeriQuery. Estoy listo para analizar sus datos forenses. Seleccione una consulta sugerida o escriba su propia pregunta.',
    confidence: 99,
  },
  {
    id: 2,
    role: 'user',
    text: 'Detectar anomalías en los registros de acceso del último mes',
  },
  {
    id: 3,
    role: 'assistant',
    text: 'Se detectaron 3 anomalías en los registros de acceso. Se identificaron patrones inusuales de acceso fuera del horario laboral desde 2 direcciones IP no reconocidas. Anomalías detectadas en 4.2s.',
    confidence: 94,
    sql: `SELECT user_id, access_time, ip_address, action\nFROM access_logs\nWHERE access_time >= NOW() - INTERVAL '30 days'\n  AND (\n    EXTRACT(HOUR FROM access_time) NOT BETWEEN 8 AND 18\n    OR ip_address NOT IN (SELECT ip FROM trusted_ips)\n  )\nORDER BY access_time DESC;`,
    explanation: 'La consulta filtra los registros de acceso de los últimos 30 días, identificando aquellos que ocurrieron fuera del horario laboral (8:00-18:00) o desde direcciones IP no registradas en la lista de confianza. Los resultados se ordenan cronológicamente para facilitar la investigación forense.',
  },
  {
    id: 4,
    role: 'user',
    text: '¿Cuál es el nivel de riesgo de estas anomalías?',
  },
  {
    id: 5,
    role: 'assistant',
    text: 'Nivel de riesgo evaluado: MEDIO-ALTO. Dos de las tres anomalías provienen de la misma IP geolocalizada en una región no autorizada. Se recomienda revisión inmediata del acceso del usuario ID #4521. SQL query validado contra política de gobernanza.',
    confidence: 78,
    sql: `SELECT a.user_id, u.name, a.ip_address,\n  COUNT(*) as access_count,\n  MAX(a.risk_score) as max_risk\nFROM access_anomalies a\nJOIN users u ON a.user_id = u.id\nWHERE a.detected_at >= NOW() - INTERVAL '30 days'\nGROUP BY a.user_id, u.name, a.ip_address\nORDER BY max_risk DESC;`,
    explanation: 'Se cruzan las anomalías detectadas con la tabla de usuarios para obtener información del responsable. La puntuación de riesgo se calcula con un modelo que pondera: hora de acceso, geolocalización IP, frecuencia de intentos y tipo de recurso accedido.',
  },
]

export default function ChatContainer() {
  const [input, setInput] = useState('')
  const { messages, isLoading, sendQuery } = useAppStore()
  const bottomRef = useRef(null)

  const allMessages = messages.length === 0 ? MOCK_MESSAGES : messages

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading) return
    setInput('')
    sendQuery(text)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      <div className="px-6 py-4 border-b border-border shrink-0">
        <h2 className="text-base font-semibold text-foreground">Auditoría Interactiva</h2>
        <p className="text-xs text-muted-foreground">Consulta forense con IA</p>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-5 space-y-6">
        {allMessages.map(msg => (
          <MessageItem key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-md bg-primary/10 flex items-center justify-center shrink-0 mt-1">
              <Loader2 size={13} className="text-primary animate-spin" />
            </div>
            <div className="bento-card px-4 py-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 px-6 pb-5 pt-3 space-y-3 border-t border-border">
        <SuggestedPrompts onSelect={setInput} />
        <div className="bento-card flex items-center gap-3 px-4 py-3">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Escribe tu consulta forense..."
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/60 text-foreground"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="w-9 h-9 rounded-md bg-primary flex items-center justify-center hover:bg-primary/90 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            <Send className="w-4 h-4 text-primary-foreground" strokeWidth={1.5} />
          </button>
        </div>
      </div>
    </div>
  )
}
