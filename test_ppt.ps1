try {
    $ppt = New-Object -ComObject PowerPoint.Application
    Write-Host "PowerPoint COM Available: $($ppt.Version)"
    $ppt.Quit()
} catch {
    Write-Host "PowerPoint COM not available: $_"
}
