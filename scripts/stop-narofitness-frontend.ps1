param(
    [int[]]$Ports,
    [switch]$KeepDev,
    [switch]$KeepOtherTunnels,
    [switch]$Quiet
)

if (-not $Ports) {
    $Ports = if ($KeepDev) { @(3014, 4014) } else { @(5173, 3014, 4014) }
}

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

function Test-IsNarofitnessDevRoot {
    param(
        [string]$Name,
        [string]$Command
    )

    $name = ([string]$Name).ToLowerInvariant()
    $command = ([string]$Command).ToLowerInvariant()

    if ($name -eq "electron.exe" -and $command -match "node_env=development") {
        return $true
    }
    if ($name -ne "node.exe") {
        return $false
    }
    if ($command -match "run dev\b|dev:app|dev:web") {
        return $true
    }
    if ($command -match "concurrently" -and $command -match "5173") {
        return $true
    }
    if ($command -match "vite" -and $command -match "--port(?:=|\s+)5173") {
        return $true
    }
    return $false
}

function Get-ProtectedDevProcessIds {
    param([array]$AllProcesses)

    $protected = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($process in $AllProcesses) {
        if (Test-IsNarofitnessDevRoot -Name $process.Name -Command $process.CommandLine) {
            [void]$protected.Add([int]$process.ProcessId)
        }
    }
    do {
        $added = $false
        foreach ($process in $AllProcesses) {
            if ($protected.Contains([int]$process.ParentProcessId) -and -not $protected.Contains([int]$process.ProcessId)) {
                [void]$protected.Add([int]$process.ProcessId)
                $added = $true
            }
        }
    } while ($added)
    return $protected
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
    $protectedDevIds = if ($KeepDev) {
        Get-ProtectedDevProcessIds -AllProcesses $allProcesses
    } else {
        [System.Collections.Generic.HashSet[int]]::new()
    }
    $candidateIds = @(
        $allProcesses | Where-Object {
            $processId = [int]$_.ProcessId
            if ($KeepDev -and $protectedDevIds.Contains($processId)) {
                return $false
            }
            $name = ([string]$_.Name).ToLowerInvariant()
            $command = ([string]$_.CommandLine).ToLowerInvariant()
            if ($KeepOtherTunnels -and $name -eq "cloudflared.exe") {
                return $false
            }
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
