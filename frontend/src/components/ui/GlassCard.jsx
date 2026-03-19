export default function GlassCard({ children, className = '', onClick }) {
  return (
    <div
      onClick={onClick}
      className={`bento-card ${onClick ? 'cursor-pointer hover:bg-muted transition-colors' : ''} ${className}`}
    >
      {children}
    </div>
  )
}
