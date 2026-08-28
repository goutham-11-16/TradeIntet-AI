$pptApp = New-Object -ComObject PowerPoint.Application
$pptPath = "d:\project files\CIT HACKFUSION\CIT Hackthon.pptx"
$outDir = "d:\project files\CIT HACKFUSION\slide_previews"

if (!(Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

$presentation = $pptApp.Presentations.Open($pptPath, $true, $false, $false)

$slideIndex = 1
foreach ($slide in $presentation.Slides) {
    $outPath = Join-Path $outDir "slide_$slideIndex.png"
    $slide.Export($outPath, "PNG", 1920, 1080)
    Write-Host "Exported slide $slideIndex to $outPath"
    $slideIndex++
}

$presentation.Close()
$pptApp.Quit()
Write-Host "All slides exported successfully!"
