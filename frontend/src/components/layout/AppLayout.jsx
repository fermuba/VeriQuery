import Header from './Header'
import { useAppStore } from '../../store/useAppStore'
import { LayoutDashboard, FileSearch, Database, Settings, Shield, Activity, PanelRightClose, PanelRightOpen } from 'lucide-react'
import { useState } from 'react'

const NAV_ITEMS = [
  { id: 'chat',       icon: LayoutDashboard, label: 'Panel Principal' },
  { id: 'audit',      icon: FileSearch,      label: 'Registros de Auditoría' },
  { id: 'database',   icon: Database,        label: 'Base de Datos' },
  { id: 'monitoring', icon: Activity,        label: 'Monitoreo' },
  { id: 'settings',   icon: Settings,        label: 'Configuración' },
]

function Sidebar() {
  const { selectedDatabase, currentView, setCurrentView } = useAppStore()
  
  return (
    <aside className="w-[4.5rem] hover:w-60 transition-all duration-300 ease-[cubic-bezier(0.2,0,0,1)] border-r border-border glass-surface flex flex-col py-5 group shrink-0 overflow-hidden z-10">
      {/* Logo */}
      <div className="px-2 mb-6">
        <div className="w-11 h-11 rounded-lg bg-slate-800/10 flex items-center justify-center">
          <Shield className="w-6 h-6 text-slate-800" strokeWidth={1.5} />
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex flex-col gap-1.5 px-2 flex-1 min-w-0">
        {NAV_ITEMS.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setCurrentView(id)}
            className={`flex items-center gap-3 px-3 py-3 rounded-md transition-all duration-200 text-left whitespace-nowrap flex-shrink-0 ${
              currentView === id
                ? 'bg-slate-800/10 text-slate-800'
                : 'text-slate-600 hover:bg-muted hover:translate-x-0.5'
            }`}
          >
            <Icon className="w-5 h-5 flex-shrink-0 text-slate-800" strokeWidth={1.5} />
            <span className="text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-slate-800">
              {label}
            </span>
          </button>
        ))}
      </nav>

      {/* Selected Database Info */}
      {selectedDatabase && (
        <div className="px-2 py-4 border-t border-border mt-auto">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <p className="text-[10px] uppercase font-bold tracking-widest text-muted-foreground mb-2 px-1">Active Database</p>
            <div className="flex items-center gap-2 px-1">
              <Database className="w-3.5 h-3.5 text-blue-500" strokeWidth={2} />
              <p className="text-xs font-semibold text-foreground truncate">{selectedDatabase}</p>
            </div>
          </div>
        </div>
      )}
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
