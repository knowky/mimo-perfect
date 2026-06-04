$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$os = Get-CimInstance Win32_OperatingSystem
$totalMem = [math]::Round($os.TotalVisibleMemorySize/1MB, 2)
$freeMem = [math]::Round($os.FreePhysicalMemory/1MB, 2)
$usedMem = [math]::Round($totalMem - $freeMem, 2)
$memPct = [math]::Round(($usedMem/$totalMem)*100, 1)
$disks = Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3'
Write-Host "CPU|$cpu"
Write-Host "MEM|$usedMem|$totalMem|$memPct"
foreach($d in $disks){
    $usedPct = [math]::Round(($d.Size - $d.FreeSpace)/$d.Size*100,1)
    $freeGB = [math]::Round($d.FreeSpace/1GB,1)
    $sizeGB = [math]::Round($d.Size/1GB,1)
    Write-Host "DISK|$($d.DeviceID)|$freeGB|$sizeGB|$usedPct"
}
