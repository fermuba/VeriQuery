import { useState, useEffect } from 'react'
import { Database, RefreshCw, Info } from 'lucide-react'
import { motion } from 'framer-motion'

/**
 * DatabaseInfoHeader - Muestra información visual de la BD actual
 * Incluye: nombre, host, tablas, registros totales
 */
export default function DatabaseInfoHeader({ database }) {
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (database) {
      fetchDatabaseInfo()
    }
  }, [database])

  const fetchDatabaseInfo = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/database/info', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'demo'}`,
        }
      })
      if (response.ok) {
        const data = await response.json()
        setInfo(data)
      }
    } catch (err) {
      console.error('Error fetching DB info:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatCount = (count) => {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`
    return count.toString()
  }

  if (!database) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="px-6 py-3 bg-gradient-to-r from-primary/5 to-primary/10 border-b border-primary/20 rounded-lg mx-2 mt-2"
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
            <Database className="w-5 h-5 text-primary" />
          </div>
          
          <div className="flex-1">
            <p className="font-semibold text-sm text-foreground">
              {database.name || 'ContosoV210k'}
            </p>
            <p className="text-xs text-muted-foreground">
              {database.host || 'localhost'}:{database.port || 1433}
            </p>
          </div>
        </div>

        {/* Estadísticas */}
        <div className="flex gap-4 text-xs">
          {info && (
            <>
              <div className="text-center">
                <p className="font-semibold text-foreground">
                  {info.totalTables || '6'}
                </p>
                <p className="text-muted-foreground">Tablas</p>
              </div>
              
              <div className="h-8 w-px bg-border" />
              
              <div className="text-center">
                <p className="font-semibold text-foreground">
                  {formatCount(info.totalRecords || 532000)}
                </p>
                <p className="text-muted-foreground">Registros</p>
              </div>
              
              <div className="h-8 w-px bg-border" />
              
              <div className="text-center">
                <p className="font-semibold text-foreground">
                  {formatBytes(info.size || 150000000)}
                </p>
                <p className="text-muted-foreground">Tamaño</p>
              </div>
            </>
          )}
        </div>

        {/* Botón refrescar */}
        <button
          onClick={fetchDatabaseInfo}
          disabled={loading}
          className="p-2 rounded-lg hover:bg-primary/10 transition-colors disabled:opacity-50"
        >
          <RefreshCw 
            className={`w-4 h-4 text-primary ${loading ? 'animate-spin' : ''}`}
          />
        </button>
      </div>

      {/* Modo desarrollo/producción */}
      <div className="mt-2 flex items-center gap-2 text-xs">
        <div className="w-2 h-2 rounded-full bg-emerald-500" />
        <span className="text-muted-foreground">
          🟢 {database.environment === 'production' ? 'PRODUCCIÓN' : 'DESARROLLO'} - {database.environment === 'production' ? 'Azure SQL' : 'Docker Local'}
        </span>
      </div>
    </motion.div>
  )
}
