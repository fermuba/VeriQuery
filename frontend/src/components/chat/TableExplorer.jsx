import { useState } from 'react'
import { ChevronDown, Database, Table2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function TableExplorer({ tables = [], database = '' }) {
  const [expanded, setExpanded] = useState(true)

  if (!tables || tables.length === 0) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="w-64 bg-muted/50 border-r border-border flex flex-col max-h-screen overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-border space-y-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors"
        >
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-primary" />
            <span className="text-sm font-semibold truncate">{database || 'Base de Datos'}</span>
          </div>
          <ChevronDown
            className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        </button>

        {expanded && database && (
          <div className="text-xs text-muted-foreground space-y-1 pl-2">
            <p>📊 {tables.length} tablas disponibles</p>
            <p>📈 {tables.reduce((sum, t) => sum + (t.row_count || 0), 0).toLocaleString()} registros</p>
          </div>
        )}
      </div>

      {/* Tables List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <AnimatePresence>
          {expanded && tables.map((table, index) => (
            <motion.div
              key={table.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ delay: index * 0.05 }}
              className="p-3 rounded-lg hover:bg-muted transition-colors cursor-pointer group"
            >
              <div className="flex items-start gap-2">
                <Table2 className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                    {table.name}
                  </p>
                  {table.row_count !== undefined && (
                    <p className="text-xs text-muted-foreground">
                      {table.row_count.toLocaleString()} registros
                    </p>
                  )}
                  {table.column_count !== undefined && (
                    <p className="text-xs text-muted-foreground">
                      {table.column_count} columnas
                    </p>
                  )}
                </div>
              </div>

              {/* Columns preview */}
              {table.columns && table.columns.length > 0 && (
                <div className="mt-2 ml-6 space-y-1 text-xs text-muted-foreground max-h-24 overflow-y-auto">
                  {table.columns.slice(0, 5).map((col) => (
                    <div key={col} className="truncate">
                      <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
                        {col}
                      </code>
                    </div>
                  ))}
                  {table.columns.length > 5 && (
                    <div className="text-xs text-muted-foreground/70">
                      +{table.columns.length - 5} más
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-border text-xs text-muted-foreground">
        <p>💡 Haz clic en cualquier tabla para ver más detalles</p>
      </div>
    </motion.div>
  )
}
