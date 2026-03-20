import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Database, Plus } from 'lucide-react'
import { useAppStore } from '../../store/useAppStore'
import MessageItem from './MessageItem'
import SuggestedPrompts from './SuggestedPrompts'
import AmbiguityResolver from './AmbiguityResolver'
import DatabaseConfigPanel from '../database/DatabaseConfigPanel'

export default function ChatContainer() {
  const [input, setInput] = useState('')
  const [lastQuestion, setLastQuestion] = useState('')
  const [showDatabasePanel, setShowDatabasePanel] = useState(true)
  const { messages, isLoading, sendQuery } = useAppStore()
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isLoading) return
    setLastQuestion(text)
    setShowDatabasePanel(false)
    setInput('')
    sendQuery(text)
  }

  const handleAmbiguitySelect = (clarification) => {
    console.log('Clarification selected:', clarification)
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
        {/* Mostrar panel de configuración de BD si no hay mensajes */}
        {messages.length === 0 && showDatabasePanel && (
          <div className="space-y-4">
            <div className="bento-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <Database className="w-5 h-5 text-primary" />
                <h3 className="font-semibold text-foreground">Configurar Base de Datos</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Seleccione una base de datos guardada o agregue una nueva para comenzar.
              </p>
              <DatabaseConfigPanel />
            </div>
          </div>
        )}

        {/* Mostrar resolver de ambigüedad si hay última pregunta */}
        {lastQuestion && !isLoading && (
          <AmbiguityResolver 
            question={lastQuestion} 
            onSelect={handleAmbiguitySelect}
            isLoading={isLoading}
          />
        )}

        {messages.map(msg => (
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
