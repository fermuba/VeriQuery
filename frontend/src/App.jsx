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
import AuditPanel from './components/security/AuditPanel'
import { useAppStore } from './store/useAppStore'
import { useBackendConnection } from './hooks/useBackend'

function MainApp() {
  const { selectedDatabase, activeView } = useAppStore()
  const { isConnected, loading, error, backendStatus } = useBackendConnection()

  useEffect(() => {
    if (isConnected) {
      console.log('✅ VeriQuery ready - Backend connected')
    } else if (!loading) {
      console.warn('⚠️ Backend not connected:', error)
    }
  }, [isConnected, loading, error])

  const renderMainContent = () => {
    switch (activeView) {
      case 'audit':
        return <AuditPanel />
      case 'databases':
        return (
          <div className="flex-1 p-8 overflow-y-auto w-full">
               <DatabaseConfigPanel />
          </div>
        )
      case 'monitoring':
        return (
          <div className="flex-1 flex items-center justify-center p-8 text-center text-muted-foreground w-full">
            El dashboard de Monitoreo aún está en construcción.
          </div>
        )
      case 'dashboard':
      default:
        return isConnected ? (
          selectedDatabase ? <ChatContainer /> : <WelcomeScreen />
        ) : (
          <div style={{ padding: '20px', textAlign: 'center', width: '100%' }}>
            {loading ? (
              <p>🔄 Conectando al backend...</p>
            ) : (
              <p style={{ color: 'red' }}>❌ Error: No se puede conectar al backend ({error})</p>
            )}
          </div>
        )
    }
  }

  return (
    <>
      <AppLayout rightPanel={activeView === 'dashboard' ? <DataPreviewPanel /> : null}>
        {renderMainContent()}
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
