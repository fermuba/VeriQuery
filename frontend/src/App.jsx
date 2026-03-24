import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthGuard, Login } from './auth'
import AuthInitializer from './components/auth/AuthInitializer'
import AppLayout from './components/layout/AppLayout'
import ChatContainer from './components/chat/ChatContainer'
import DataPreviewPanel from './components/data/DataPreviewPanel'
import SecurityBadge from './components/security/SecurityBadge'
import WelcomeScreen from './components/layout/WelcomeScreen'
import DebugPanel from './components/debug/DebugPanel'
import { useAppStore } from './store/useAppStore'
import { useBackendConnection } from './hooks/useBackend'

function MainApp() {
  const { selectedDatabase } = useAppStore()
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
          selectedDatabase ? <ChatContainer /> : <WelcomeScreen />
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
      <DebugPanel />
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
