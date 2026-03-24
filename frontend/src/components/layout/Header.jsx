import { Shield, ShieldCheck, LogOut, User } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showMenu, setShowMenu] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="h-20 glass-surface border-b border-border flex items-center justify-between px-8 shrink-0 z-10">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-md bg-primary flex items-center justify-center">
          <Shield className="w-6 h-6 text-primary-foreground" strokeWidth={1.5} />
        </div>
        <div>
          <h1 className="text-lg font-bold text-primary tracking-tight" style={{ fontFamily: 'Plus Jakarta Sans, sans-serif' }}>VeriQuery</h1>
          <p className="text-xs text-muted-foreground tracking-wide uppercase">Forensic Data Analysis</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-4 py-2 rounded-md bg-success/10">
          <ShieldCheck className="w-5 h-5 text-success" strokeWidth={1.5} />
          <span className="text-sm font-medium text-success">Sistema Protegido</span>
        </div>

        {/* User Menu */}
        {user && (
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <User className="w-4 h-4 text-primary" strokeWidth={1.5} />
              </div>
              <span className="text-sm font-medium text-foreground">{user.name || 'Usuario'}</span>
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-2 w-48 rounded-md bg-popover border border-border shadow-lg z-20">
                <div className="p-3 border-b border-border">
                  <p className="text-xs text-muted-foreground">Conectado como</p>
                  <p className="text-sm font-medium text-foreground truncate">{user.email}</p>
                </div>
                <button
                  onClick={() => {
                    setShowMenu(false)
                    handleLogout()
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" strokeWidth={1.5} />
                  <span>Cerrar sesión</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
