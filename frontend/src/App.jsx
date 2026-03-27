import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGuard, Login } from './auth'
import AuthInitializer from './components/auth/AuthInitializer'
import AppLayout from './components/layout/AppLayout'
import ChatContainer from './components/chat/ChatContainer'
import DataPreviewPanel from './components/data/DataPreviewPanel'
import SecurityBadge from './components/security/SecurityBadge'
import WelcomeScreen from './components/layout/WelcomeScreen'
import DatabaseConfigPanel from './components/database/DatabaseConfigPanel'
import AuditLog from './components/data/AuditLog'
import { Activity, Settings } from 'lucide-react'
import { useAppStore } from './store/useAppStore'
import { useBackendConnection } from './hooks/useBackend'

function MainApp() {
  const { selectedDatabase, currentView } = useAppStore()
  const { isConnected, loading, error, backendStatus } = useBackendConnection()

  useEffect(() => {
    if (isConnected) {
      console.log('✅ VeriQuery ready - Backend connected')
    } else if (!loading) {
      console.warn('⚠️ Backend not connected:', error)
    }
  }, [isConnected, loading, error])

  return (
    <>
      <AppLayout rightPanel={<DataPreviewPanel />}>
        {isConnected ? (
          currentView === 'database' ? (
            <div className="p-8 h-full overflow-y-auto w-full max-w-5xl mx-auto scrollbar-thin">
              <DatabaseConfigPanel />
            </div>
          ) : currentView === 'audit' ? (
            <div className="p-8 h-full overflow-y-auto w-full max-w-5xl mx-auto scrollbar-thin space-y-6">
              <div>
                <h2 className="text-2xl font-semibold text-foreground">Registros de Auditoría</h2>
                <p className="text-sm text-foreground/60 mt-1">Historial de consultas y eventos del sistema</p>
              </div>
              <div className="bento-card p-6">
                <AuditLog />
              </div>
            </div>
          ) : currentView === 'monitoring' ? (
            <div className="p-8 h-full flex flex-col items-center justify-center text-muted-foreground w-full max-w-5xl mx-auto">
              <Activity className="w-16 h-16 mb-4 opacity-20" />
              <h2 className="text-xl font-semibold text-foreground mb-2">Monitoreo</h2>
              <p>Módulo en construcción. Aquí verás métricas de rendimiento y uso.</p>
            </div>
          ) : currentView === 'settings' ? (
            <div className="p-8 h-full flex flex-col items-center justify-center text-muted-foreground w-full max-w-5xl mx-auto">
              <Settings className="w-16 h-16 mb-4 opacity-20" />
              <h2 className="text-xl font-semibold text-foreground mb-2">Configuración</h2>
              <p>Módulo en construcción. Aquí podrás ajustar las preferencias del sistema.</p>
            </div>
          ) : selectedDatabase ? (
            <ChatContainer />
          ) : (
            <WelcomeScreen />
          )
        ) : (
          <div style={{ padding: '20px', textAlign: 'center' }}>
            {loading ? (
              <p>🔄 Conectando al backend...</p>
            ) : (
              <p style={{ color: 'red' }}>❌ Error: No se puede conectar al backend ({error})</p>
            )}
          </div>
        )}
      </AppLayout>
      <SecurityBadge />
    </>
  )
}

export default function App() {
  return (
    <AuthInitializer>
      <Routes>
        {/* Public route - Login */}
        <Route path="/login" element={<Login />} />

        {/* Callback route - Microsoft Entra ID redirect after login */}
        <Route path="/callback" element={<Login />} />

        {/* Protected route - Main app */}
        <Route
          path="/dashboard"
          element={
            <AuthGuard>
              <MainApp />
            </AuthGuard>
          }
        />

        {/* Redirect root to dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* Catch all - redirect to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthInitializer>
  )
}
