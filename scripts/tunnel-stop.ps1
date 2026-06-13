$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $Root "temp\cloudflare-tunnels\state.json"

& (Join-Path $PSScriptRoot "stop-narofitness-frontend.ps1") -Quiet

if (Test-Path $StatePath) {
    Remove-Item -LiteralPath $StatePath -Force
}

Write-Host "==> Tunnel Narofitness detenido." -ForegroundColor Green

