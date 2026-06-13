# NaroCatalog - arranque desarrollo local: Docker (API+BD) + Vite [+ Electron]

param(

    [switch]$WebOnly

)



$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

Set-Location $Root



$modeLabel = if ($WebOnly) { "navegador" } else { "Electron" }

Write-Host ""

Write-Host "  NaroCatalog - desarrollo local ($modeLabel)" -ForegroundColor Cyan

Write-Host "  API: http://127.0.0.1:8000  |  UI: http://127.0.0.1:5173" -ForegroundColor DarkGray

Write-Host ""



try {

    docker info 2>&1 | Out-Null

} catch {

    Write-Host "ERROR: Docker Desktop no esta en ejecucion. Abrelo y vuelve a ejecutar:" -ForegroundColor Red

    Write-Host "  npm run dev" -ForegroundColor Yellow

    exit 1

}



$Desktop = Join-Path $Root "apps\desktop"

$NodeModules = Join-Path $Desktop "node_modules"



if (-not (Test-Path $NodeModules)) {

    Write-Host "==> Primera vez: instalando dependencias de Electron/React..." -ForegroundColor Yellow

    npm ci --prefix $Desktop

    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

}



$Compose = @("-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")

$healthUrl = "http://127.0.0.1:8000/api/v1/health"



function Test-DockerServicesRunning {

    $running = @(docker compose @Compose ps --services --filter "status=running" 2>$null)

    return ($running -contains "api") -and ($running -contains "postgres")

}



function Test-ApiHealth {

    param([int]$TimeoutSec = 3)

    try {

        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec $TimeoutSec

        return ($r.StatusCode -eq 200)

    } catch {

        return $false

    }

}



function Show-ApiHealthStatus {

    try {

        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5

        if ($health.pdf_engine) {

            Write-Host "==> API OK - pdf engine: $($health.pdf_engine)" -ForegroundColor Green

        } else {

            Write-Host "==> API OK - pdf_engine no disponible; revisa WeasyPrint en Docker" -ForegroundColor Yellow

        }

    } catch {

        Write-Host "==> API OK" -ForegroundColor Green

    }

}



$dockerReady = Test-DockerServicesRunning



if ($dockerReady -and (Test-ApiHealth)) {

    Write-Host "==> Docker ya en ejecucion (postgres + api), omitiendo up" -ForegroundColor DarkGray

} elseif ($dockerReady) {

    Write-Host "==> Contenedores activos pero API no responde, esperando..." -ForegroundColor Yellow

    $ready = $false

    for ($i = 1; $i -le 45; $i++) {

        if (Test-ApiHealth) {

            $ready = $true

            break

        }

        Start-Sleep -Seconds 2

    }

    if (-not $ready) {

        Write-Host "ERROR: La API no respondio. Revisa: npm run docker:logs:api" -ForegroundColor Red

        exit 1

    }

} else {

    Write-Host "==> Levantando Postgres + API (Docker, hot-reload)..." -ForegroundColor Cyan

    docker compose @Compose up -d --wait

    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }



    Write-Host "==> Esperando API..." -ForegroundColor Cyan

    $ready = $false

    for ($i = 1; $i -le 45; $i++) {

        if (Test-ApiHealth) {

            $ready = $true

            break

        }

        Start-Sleep -Seconds 2

    }

    if (-not $ready) {

        Write-Host "ERROR: La API no respondio. Revisa: npm run docker:logs:api" -ForegroundColor Red

        exit 1

    }

}



Show-ApiHealthStatus



Write-Host "==> Migraciones: npm run db:migrate (no se aplican en dev)" -ForegroundColor DarkGray



& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "stop-narofitness-frontend.ps1") -Quiet



if ($WebOnly) {

    Write-Host "==> Iniciando Vite (navegador) - Ctrl+C para cerrar" -ForegroundColor Cyan

    Write-Host ""

    npm run dev:web --prefix $Desktop

} else {

    Write-Host "==> Iniciando Vite + Electron - Ctrl+C para cerrar" -ForegroundColor Cyan

    Write-Host ""

    npm run dev:app --prefix $Desktop

}


