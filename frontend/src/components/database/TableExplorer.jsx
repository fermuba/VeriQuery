import { useState, useEffect } from 'react'
import { ChevronDown, ChevronRight, Database, Eye, RefreshCw, List } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

/**
 * TableExplorer - Muestra las tablas disponibles en la BD actual
 * Permite explorar el schema y seleccionar tablas para consultar
 */
export default function TableExplorer({ onTableSelect }) {
  const [tables, setTables] = useState([])
  const [expandedTables, setExpandedTables] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Cargar tablas desde el backend
  useEffect(() => {
    fetchTables()
  }, [])

  const fetchTables = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch('http://localhost:8000/api/database/schema', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'demo'}`,
        }
      })
      
      if (!response.ok) throw new Error('Failed to fetch schema')
      
      const data = await response.json()
      setTables(data.tables || [])
    } catch (err) {
      console.error('Error fetching tables:', err)
      setError('No se pudo cargar las tablas')
    } finally {
      setLoading(false)
    }
  }

  const toggleTableExpand = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }))
  }

  const formatRecordCount = (count) => {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`
    return count.toString()
  }

  if (loading) {
    return (
      <div className="p-4 text-center text-muted-foreground text-sm">
        <div className="animate-spin inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full"></div>
        <p className="mt-2">Cargando tablas...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
        {error}
        <button 
          onClick={fetchTables}
          className="block mt-2 text-xs text-primary hover:underline"
        >
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="px-2 py-1 text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em] flex items-center gap-2">
        <List className="w-3 h-3" />
        Tablas Disponibles
      </div>
      
      <div className="space-y-1 max-h-96 overflow-y-auto">
        {tables.length === 0 ? (
          <div className="text-xs text-muted-foreground p-2 text-center">
            No hay tablas disponibles
          </div>
        ) : (
          tables.map(table => (
            <div key={table.name} className="group">
              <button
                onClick={() => toggleTableExpand(table.name)}
                className="w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-accent/50 transition-colors text-sm"
              >
                {expandedTables[table.name] ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
                
                <Database className="w-4 h-4 text-primary/60" />
                
                <span className="font-medium flex-1 text-left">{table.name}</span>
                
                <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                  {formatRecordCount(table.recordCount)}
                </span>
              </button>

              {/* Columnas expandidas */}
              <AnimatePresence>
                {expandedTables[table.name] && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="pl-6 pr-2 py-1 space-y-0.5 bg-accent/30 rounded-b border-l-2 border-primary/30">
                      {table.columns?.slice(0, 8).map(col => (
                        <div
                          key={col.name}
                          className="text-xs text-muted-foreground py-0.5 flex items-center justify-between hover:text-foreground transition-colors"
                        >
                          <span>• {col.name}</span>
                          <span className="text-xs bg-muted/50 px-1.5 py-0.5 rounded font-mono">
                            {col.type}
                          </span>
                        </div>
                      ))}
                      {table.columns?.length > 8 && (
                        <div className="text-xs text-muted-foreground/50 py-0.5 italic">
                          +{table.columns.length - 8} más...
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))
        )}
      </div>

      {/* Botón para refrescar */}
      <button
        onClick={fetchTables}
        className="w-full mt-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors p-2 rounded-lg hover:bg-accent/50 flex items-center justify-center gap-2"
      >
        <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
        Actualizar Schema
      </button>
    </div>
  )
}
