import { useState, useEffect } from 'react'
import { Plus, Database, Shield, Trash2, Eye, EyeOff, Loader, Table, Columns, Layers } from 'lucide-react'
import { motion } from 'framer-motion'
import DatabaseModal from '../database/DatabaseModal'
import { API } from '../../config/endpoints'
import { useAppStore } from '../../store/useAppStore'

/**
 * DatabaseConfigPanel Component
 * Displays saved database configurations and allows CRUD operations
 * Uses Azure Key Vault for secure credential storage
 */

export default function DatabaseConfigPanel() {
  const { userDatabases, fetchUserDatabases, deleteDatabase, fetchDatabaseSchema } = useAppStore()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [expandedDb, setExpandedDb] = useState(null)
  const [schemas, setSchemas] = useState({})
  const [loadingSchema, setLoadingSchema] = useState(false)

  useEffect(() => {
    fetchUserDatabases()
  }, [])

  const handleToggleDb = async (dbName) => {
    if (expandedDb === dbName) {
      setExpandedDb(null)
      return
    }
    setExpandedDb(dbName)
    if (!schemas[dbName]) {
      setLoadingSchema(true)
      const schemaData = await fetchDatabaseSchema(dbName)
      if (schemaData) {
        setSchemas(prev => ({ ...prev, [dbName]: schemaData }))
      }
      setLoadingSchema(false)
    }
  }

  const handleAddDatabase = async (config) => {
    setIsModalOpen(false)
    await fetchUserDatabases()
  }

  const handleVerifyDatabase = async (dbName) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/databases/credentials/${dbName}/verify`,
        { method: 'POST' }
      )
      const data = await response.json()
      
      if (data.success) {
        // Update last_verified timestamp
        setDatabases(prev => prev.map(db => 
          db.name === dbName 
            ? { ...db, last_verified: new Date().toISOString() }
            : db
        ))
      }
    } catch (err) {
      console.error('Verification failed:', err)
    }
  }

  const handleDeleteDatabase = async (dbName) => {
    if (!confirm(`Delete database configuration "${dbName}"?`)) return

    try {
      await deleteDatabase(dbName)
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const getDbIcon = (dbType) => {
    const icons = {
      sqlserver: '🔵',
      postgresql: '🐘',
      mysql: '🐬',
      sqlite: '📄'
    }
    return icons[dbType?.toLowerCase()] || '📊'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-foreground flex items-center gap-2">
            <Database className="w-6 h-6" strokeWidth={1.5} />
            Database Connections
          </h2>
          <p className="text-sm text-foreground/60 mt-1">
            Manage secure database credentials with Azure Key Vault
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground 
            hover:bg-primary/90 transition-colors font-medium text-sm"
        >
          <Plus className="w-4 h-4" strokeWidth={2} />
          Add Database
        </button>
      </div>

      {/* Database List */}
      <div className="grid gap-3">
        {userDatabases.length === 0 ? (
          <div className="bento-card p-8 text-center">
            <Database className="w-12 h-12 text-muted-foreground mx-auto mb-3 opacity-50" strokeWidth={1.5} />
            <p className="text-foreground/60">No databases configured yet</p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-4 text-sm text-primary hover:underline font-medium"
            >
              Add your first database
            </button>
          </div>
        ) : (
          userDatabases.map((db, idx) => (
            <motion.div
              key={db.db_name || db.name}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`bento-card p-4 transition-colors cursor-pointer ${expandedDb === (db.db_name || db.name) ? 'bg-slate-50/50' : 'hover:bg-muted/30'}`}
              onClick={() => handleToggleDb(db.db_name || db.name)}
            >
              {/* Main Row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <span className="text-2xl">{getDbIcon(db.db_type)}</span>
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground">{db.db_name || db.name}</h3>
                    <p className="text-xs text-foreground/60">
                      {db.db_type.toUpperCase()} • {db.host}
                    </p>
                  </div>
                </div>

                {/* Status Badges & Actions */}
                <div className="flex items-center gap-2">
                  {db.is_readonly && (
                    <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium bg-success/10 text-success">
                      <Shield className="w-3 h-3" strokeWidth={2} />
                      Read-Only
                    </div>
                  )}
                  {db.stored_in_keyvault && (
                    <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium bg-primary/10 text-primary">
                      🔐 Vault
                    </div>
                  )}
                  {/* Delete Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteDatabase(db.db_name || db.name)
                    }}
                    className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors ml-2"
                    title="Delete database"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Expandable Schema Rendering */}
              {expandedDb === (db.db_name || db.name) && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  className="pt-4 mt-4 border-t border-slate-100 overflow-hidden"
                >
                  <div className="flex items-center justify-between mb-4 pl-1">
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4 text-slate-500" />
                      <h4 className="text-sm font-bold text-slate-800">Estructura de la Base de Datos</h4>
                    </div>
                    {/* Botón de Verificar original */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleVerifyDatabase(db.db_name || db.name)
                      }}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold 
                        bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-sm transition-colors"
                    >
                      ✓ Verificar Conexión
                    </button>
                  </div>
                  
                  {loadingSchema && !schemas[db.db_name || db.name] ? (
                    <div className="flex items-center gap-2 text-xs font-medium text-slate-500 py-6 px-4 bg-slate-50/50 rounded-lg justify-center border border-slate-100 border-dashed">
                      <Loader className="w-4 h-4 animate-spin text-slate-400" />
                      Analizando esquema (tablas y columnas)...
                    </div>
                  ) : schemas[db.db_name || db.name] && Object.keys(schemas[db.db_name || db.name]).length > 0 ? (
                    <div className="grid lg:grid-cols-2 gap-4 max-h-[500px] overflow-y-auto scrollbar-thin pr-2 pb-2">
                      {Object.entries(schemas[db.db_name || db.name]).map(([tableName, columns]) => (
                        <div key={tableName} className="rounded-xl border border-slate-200 overflow-hidden bg-white shadow-sm flex flex-col h-[280px]">
                          {/* Table Header */}
                          <div className="bg-slate-50/80 px-4 py-3 border-b border-slate-200 flex items-center justify-between shrink-0">
                            <h5 className="text-sm font-bold text-slate-800 flex items-center gap-2 truncate pr-2">
                              <Table className="w-4 h-4 text-slate-500 flex-shrink-0" />
                              <span className="truncate">{tableName}</span>
                            </h5>
                            <span className="text-[10px] font-semibold text-slate-500 bg-white px-2 py-0.5 rounded-md border border-slate-200 shadow-sm whitespace-nowrap">
                              {Object.keys(columns).length} cols
                            </span>
                          </div>
                          
                          {/* Columns List */}
                          <div className="flex-1 overflow-y-auto scrollbar-thin p-0">
                            <table className="w-full text-left text-xs">
                              <thead className="bg-white/95 backdrop-blur-sm sticky top-0 border-b border-slate-100 z-10">
                                <tr>
                                  <th className="px-4 py-2 font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Columna</th>
                                  <th className="px-4 py-2 font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Tipo</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100">
                                {Object.entries(columns).map(([colName, colType]) => (
                                  <tr key={colName} className="hover:bg-slate-50/50 transition-colors group">
                                    <td className="px-4 py-2 font-semibold text-slate-700 flex items-center gap-2 truncate max-w-[140px]" title={colName}>
                                      <Columns className="w-3 h-3 text-slate-200 group-hover:text-slate-400 transition-colors flex-shrink-0" />
                                      <span className="truncate">{colName}</span>
                                    </td>
                                    <td className="px-4 py-2 text-slate-500 font-mono text-[10px]">
                                      <span className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">{colType}</span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500 italic py-6 text-center bg-slate-50 rounded-lg border border-slate-100">
                      No se encontró información de tablas para esta base de datos o el usuario no tiene permisos configurados.
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          ))
        )}
      </div>

      {/* Modal */}
      <DatabaseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleAddDatabase}
      />

      {/* Info Box */}
      <div className="bento-card p-4 bg-primary/5 border-l-4 border-primary space-y-2 mt-4">
        <h4 className="font-semibold text-sm text-foreground flex items-center gap-2">
          <Shield className="w-4 h-4" strokeWidth={1.5} />
          Información de Seguridad
        </h4>
        <ul className="text-xs text-foreground/70 space-y-1">
          <li>✓ Las credenciales están encriptadas y protegidas remotamente.</li>
          <li>✓ Los permisos de solo lectura se validan automáticamente al consultar.</li>
          <li>✓ Cada acceso es registrado estrictamente para auditoría.</li>
          <li>✓ El esquema de la base se analiza mediante consultas no invasivas (Information Schema).</li>
        </ul>
      </div>
    </div>
  )
}
