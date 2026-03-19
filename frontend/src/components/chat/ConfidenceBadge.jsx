const badge = (score) => {
  if (score >= 85) return { color: 'bg-success/10 text-success border-success/20',      label: `${score}%` }
  if (score >= 65) return { color: 'bg-warning/10 text-warning border-warning/20',      label: `${score}%` }
  if (score >= 40) return { color: 'bg-warning/10 text-warning border-warning/20',      label: `${score}%` }
  return                   { color: 'bg-destructive/10 text-destructive border-destructive/20', label: `${score}%` }
}

export default function ConfidenceBadge({ score }) {
  const { color, label } = badge(score)
  return (
    <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-md border text-[11px] font-semibold ${color}`}>
      {label}
    </span>
  )
}
