import Header from './Header'
import { useAppStore } from '../../store/useAppStore'
import { LayoutDashboard, FileSearch, Database, Settings, Shield, Activity, PanelRightClose, PanelRightOpen } from 'lucide-react'
import { useState } from 'react'

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: 'Panel Principal' },
  { icon: FileSearch,      label: 'Registros de Auditoría' },
  { icon: Database,        label: 'Base de Datos' },
  { icon: Activity,        label: 'Monitoreo' },
  { icon: Settings,        label: 'Configuración' },
]

function Sidebar() {
  const [activeIndex, setActiveIndex] = useState(0)
  return (
    <aside className="w-[4.5rem] hover:w-60 transition-all duration-300 ease-[cubic-bezier(0.2,0,0,1)] border-r border-border glass-surface flex flex-col items-center py-5 group shrink-0 overflow-hidden z-10">
      <div className="w-11 h-11 rounded-lg bg-primary/10 flex items-center justify-center mb-7">
        <Shield className="w-6 h-6 text-primary" strokeWidth={1.5} />
      </div>
      <nav className="flex flex-col gap-1.5 w-full px-2">
        {NAV_ITEMS.map(({ icon: Icon, label }, i) => (
          <button
            key={label}
            onClick={() => setActiveIndex(i)}
            className={`flex items-center gap-3 px-3 py-3 rounded-md transition-all duration-200 text-left w-full ${
              i === activeIndex
                ? 'bg-[hsl(var(--sidebar-accent))] text-[hsl(var(--sidebar-accent-foreground))]'
                : 'text-[hsl(var(--sidebar-foreground))] hover:bg-muted hover:translate-x-0.5'
            }`}
          >
            <Icon className="w-5 h-5 shrink-0" strokeWidth={1.5} />
            <span className="text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              {label}
            </span>
          </button>
        ))}
      </nav>
    </aside>
  )
}

export default function AppLayout({ children, rightPanel }) {
  const { previewOpen, togglePreview } = useAppStore()

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-hidden flex flex-col min-w-0">
          {children}
        </main>

        <div className={`shrink-0 flex flex-col border-l border-border glass-surface transition-all duration-300 overflow-hidden ${previewOpen ? 'w-80 xl:w-96' : 'w-10'}`}>
          <div className="flex items-center justify-between px-3 py-3 border-b border-border">
            {previewOpen && <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Resultados</span>}
            <button onClick={togglePreview} className="p-1 rounded hover:bg-muted transition-colors ml-auto">
              {previewOpen
                ? <PanelRightClose size={15} className="text-muted-foreground" />
                : <PanelRightOpen  size={15} className="text-muted-foreground" />
              }
            </button>
          </div>
          {previewOpen && <div className="flex-1 overflow-y-auto scrollbar-thin">{rightPanel}</div>}
        </div>
      </div>
    </div>
  )
}
