const LEVELS = {
  high:   { color: 'bg-destructive/10 text-destructive border-destructive/30',  dot: 'bg-destructive' },
  medium: { color: 'bg-warning/10 text-warning border-warning/30',              dot: 'bg-warning' },
  low:    { color: 'bg-warning/10 text-warning border-warning/20',              dot: 'bg-warning' },
  safe:   { color: 'bg-success/10 text-success border-success/30',              dot: 'bg-success' },
}

export default function StatusIndicator({ level = 'safe', label, className = '' }) {
  const cfg = LEVELS[level] ?? LEVELS.safe
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium ${cfg.color} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {label}
    </span>
  )
}
