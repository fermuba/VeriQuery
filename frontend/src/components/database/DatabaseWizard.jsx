import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, AlertCircle, Check, Loader } from 'lucide-react'
import PermissionValidator from './PermissionValidator'

/**
 * DatabaseWizard Component
 * Manages database connection configuration workflow
 * Steps: 1. Input → 2. Validate → 3. Permissions → 4. Save to Key Vault
 */

export default function DatabaseWizard({ onSuccess = () => {}, onCancel = () => {} }) {
  const [step, setStep] = useState(1) // 1: Input, 2: Validation, 3: Permissions, 4: Success
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [permissions, setPermissions] = useState(null)
  const [savedConfig, setSavedConfig] = useState(null)

  const [formData, setFormData] = useState({
    name: '',
    db_type: 'sqlserver',
    host: '',
    port: '',
    database: '',
    username: '',
    password: ''
  })

  const dbTypeDefaults = {
    sqlserver: { port: 1433 },
    postgresql: { port: 5432 },
    mysql: { port: 3306 },
    sqlite: { port: null }
  }

  const handleDbTypeChange = (type) => {
    setFormData(prev => ({
      ...prev,
      db_type: type,
      port: dbTypeDefaults[type]?.port || ''
    }))
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleValidateAndCheck = async () => {
    setIsLoading(true)
    setError(null)

    try {
      // Step 1: Validate connection
      const testResponse = await fetch('http://localhost:8888/api/databases/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (!testResponse.ok) {
        throw new Error('Connection test failed. Check your credentials.')
      }

      // Step 2: Check permissions
      const permResponse = await fetch('http://localhost:8888/api/databases/credentials/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (!permResponse.ok) {
        throw new Error('Permission validation failed')
      }

      const permData = await permResponse.json()
      setPermissions(permData)
      setStep(3)

    } catch (err) {
      setError(err.message || 'An error occurred')
      setStep(1)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveToKeyVault = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8888/api/databases/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (!response.ok || !data.success) {
        throw new Error(data.message || 'Failed to save configuration')
      }

      setSavedConfig(data)
      setStep(4)
      setTimeout(() => onSuccess(data), 2000)

    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setStep(1)
    setError(null)
    setPermissions(null)
    setSavedConfig(null)
    setFormData({
      name: '',
      db_type: 'sqlserver',
      host: '',
      port: 1433,
      database: '',
      username: '',
      password: ''
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="max-w-2xl mx-auto"
    >
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-foreground flex items-center gap-2">
          <Database className="w-6 h-6" strokeWidth={1.5} />
          Database Configuration
        </h2>
        <p className="text-sm text-foreground/60 mt-1">
          Connect your database securely with Azure Key Vault
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex gap-2 mb-6">
        {[
          { num: 1, label: 'Input' },
          { num: 2, label: 'Validate' },
          { num: 3, label: 'Permissions' },
          { num: 4, label: 'Complete' }
        ].map(s => (
          <div key={s.num} className="flex-1">
            <div className={`flex items-center justify-center h-10 rounded font-semibold transition-all ${
              step >= s.num
                ? step === s.num
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-success text-success-foreground'
                : 'bg-muted text-muted-foreground'
            }`}>
              {step > s.num ? (
                <Check className="w-5 h-5" strokeWidth={2} />
              ) : (
                s.num
              )}
            </div>
            <p className="text-xs text-center text-foreground/60 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {/* Step 1: Input */}
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="bento-card p-6 space-y-4"
          >
            {/* Connection Name */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Connection Name
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="e.g., production_db"
                className="w-full px-3 py-2 rounded border border-muted bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
              />
            </div>

            {/* Database Type */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Database Type
              </label>
              <div className="grid grid-cols-4 gap-2">
                {['sqlserver', 'postgresql', 'mysql', 'sqlite'].map(type => (
                  <button
                    key={type}
                    onClick={() => handleDbTypeChange(type)}
                    className={`px-3 py-2 rounded text-xs font-medium capitalize transition-colors ${
                      formData.db_type === type
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80 text-foreground'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Connection Details */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Host
                </label>
                <input
                  type="text"
                  name="host"
                  value={formData.host}
                  onChange={handleInputChange}
                  placeholder="server.database.windows.net"
                  className="w-full px-3 py-2 rounded border border-muted bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Port
                </label>
                <input
                  type="number"
                  name="port"
                  value={formData.port}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 rounded border border-muted bg-background text-foreground focus:outline-none focus:border-primary/50"
                />
              </div>
            </div>

            {/* Database & Username */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Database
                </label>
                <input
                  type="text"
                  name="database"
                  value={formData.database}
                  onChange={handleInputChange}
                  placeholder="MyDatabase"
                  className="w-full px-3 py-2 rounded border border-muted bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Username
                </label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  placeholder="username"
                  className="w-full px-3 py-2 rounded border border-muted bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded border border-muted bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 rounded bg-destructive/10 border border-destructive/30 flex gap-2">
                <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" strokeWidth={1.5} />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Buttons */}
            <div className="flex gap-3 justify-end pt-2">
              <button
                onClick={onCancel}
                className="px-4 py-2 rounded text-sm font-medium text-foreground 
                  hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleValidateAndCheck}
                disabled={isLoading || !formData.name || !formData.host || !formData.database || !formData.username || !formData.password}
                className="px-4 py-2 rounded text-sm font-medium bg-primary text-primary-foreground 
                  hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed 
                  flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Validating...
                  </>
                ) : (
                  'Validate & Check'
                )}
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Permissions */}
        {step === 3 && permissions && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-4"
          >
            <PermissionValidator
              permissions={permissions}
              isLoading={isLoading}
              onContinue={handleSaveToKeyVault}
              onCancel={handleReset}
            />
          </motion.div>
        )}

        {/* Step 4: Success */}
        {step === 4 && savedConfig && (
          <motion.div
            key="step4"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bento-card p-6 text-center space-y-4"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="flex justify-center"
            >
              <div className="w-16 h-16 rounded-full bg-success/10 flex items-center justify-center">
                <Check className="w-8 h-8 text-success" strokeWidth={1.5} />
              </div>
            </motion.div>
            
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                ✓ Configuration Saved
              </h3>
              <p className="text-sm text-foreground/60 mt-1">
                {savedConfig.message}
              </p>
            </div>

            {savedConfig.stored_in_keyvault && (
              <div className="bg-success/10 border border-success/30 rounded p-3 text-xs text-foreground/80">
                Credentials securely stored in Azure Key Vault
              </div>
            )}

            <button
              onClick={handleReset}
              className="px-4 py-2 rounded text-sm font-medium bg-primary text-primary-foreground 
                hover:bg-primary/90 transition-colors"
            >
              Configure Another Database
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
