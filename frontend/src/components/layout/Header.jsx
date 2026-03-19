import { Shield, ShieldCheck } from 'lucide-react'

export default function Header() {
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

      <div className="flex items-center gap-2 px-4 py-2 rounded-md bg-success/10">
        <ShieldCheck className="w-5 h-5 text-success" strokeWidth={1.5} />
        <span className="text-sm font-medium text-success">Sistema Protegido</span>
      </div>
    </header>
  )
}
