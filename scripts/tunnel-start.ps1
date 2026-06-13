param(
    [ValidateRange(1024, 65535)]
    [int]$UiPort = 3014,
    [ValidateRange(10, 120)]
    [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Desktop = Join-Path $Root "apps\desktop"
$RuntimeDir = Join-Path $Root "temp\cloudflare-tunnels"
$RunId = "{0}-{1}" -f (Get-Date -Format "yyyyMMdd-HHmmss"), ([guid]::NewGuid().ToString("N").Substring(0, 8))
$StatePath = Join-Path $RuntimeDir "state.json"
$ApiLog = Join-Path $RuntimeDir "api-tunnel-$RunId.log"
$UiLog = Join-Path $RuntimeDir "ui-tunnel-$RunId.log"
$ViteLog = Join-Path $RuntimeDir "vite-$RunId.log"
$HealthUrl = "http://127.0.0.1:8000/api/v1/health"
$completed = $false

trap {
    $message = $_.Exception.Message
    foreach ($managedProcess in @($uiTunnel, $apiTunnel, $viteWrapper)) {
        if ($managedProcess -and -not $managedProcess.HasExited) {
            Stop-Process -Id $managedProcess.Id -Force -ErrorAction SilentlyContinue
        }
    }
    & (Join-Path $PSScriptRoot "stop-narofitness-frontend.ps1") -Quiet
    Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
    [Console]::Error.WriteLine("ERROR: $message")
    exit 1
}

function Start-HiddenProcess {
    param(
        [string]$FileName,
        [string]$Arguments,
        [string]$WorkingDirectory
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FileName
    $startInfo.Arguments = $Arguments
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    return [System.Diagnostics.Process]::Start($startInfo)
}

function Wait-QuickTunnelUrl {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$LogPath,
        [int]$Timeout
    )

    $deadline = (Get-Date).AddSeconds($Timeout)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $LogPath) {
            $match = Select-String -Path $LogPath -Pattern "https://[-a-z0-9]+\.trycloudflare\.com" -AllMatches -ErrorAction SilentlyContinue |
                Select-Object -Last 1
            if ($match) {
                return $match.Matches[-1].Value
            }
        }
        if ($Process.HasExited) {
            throw "cloudflared termino antes de crear el tunnel. Revisa $LogPath"
        }
        Start-Sleep -Milliseconds 500
    }
    throw "Timeout esperando la URL de Cloudflare. Revisa $LogPath"
}

function Wait-TunnelRegistered {
    param(
        [System.Diagnostics.Process]$Process,
        [string]$LogPath,
        [int]$Timeout
    )

    $deadline = (Get-Date).AddSeconds($Timeout)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $LogPath) {
            $registered = Select-String -Path $LogPath -Pattern '"message":"Registered tunnel connection"' -Quiet -ErrorAction SilentlyContinue
            if ($registered) {
                return
            }
        }
        if ($Process.HasExited) {
            throw "cloudflared termino antes de registrar el tunnel. Revisa $LogPath"
        }
        Start-Sleep -Milliseconds 500
    }
    throw "Timeout esperando el registro del tunnel. Revisa $LogPath"
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$Timeout,
        [System.Diagnostics.Process]$Process = $null
    )

    $deadline = (Get-Date).AddSeconds($Timeout)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                return
            }
        } catch {
            # Retry while the local service or Cloudflare route becomes ready.
        }
        if ($Process -and $Process.HasExited) {
            throw "El proceso termino antes de responder en $Url"
        }
        Start-Sleep -Seconds 1
    }
    throw "Timeout esperando respuesta HTTP de $Url"
}

function Get-ListeningProcessId {
    param([int]$Port)

    try {
        return [int](Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop |
            Select-Object -First 1 -ExpandProperty OwningProcess)
    } catch {
        return 0
    }
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

& (Join-Path $PSScriptRoot "stop-narofitness-frontend.ps1") -Quiet
Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue

try {
    Wait-HttpOk -Url $HealthUrl -Timeout 10
} catch {
    throw "La API local no responde en $HealthUrl. Ejecuta primero npm run docker:up"
}

$cloudflared = (Get-Command cloudflared -ErrorAction Stop).Source
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
$cmd = (Get-Command cmd.exe -ErrorAction Stop).Source

Write-Host "==> Creando tunnel publico para la API..." -ForegroundColor Cyan
$apiTunnel = Start-HiddenProcess `
    -FileName $cloudflared `
    -Arguments "tunnel --url http://127.0.0.1:8000 --no-autoupdate --logfile `"$ApiLog`"" `
    -WorkingDirectory $Root
$apiPublicUrl = Wait-QuickTunnelUrl -Process $apiTunnel -LogPath $ApiLog -Timeout $TimeoutSeconds
Wait-TunnelRegistered -Process $apiTunnel -LogPath $ApiLog -Timeout $TimeoutSeconds

Write-Host "==> Iniciando Vite en segundo plano en el puerto $UiPort..." -ForegroundColor Cyan
$viteCommand = "set `"VITE_API_BASE=$apiPublicUrl`" && `"$npm`" run ui --prefix `"$Desktop`" -- --host 127.0.0.1 --port $UiPort --strictPort > `"$ViteLog`" 2>&1"
$viteWrapper = Start-HiddenProcess -FileName $cmd -Arguments "/d /s /c `"$viteCommand`"" -WorkingDirectory $Root
Wait-HttpOk -Url "http://127.0.0.1:$UiPort" -Timeout $TimeoutSeconds -Process $viteWrapper
$vitePid = Get-ListeningProcessId -Port $UiPort

Write-Host "==> Creando tunnel publico para el frontend..." -ForegroundColor Cyan
$uiTunnel = Start-HiddenProcess `
    -FileName $cloudflared `
    -Arguments "tunnel --url http://127.0.0.1:$UiPort --http-host-header 127.0.0.1:$UiPort --no-autoupdate --logfile `"$UiLog`"" `
    -WorkingDirectory $Root
$uiPublicUrl = Wait-QuickTunnelUrl -Process $uiTunnel -LogPath $UiLog -Timeout $TimeoutSeconds
Wait-TunnelRegistered -Process $uiTunnel -LogPath $UiLog -Timeout $TimeoutSeconds

$state = [ordered]@{
    started_at = (Get-Date).ToString("o")
    ui_port = $UiPort
    local_ui_url = "http://127.0.0.1:$UiPort"
    public_ui_url = $uiPublicUrl
    public_api_url = $apiPublicUrl
    vite_wrapper_pid = $viteWrapper.Id
    vite_pid = $vitePid
    ui_tunnel_pid = $uiTunnel.Id
    api_tunnel_pid = $apiTunnel.Id
    vite_log = $ViteLog
    ui_tunnel_log = $UiLog
    api_tunnel_log = $ApiLog
}
$state | ConvertTo-Json | Set-Content -Path $StatePath -Encoding UTF8

$completed = $true
Write-Host ""
Write-Host "==> Tunnel levantado y funcionando." -ForegroundColor Green
Write-Host "    App publica: $uiPublicUrl" -ForegroundColor Green
Write-Host "    API publica: $apiPublicUrl" -ForegroundColor DarkGray
Write-Host "    UI local:    http://127.0.0.1:$UiPort" -ForegroundColor DarkGray
Write-Host "    Detener:     npm run tunnel:stop" -ForegroundColor DarkGray
