# Build catalog-api.exe (PyInstaller only)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Building Python API (PyInstaller)" -ForegroundColor Cyan
Push-Location "$Root\apps\api"
if (-not (Test-Path ".venv-build")) {
    python -m venv .venv-build
}
& .\.venv-build\Scripts\pip install -q -r requirements.txt pyinstaller
& .\.venv-build\Scripts\playwright install chromium
& .\.venv-build\Scripts\pyinstaller --noconfirm "$Root\packaging\pyinstaller.spec" --distpath "$Root\packaging\dist" --workpath "$Root\packaging\build"
Pop-Location
Write-Host "API binary: packaging/dist/catalog-api.exe" -ForegroundColor Green
