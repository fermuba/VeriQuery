import { useState, useEffect } from 'react'
import { Plus, Database, Shield, Trash2, Eye, EyeOff } from 'lucide-react'
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
  const { userDatabases, fetchUserDatabases, deleteDatabase } = useAppStore()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedDb, setSelectedDb] = useState(null)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    fetchUserDatabases()
  }, [])

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
              className="bento-card p-4 space-y-3 hover:bg-muted/30 transition-colors cursor-pointer"
              onClick={() => {
                setSelectedDb(db)
                setShowDetails(!showDetails)
              }}
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

              {/* Details (Expandable) */}
              {showDetails && selectedDb && (selectedDb.db_name === db.db_name || selectedDb.name === db.name) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="pt-3 border-t border-border space-y-2"
                >
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <p className="text-foreground/60">Database</p>
                      <p className="font-medium text-foreground">{db.database}</p>
                    </div>
                    <div>
                      <p className="text-foreground/60">Last Verified</p>
                      <p className="font-medium text-foreground">
                        {db.last_verified ? new Date(db.last_verified).toLocaleDateString() : 'Never'}
                      </p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 justify-end pt-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleVerifyDatabase(db.db_name || db.name)
                      }}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium 
                        bg-muted hover:bg-muted/80 text-foreground transition-colors"
                    >
                      ✓ Verify
                    </button>
                  </div>
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
      <div className="bento-card p-4 bg-primary/5 border-l-4 border-primary space-y-2">
        <h4 className="font-semibold text-sm text-foreground flex items-center gap-2">
          <Shield className="w-4 h-4" strokeWidth={1.5} />
          Security Info
        </h4>
        <ul className="text-xs text-foreground/70 space-y-1">
          <li>✓ Credentials encrypted in Azure Key Vault</li>
          <li>✓ Read-only permissions automatically validated</li>
          <li>✓ Access logged for audit trails</li>
          <li>✓ No passwords stored locally</li>
        </ul>
      </div>
    </div>
  )
}
