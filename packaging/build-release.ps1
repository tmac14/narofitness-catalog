# NaroCatalog — build API sidecar + Electron installer (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

& "$Root\packaging\setup-postgres.ps1"
& "$Root\packaging\build-api.ps1"

Write-Host "==> Building React UI" -ForegroundColor Cyan
Push-Location "$Root\apps\desktop"
npm ci
npm run build
Write-Host "==> Packaging Electron (NSIS)" -ForegroundColor Cyan
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
npm run electron:build
Pop-Location

Write-Host "Done. Check apps/desktop/release/" -ForegroundColor Green
