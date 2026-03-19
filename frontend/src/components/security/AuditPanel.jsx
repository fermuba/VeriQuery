import { ShieldAlert, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { useAppStore } from '../../store/useAppStore'

const EVENT_CFG = {
  success:    { icon: CheckCircle2, color: 'text-success' },
  failed:     { icon: XCircle,      color: 'text-destructive' },
  processing: { icon: Clock,        color: 'text-warning' },
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function AuditPanel() {
  const { auditEvents } = useAppStore()

  return (
    <div className="p-3 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-muted-foreground">
        <ShieldAlert size={13} />
        <span className="text-xs font-semibold uppercase tracking-wider">Log de Auditoría</span>
        <span className="ml-auto text-xs bg-muted px-1.5 py-0.5 rounded-full">{auditEvents.length}</span>
      </div>

      {auditEvents.length === 0 ? (
        <p className="text-xs text-muted-foreground text-center py-4">Sin eventos registrados</p>
      ) : (
        <div className="flex flex-col gap-1.5">
          {auditEvents.map(ev => {
            const cfg = EVENT_CFG[ev.status] ?? EVENT_CFG.processing
            const Icon = cfg.icon
            return (
              <div key={ev.id} className="flex items-start gap-2 px-2 py-2 rounded-lg bg-muted border border-border">
                <Icon size={13} className={`${cfg.color} shrink-0 mt-0.5`} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-foreground truncate">{ev.text}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{formatTime(ev.timestamp)}</p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
