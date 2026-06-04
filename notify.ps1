# Windows Toast Notification Script
param(
    [string]$Title = "ClawX",
    [string]$Message,
    [string]$Icon = "info"  # info, warning, error
)

# Load Windows Forms
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create notification
$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Information
$balloon.Visible = $true
$balloon.BalloonTipIcon = $Icon
$balloon.BalloonTipTitle = $Title
$balloon.BalloonTipText = $Message

# Show notification
$balloon.ShowBalloonTip(5000)

# Cleanup after 6 seconds
Start-Sleep -Seconds 6
$balloon.Dispose()
