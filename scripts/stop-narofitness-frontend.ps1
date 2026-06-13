param(
    [int[]]$Ports = @(5173, 3014, 4014),
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$Root = (Split-Path -Parent $PSScriptRoot).TrimEnd("\")
$StatePath = Join-Path $Root "temp\cloudflare-tunnels\state.json"
$stopped = [System.Collections.Generic.HashSet[int]]::new()

function Stop-ProcessIds {
    param([int[]]$ProcessIds)

    foreach ($processId in ($ProcessIds | Where-Object { $_ -gt 0 } | Sort-Object -Unique)) {
        if ($processId -eq $PID) {
            continue
        }
        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            [void]$stopped.Add($processId)
        } catch {
            if ($_.Exception.Message -notmatch "Cannot find a process|No se encuentra ningun proceso") {
                Write-Warning "No se pudo detener PID ${processId}: $($_.Exception.Message)"
            }
        }
    }
}

function Get-ListenerProcessIdsFromNetstat {
    param([int]$Port)

    $matches = netstat.exe -ano -p tcp | Select-String -Pattern "^\s*TCP\s+\S+:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$"
    return @($matches | ForEach-Object {
        if ($_.Matches.Count -gt 0) {
            [int]$_.Matches[0].Groups[1].Value
        }
    })
}

# First stop processes explicitly registered by tunnel:start.
if (Test-Path $StatePath) {
    try {
        $state = Get-Content -Path $StatePath -Raw | ConvertFrom-Json
        Stop-ProcessIds -ProcessIds @(
            $state.ui_tunnel_pid
            $state.api_tunnel_pid
            $state.vite_pid
        )
    } catch {
        Write-Warning "No se pudo leer el estado anterior del tunnel: $($_.Exception.Message)"
    }
    Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
}

# Then find any manually-started Narofitness Vite/Electron/cloudflared processes.
try {
    $allProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    $rootNeedle = $Root.ToLowerInvariant()
    $candidateIds = @(
        $allProcesses | Where-Object {
            $name = ([string]$_.Name).ToLowerInvariant()
            $command = ([string]$_.CommandLine).ToLowerInvariant()
            $isFrontendProcess = $name -in @("node.exe", "electron.exe", "cloudflared.exe")
            $belongsToWorkspace = $command.Contains($rootNeedle)
            $isFrontendProcess -and $belongsToWorkspace
        } | ForEach-Object { [int]$_.ProcessId }
    )

    # Stop children before parents so npm/concurrently wrappers exit cleanly.
    $descendantIds = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($candidateId in $candidateIds) {
        [void]$descendantIds.Add($candidateId)
    }
    do {
        $added = $false
        foreach ($process in $allProcesses) {
            if ($descendantIds.Contains([int]$process.ParentProcessId) -and -not $descendantIds.Contains([int]$process.ProcessId)) {
                [void]$descendantIds.Add([int]$process.ProcessId)
                $added = $true
            }
        }
    } while ($added)

    Stop-ProcessIds -ProcessIds @($descendantIds)
} catch {
    # CIM can be restricted in some shells. Fall back to Node/Electron listeners
    # on the project's known frontend ports.
    foreach ($port in $Ports) {
        $listenerIds = @()
        try {
            $listenerIds = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction Stop |
                Select-Object -ExpandProperty OwningProcess)
        } catch {
            $listenerIds = @(Get-ListenerProcessIdsFromNetstat -Port $port)
        }
        foreach ($listenerId in $listenerIds) {
            $process = Get-Process -Id $listenerId -ErrorAction SilentlyContinue
            if ($process -and $process.ProcessName -in @("node", "electron")) {
                Stop-ProcessIds -ProcessIds @([int]$process.Id)
            }
        }
    }
}

if (-not $Quiet) {
    if ($stopped.Count -gt 0) {
        Write-Host "==> Frontend Narofitness anterior detenido ($($stopped.Count) procesos)." -ForegroundColor Green
    } else {
        Write-Host "==> No habia procesos frontend Narofitness anteriores." -ForegroundColor DarkGray
    }
}
