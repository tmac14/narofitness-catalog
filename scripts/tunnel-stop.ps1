param(
    [switch]$StopAllTunnels
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$StatePath = Join-Path $Root "temp\cloudflare-tunnels\state.json"

$stopFrontendArgs = @{ Quiet = $true }
if (-not $StopAllTunnels) {
    $stopFrontendArgs.KeepOtherTunnels = $true
}

& (Join-Path $PSScriptRoot "stop-narofitness-frontend.ps1") @stopFrontendArgs

if (Test-Path $StatePath) {
    Remove-Item -LiteralPath $StatePath -Force
}

Write-Host "==> Tunnel Narofitness detenido." -ForegroundColor Green

