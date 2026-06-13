# Descarga y prepara PostgreSQL 16 portable para el instalador Windows.
param(
    [string[]]$Versions = @("16.6-1", "16.4-1", "16.2-1")
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DestBin = Join-Path $Root "packaging\postgres\bin"
$Marker = Join-Path $DestBin "initdb.exe"
$CacheDir = Join-Path $Root "packaging\.cache"
$Needed = @(
    "initdb.exe", "pg_ctl.exe", "createdb.exe",
    "pg_dump.exe", "pg_restore.exe", "postgres.exe", "psql.exe"
)

function Ensure-Dest {
    New-Item -ItemType Directory -Force -Path $DestBin, $CacheDir | Out-Null
}

if (Test-Path $Marker) {
    Write-Host "PostgreSQL portable OK: $DestBin" -ForegroundColor Green
    exit 0
}

Ensure-Dest
$downloaded = $false
$ZipPath = $null
$ExtractRoot = Join-Path $CacheDir "extract"

$MinZipBytes = 200MB

foreach ($ver in $Versions) {
    $ZipName = "postgresql-$ver-windows-x64-binaries.zip"
    $Url = "https://get.enterprisedb.com/postgresql/$ZipName"
    $candidate = Join-Path $CacheDir $ZipName
    Write-Host "Trying $Url ..." -ForegroundColor Cyan
    try {
        $need = $true
        if (Test-Path $candidate) {
            $len = (Get-Item $candidate).Length
            if ($len -ge $MinZipBytes) { $need = $false }
            else {
                Write-Host "  Incomplete cache ($len bytes), re-downloading..." -ForegroundColor Yellow
                Remove-Item $candidate -Force -ErrorAction SilentlyContinue
            }
        }
        if ($need) {
            if (Get-Command Start-BitsTransfer -ErrorAction SilentlyContinue) {
                Start-BitsTransfer -Source $Url -Destination $candidate -Description "PostgreSQL $ver"
            } else {
                Invoke-WebRequest -Uri $Url -OutFile $candidate -UseBasicParsing -TimeoutSec 1200
            }
        }
        if (-not (Test-Path $candidate) -or (Get-Item $candidate).Length -lt $MinZipBytes) {
            Remove-Item $candidate -Force -ErrorAction SilentlyContinue
            continue
        }
        $ZipPath = $candidate
        $downloaded = $true
        break
    } catch {
        Write-Host "  Failed: $_" -ForegroundColor Yellow
        Remove-Item $candidate -Force -ErrorAction SilentlyContinue
    }
}

if (-not $downloaded) {
    throw "Could not download PostgreSQL binaries. Check network or set manually in packaging/postgres/bin/"
}

$ExtractRoot = Join-Path $CacheDir ("extract-" + [guid]::NewGuid().ToString("n").Substring(0, 8))
New-Item -ItemType Directory -Force -Path $ExtractRoot | Out-Null

Write-Host "Extracting $ZipPath ..." -ForegroundColor Cyan
if (Get-Command tar -ErrorAction SilentlyContinue) {
    & tar -xf $ZipPath -C $ExtractRoot
} else {
    Expand-Archive -Path $ZipPath -DestinationPath $ExtractRoot -Force
}

$BinSource = Join-Path $ExtractRoot "pgsql\bin"
if (-not (Test-Path (Join-Path $BinSource "initdb.exe"))) {
    $initdb = Get-ChildItem -Path $ExtractRoot -Recurse -Filter "initdb.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($initdb) { $BinSource = $initdb.Directory.FullName }
}
if (-not (Test-Path (Join-Path $BinSource "initdb.exe"))) {
    throw "initdb.exe not found inside archive"
}

Write-Host "Copying from $BinSource" -ForegroundColor Cyan
cmd /c "xcopy /E /I /Y `"$BinSource`" `"$DestBin`"" | Out-Null

$LibDir = Join-Path (Split-Path $BinSource -Parent) "lib"
if (Test-Path $LibDir) {
    $LibDest = Join-Path $Root "packaging\postgres\lib"
    New-Item -ItemType Directory -Force -Path $LibDest | Out-Null
    cmd /c "xcopy /E /I /Y `"$LibDir`" `"$LibDest`"" | Out-Null
}

Remove-Item -Recurse -Force $ExtractRoot -ErrorAction SilentlyContinue

$missing = $Needed | Where-Object { -not (Test-Path (Join-Path $DestBin $_)) }
if ($missing) {
    Write-Host "Warning: missing tools: $($missing -join ', ')" -ForegroundColor Yellow
}

Write-Host "PostgreSQL portable ready: $DestBin" -ForegroundColor Green
