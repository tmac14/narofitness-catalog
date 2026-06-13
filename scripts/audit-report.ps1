# Copia informes de auditoría desde el contenedor API a temp/
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet(
        "api1",
        "variants",
        "baseline",
        "page-import",
        "pr-i0",
        "pr-j",
        "pr-k-preflight",
        "pr-k-k0",
        "pr-k-k1-preflight"
    )]
    [string]$Name
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

New-Item -Force -ItemType Directory -Path (Join-Path $Root "temp") | Out-Null

function Copy-ApiFile {
    param([string]$ContainerPath, [string]$HostPath)
    docker compose cp "api:${ContainerPath}" $HostPath
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "==> $HostPath" -ForegroundColor Green
}

switch ($Name) {
    "api1" {
        Copy-ApiFile "/data/api1_validation_report.json" "temp/api1_validation_report.json"
    }
    "variants" {
        Copy-ApiFile "/data/variant_detection_audit_report.json" "temp/variant_detection_audit_report.json"
    }
    "baseline" {
        Copy-ApiFile "/data/category_seed_baseline.json" "temp/category_seed_baseline.json"
        Copy-ApiFile "/data/taxonomy_mapping_seed_baseline.json" "temp/taxonomy_mapping_seed_baseline.json"
    }
    "page-import" {
        $dest = Join-Path $Root "temp/audit/pages"
        New-Item -Force -ItemType Directory -Path $dest | Out-Null
        docker compose cp "api:/data/audit/pages/." $dest
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Write-Host "==> $dest" -ForegroundColor Green
    }
    "pr-i0" {
        Copy-ApiFile "/data/pr_i0_validation_report.json" "temp/pr_i0_validation_report.json"
    }
    "pr-j" {
        Copy-ApiFile "/data/pr_j_audit_report.json" "temp/pr_j_audit_report.json"
    }
    "pr-k-preflight" {
        Copy-ApiFile "/data/pr_k_preflight_report.json" "temp/pr_k_preflight_report.json"
    }
    "pr-k-k0" {
        Copy-ApiFile "/data/pr_k_k0_validation_report.json" "temp/pr_k_k0_validation_report.json"
    }
    "pr-k-k1-preflight" {
        Copy-ApiFile "/data/pr_k_k1_preflight_report.json" "temp/pr_k_k1_preflight_report.json"
    }
}

Write-Host "Informe copiado ($Name)." -ForegroundColor Cyan
