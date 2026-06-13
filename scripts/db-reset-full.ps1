# NaroCatalog - reset completo: migraciones + PIM seed + importación PDF

param(
    [switch]$WipeDatabase
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "  NaroCatalog - reset completo de base de datos" -ForegroundColor Cyan
Write-Host ""

try {
    docker info 2>&1 | Out-Null
} catch {
    Write-Host "ERROR: Docker Desktop no esta en ejecucion." -ForegroundColor Red
    exit 1
}

if ($WipeDatabase) {
    Write-Host "==> Borrando volumen PostgreSQL (datos completamente nuevos)..." -ForegroundColor Yellow
    docker compose -f docker-compose.yml -f docker-compose.dev.yml down
    $volume = docker volume ls -q --filter "name=pgdata"
    if ($volume) {
        docker volume rm $volume
    }
}

$Compose = @("-f", "docker-compose.yml", "-f", "docker-compose.dev.yml")

# Postgres first: API lifespan queries background_jobs and needs a migrated schema.
Write-Host "==> Levantando PostgreSQL..." -ForegroundColor Yellow
docker compose @Compose up -d postgres --wait
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Aplicando migraciones..." -ForegroundColor Yellow
docker compose @Compose run --rm -T api alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Levantando API..." -ForegroundColor Yellow
docker compose @Compose up -d --wait
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Sembrando datos PIM (taxonomía, specs, reglas)..." -ForegroundColor Yellow
docker compose @Compose exec -T -e PYTHONPATH=/app api python scripts/seed_pim.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Reseteando catálogo e importando desde PDF..." -ForegroundColor Yellow
docker compose @Compose exec -T -e PYTHONPATH=/app api python scripts/seed_catalog.py --fresh
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "  Reset completo finalizado." -ForegroundColor Green
Write-Host ""
