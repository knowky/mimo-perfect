$os = Get-CimInstance Win32_OperatingSystem
$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$memUsedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB, 1)
$memTotalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$diskFree = [math]::Round((Get-PSDrive C).Free / 1GB, 1)
Write-Output "CPU: $cpu%"
Write-Output "Memory: ${memUsedGB}/${memTotalGB} GB"
Write-Output "Disk C Free: ${diskFree} GB"
Write-Output "---"
Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object ProcessName, MainWindowTitle | Format-Table -AutoSize
