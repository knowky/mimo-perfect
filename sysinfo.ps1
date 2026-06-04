Get-CimInstance Win32_OperatingSystem | ForEach-Object {
    $cpu = (Get-CimInstance Win32_Processor).LoadPercentage
    $memTotal = [math]::Round($_.TotalVisibleMemorySize/1MB,1)
    $memFree = [math]::Round($_.FreePhysicalMemory/1MB,1)
    $memUsed = [math]::Round($memTotal - $memFree,1)
    $memPct = [math]::Round(($memUsed/$memTotal)*100,1)
    
    Write-Output "CPU: $cpu%"
    Write-Output "MEM: ${memUsed}GB/${memTotal}GB (${memPct}%)"
}

Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
    $sizeGB = [math]::Round($_.Size/1GB,1)
    $freeGB = [math]::Round($_.FreeSpace/1GB,1)
    $usedGB = [math]::Round(($_.Size - $_.FreeSpace)/1GB,1)
    $usedPct = [math]::Round(($_.Size - $_.FreeSpace)/$_.Size*100,1)
    Write-Output "DISK $($_.DeviceID) ${usedGB}GB/${sizeGB}GB (${usedPct}%)"
}

Write-Output "---TOP5 CPU---"
Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 5 Name, @{N='CPU';E={[math]::Round($_.CPU,1)}}, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}} | Format-Table -AutoSize | Out-String

Write-Output "---TOP5 MEM---"
Get-Process | Sort-Object -Property WorkingSet64 -Descending | Select-Object -First 5 Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}} | Format-Table -AutoSize | Out-String
