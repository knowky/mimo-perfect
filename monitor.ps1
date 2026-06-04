# ClawX System Monitor Script
# Outputs JSON for agent consumption

$result = @{
    timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    timezone  = "Asia/Shanghai"
}

# 1. Active Windows
try {
    $windows = Get-Process | Where-Object { $_.MainWindowTitle -ne '' } |
        Select-Object ProcessName, MainWindowTitle, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}
    $result.activeWindows = @($windows | ForEach-Object {
        @{ process = $_.ProcessName; title = $_.MainWindowTitle; memMB = $_.MemMB }
    })
} catch { $result.activeWindows = @(); $result.winError = $_.Exception.Message }

# 2. CPU Usage
try {
    $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction Stop).CounterSamples.CookedValue
    $result.cpuPercent = [math]::Round($cpu, 1)
} catch { $result.cpuPercent = -1; $result.cpuError = $_.Exception.Message }

# 3. Memory Usage
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $totalMB = [math]::Round($os.TotalVisibleMemorySize/1KB)
    $freeMB = [math]::Round($os.FreePhysicalMemory/1KB)
    $usedMB = $totalMB - $freeMB
    $result.memory = @{
        totalGB = [math]::Round($totalMB/1024, 1)
        usedGB  = [math]::Round($usedMB/1024, 1)
        freeGB  = [math]::Round($freeMB/1024, 1)
        usedPercent = [math]::Round(($usedMB/$totalMB)*100, 1)
    }
} catch { $result.memory = @{}; $result.memError = $_.Exception.Message }

# 4. Disk Usage (C: drive)
try {
    $disk = Get-PSDrive C -ErrorAction Stop
    $result.disk = @{
        usedGB    = [math]::Round($disk.Used/1GB, 1)
        freeGB    = [math]::Round($disk.Free/1GB, 1)
        totalGB   = [math]::Round(($disk.Used+$disk.Free)/1GB, 1)
        freePercent = [math]::Round(($disk.Free/($disk.Used+$disk.Free))*100, 1)
    }
} catch { $result.disk = @{}; $result.diskError = $_.Exception.Message }

# 5. WeChat Status
try {
    $wechat = Get-Process WeChat -ErrorAction SilentlyContinue
    $result.wechat = if ($wechat) {
        @{ running = $true; pid = $wechat.Id; memMB = [math]::Round($wechat.WorkingSet64/1MB); cpuSec = [math]::Round($wechat.CPU,1) }
    } else {
        @{ running = $false }
    }
} catch { $result.wechat = @{ running = $false }; $result.wechatError = $_.Exception.Message }

# 6. Top 5 CPU processes
try {
    $topProcs = Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, @{N='CPU';E={[math]::Round($_.CPU,1)}}, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}
    $result.topProcesses = @($topProcs | ForEach-Object {
        @{ name = $_.Name; cpu = $_.CPU; memMB = $_.MemMB }
    })
} catch { $result.topProcesses = @() }

# 7. Recent files (last 5)
try {
    $recent = Get-ChildItem "$env:APPDATA\Microsoft\Windows\Recent" -File -ErrorAction Stop |
        Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime
    $result.recentFiles = @($recent | ForEach-Object {
        @{ name = $_.Name; time = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm") }
    })
} catch { $result.recentFiles = @() }

# 8. .learnings/ error files
try {
    $learnDir = "C:\Users\a1517\.openclaw\workspace\.learnings"
    if (Test-Path $learnDir) {
        $errs = Get-ChildItem $learnDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, LastWriteTime, Length
        $result.learnings = @($errs | ForEach-Object {
            @{ name = $_.Name; modified = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm"); sizeKB = [math]::Round($_.Length/1KB,1) }
        })
    } else { $result.learnings = @() }
} catch { $result.learnings = @() }

# 9. Uptime
try {
    $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $uptime = (Get-Date) - $boot
    $result.uptime = @{
        days  = $uptime.Days
        hours = $uptime.Hours
        mins  = $uptime.Minutes
        bootTime = $boot.ToString("yyyy-MM-dd HH:mm")
    }
} catch { $result.uptime = @{} }

# Output as JSON
$result | ConvertTo-Json -Depth 4 -Compress
