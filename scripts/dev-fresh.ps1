# NaroCatalog - arranque fresh: reset BD + import PDF + catálogo de presentación + Electron

param(
    [switch]$WipeDatabase
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PdfName = "FDL .. Tarifa Mayorista 01-Febr-2026.pdf"
$PdfPath = Join-Path $Root "temp\$PdfName"

Write-Host ""
Write-Host "  NaroCatalog - arranque fresh (PDF + catálogo + app)" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $PdfPath)) {
    Write-Host "ERROR: PDF no encontrado en:" -ForegroundColor Red
    Write-Host "  $PdfPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Copia la tarifa FDL a temp/ antes de ejecutar dev:fresh." -ForegroundColor Yellow
    exit 1
}

$ResetArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "db-reset-full.ps1"))
if ($WipeDatabase) {
    $ResetArgs += "-WipeDatabase"
}

& powershell @ResetArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "desktop-run-local.ps1")
exit $LASTEXITCODE
