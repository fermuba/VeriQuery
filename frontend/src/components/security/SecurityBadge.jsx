import { motion } from 'framer-motion'
import { ShieldCheck } from 'lucide-react'

export default function SecurityBadge() {
  return (
    <motion.div
      className="fixed bottom-6 right-6 z-50 bento-card px-4 py-2.5 flex items-center gap-2.5 cursor-default"
      animate={{ y: [0, -4, 0] }}
      transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
    >
      <ShieldCheck className="w-4 h-4 text-success" strokeWidth={1.5} />
      <div>
        <p className="text-[11px] font-semibold text-foreground">Validado</p>
        <p className="text-[9px] text-muted-foreground">Políticas de Gobernanza</p>
      </div>
    </motion.div>
  )
}
