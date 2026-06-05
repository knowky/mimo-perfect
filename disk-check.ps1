Get-PSDrive -PSProvider FileSystem | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        UsedGB = [math]::Round($_.Used/1GB,1)
        FreeGB = [math]::Round($_.Free/1GB,1)
    }
} | Format-Table -AutoSize
