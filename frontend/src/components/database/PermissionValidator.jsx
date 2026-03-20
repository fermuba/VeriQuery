import { useState } from 'react'
import { AlertCircle, CheckCircle2, Shield, Copy } from 'lucide-react'
import { motion } from 'framer-motion'

/**
 * PermissionValidator Component
 * Displays read-only permission validation results
 * Integrates with Azure Key Vault credential storage
 */

export default function PermissionValidator({ 
  permissions = null, 
  isLoading = false,
  onContinue = () => {},
  onCancel = () => {}
}) {
  const [copiedCode, setCopiedCode] = useState(null)

  if (!permissions) {
    return null
  }

  const { is_readonly, readonly_message, permission_details, warnings } = permissions

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopiedCode(id)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  // SQL Server read-only user creation
  const sqlServerCode = `CREATE LOGIN [readonly_user] WITH PASSWORD = 'StrongPassword123!';
USE [YourDatabase];
CREATE USER [readonly_user] FOR LOGIN [readonly_user];
ALTER ROLE [db_datareader] ADD MEMBER [readonly_user];`

  // PostgreSQL read-only user creation
  const postgresCode = `CREATE USER readonly_user WITH PASSWORD 'StrongPassword123!';
GRANT CONNECT ON DATABASE your_database TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;`

  // MySQL read-only user creation
  const mysqlCode = `CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'StrongPassword123!';
GRANT SELECT ON your_database.* TO 'readonly_user'@'%';
FLUSH PRIVILEGES;`

  const getDbTypeCode = (dbType) => {
    const type = dbType?.toLowerCase() || ''
    if (type.includes('postgres')) return postgresCode
    if (type.includes('sqlserver') || type.includes('mssql')) return sqlServerCode
    if (type.includes('mysql')) return mysqlCode
    return ''
  }

  const dbType = permission_details?.db_type || 'Unknown'
  const dbCode = getDbTypeCode(dbType)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      {/* Main Status Card */}
      <div className={`bento-card p-4 border-l-4 ${
        is_readonly 
          ? 'border-success bg-gradient-to-r from-success/5 to-transparent' 
          : 'border-warning bg-gradient-to-r from-warning/5 to-transparent'
      }`}>
        <div className="flex items-start gap-3">
          {is_readonly ? (
            <CheckCircle2 className="w-5 h-5 text-success mt-0.5 flex-shrink-0" strokeWidth={1.5} />
          ) : (
            <AlertCircle className="w-5 h-5 text-warning mt-0.5 flex-shrink-0" strokeWidth={1.5} />
          )}
          
          <div className="flex-1">
            <h3 className={`font-semibold ${is_readonly ? 'text-success' : 'text-warning'}`}>
              {is_readonly ? '✓ Read-Only Confirmed' : '⚠ Write Access Detected'}
            </h3>
            <p className="text-sm text-foreground/80 mt-1">
              {readonly_message}
            </p>
          </div>
        </div>
      </div>

      {/* Permission Details */}
      {permission_details?.checks && (
        <div className="bento-card p-4 space-y-2">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Shield className="w-4 h-4" strokeWidth={1.5} />
            Permission Checks
          </h4>
          
          <div className="space-y-2">
            {permission_details.checks.map((check, idx) => (
              <div 
                key={idx}
                className="flex items-center gap-3 text-sm p-2 rounded bg-muted/50"
              >
                <div className={`w-1.5 h-1.5 rounded-full ${
                  check.status?.includes('PASS') && !check.status?.includes('WARNING')
                    ? 'bg-success'
                    : check.status?.includes('FAIL')
                    ? 'bg-destructive'
                    : 'bg-warning'
                }`} />
                <span className="text-foreground/80 flex-1">{check.name}</span>
                <span className="text-foreground/60 text-xs">{check.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warning Message */}
      {!is_readonly && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="bento-card p-4 border-l-4 border-warning bg-warning/5 space-y-3"
        >
          <p className="text-sm text-foreground font-medium">
            For Forensic Data Guardian, we recommend using read-only database users. 
            Here's how to create one:
          </p>

          <div className="bg-background/50 rounded p-3 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold text-muted-foreground uppercase">
                {dbType} SQL
              </p>
              <button
                onClick={() => copyToClipboard(dbCode, 'db-code')}
                className="inline-flex items-center gap-1.5 px-2 py-1 text-xs rounded 
                  bg-muted hover:bg-muted/80 transition-colors text-foreground/80"
              >
                <Copy className="w-3 h-3" strokeWidth={2} />
                {copiedCode === 'db-code' ? 'Copied!' : 'Copy'}
              </button>
            </div>
            
            <pre className="text-xs overflow-x-auto bg-foreground/5 p-2 rounded border border-muted text-foreground/70">
              {dbCode}
            </pre>
          </div>

          <p className="text-xs text-foreground/70">
            Execute the SQL above in your database to create a read-only user, then update your connection.
          </p>
        </motion.div>
      )}

      {/* Warnings List */}
      {warnings && warnings.length > 0 && (
        <div className="bento-card p-4 space-y-2 border-l-4 border-warning">
          <p className="text-sm font-medium text-warning">Additional Warnings:</p>
          <ul className="space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx} className="text-sm text-foreground/80 flex gap-2">
                <span className="text-warning">•</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 justify-end pt-2">
        <button
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 rounded text-sm font-medium text-foreground 
            hover:bg-muted transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
        
        <button
          onClick={onContinue}
          disabled={isLoading}
          className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
            is_readonly
              ? 'bg-success text-success-foreground hover:bg-success/90'
              : 'bg-warning text-warning-foreground hover:bg-warning/90'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isLoading ? 'Processing...' : is_readonly ? 'Save to Key Vault' : 'Continue Anyway'}
        </button>
      </div>
    </motion.div>
  )
}
