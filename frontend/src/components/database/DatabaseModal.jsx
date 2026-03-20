import { motion, AnimatePresence } from 'framer-motion'
import DatabaseWizard from './DatabaseWizard'
import { X } from 'lucide-react'

/**
 * DatabaseModal Component
 * Modal container for DatabaseWizard
 * Provides clean overlay and close functionality
 */

export default function DatabaseModal({ 
  isOpen = false, 
  onClose = () => {},
  onSuccess = () => {}
}) {
  const handleSuccess = (config) => {
    onSuccess(config)
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-0 flex items-center justify-center z-50 p-4"
          >
            <div className="w-full max-w-2xl bg-background border border-border rounded-xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-border bg-muted/50">
                <h2 className="font-semibold text-foreground">Add Database Connection</h2>
                <button
                  onClick={onClose}
                  className="p-1 rounded hover:bg-muted transition-colors text-foreground/60 hover:text-foreground"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" strokeWidth={2} />
                </button>
              </div>

              {/* Content */}
              <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
                <DatabaseWizard
                  onSuccess={handleSuccess}
                  onCancel={onClose}
                />
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
