# Script PowerShell para restaurar ContosoV210k desde el backup
# Uso: .\restore_db.ps1

param(
    [string]$ServerInstance = "localhost,1433",
    [string]$Username = "sa",
    [string]$Password = "VeriQuery26!",
    [string]$BackupPath = "C:\Users\Daniela\Desktop\forensicGuardian\database\assets\bak-ContosoV2-10k\dump\ContosoV210k.bak"
)

Write-Host "🔄 Restaurando ContosoV210k desde: $BackupPath" -ForegroundColor Cyan

# Crear conexión
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($Username, $securePassword)

# Conectar a SQL Server
try {
    [System.Reflection.Assembly]::LoadWithPartialName("Microsoft.SqlServer.SMO") | Out-Null
    $server = New-Object "Microsoft.SqlServer.Management.Smo.Server" $ServerInstance
    $server.ConnectionContext.LoginSecure = $false
    $server.ConnectionContext.Login = $Username
    $server.ConnectionContext.Password = $Password
    $server.ConnectionContext.Connect()
    
    Write-Host "✅ Conectado a SQL Server: $ServerInstance" -ForegroundColor Green
    
    # Restaurar base de datos
    $restore = New-Object "Microsoft.SqlServer.Management.Smo.Restore"
    $restore.Database = "ContosoV210k"
    $restore.Devices.AddDevice($BackupPath, "File")
    $restore.ReplaceDatabase = $true
    $restore.NoRecovery = $false
    
    # Ejecutar restauración
    $server.KillAllProcesses("ContosoV210k")
    $restore.SqlRestore($server)
    
    Write-Host "✅ Base de datos ContosoV210k restaurada exitosamente!" -ForegroundColor Green
    
    # Verificar
    $db = $server.Databases["ContosoV210k"]
    if ($db) {
        Write-Host "✅ BD Verificada: $($db.Name) - Estado: $($db.Status)" -ForegroundColor Green
        Write-Host "✅ Tablas en ContosoV210k:" -ForegroundColor Cyan
        $db.Tables | Where-Object { $_.IsSystemObject -eq $false } | Select-Object Name | ForEach-Object { Write-Host "  - $($_.Name)" }
    }
    
    $server.ConnectionContext.Disconnect()
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 ¡Listo! La BD está lista para usar." -ForegroundColor Green
