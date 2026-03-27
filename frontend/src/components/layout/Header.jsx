import { Shield, ShieldCheck, LogOut, User } from 'lucide-react'
import logo from '../../assets/logo.png'
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
    <header className="h-20 glass-surface border-b border-border flex items-center justify-between px-8 shrink-0 z-40">
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 bg-slate-900 rounded-lg flex items-center justify-center overflow-hidden shadow-sm">
          <img src={logo} alt="VeriQuery" className="w-7 h-7 object-contain" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-800 tracking-tight" style={{ fontFamily: 'Plus Jakarta Sans, sans-serif' }}>VeriQuery</h1>
          <p className="text-xs text-muted-foreground tracking-wide uppercase">Forensic Data Analysis</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-4 py-2 rounded-md bg-green-600/20 border border-green-600/30">
          <ShieldCheck className="w-5 h-5 text-green-700" strokeWidth={1.5} />
          <span className="text-sm font-medium text-green-700" style={{ fontFamily: 'Plus Jakarta Sans, sans-serif' }}>Sistema Protegido</span>
        </div>

        {/* User Menu */}
        {user && (
          <div className="relative z-50">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-slate-800/20 flex items-center justify-center">
                <User className="w-4 h-4 text-slate-800" strokeWidth={1.5} />
              </div>
              <span className="text-sm font-medium text-foreground">{user.name || 'Usuario'}</span>
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-2 w-48 rounded-md bg-white border border-border shadow-xl z-50">
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
