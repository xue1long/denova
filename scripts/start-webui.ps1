[CmdletBinding()]
param(
    [switch]$SkipBrowser
)

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\')
$logDirectory = Join-Path $repoRoot 'log'
$stateFilePattern = 'dev-windows-*.json'
$localGo = Join-Path $env:USERPROFILE '.local\go\bin\go.exe'
$corepackPnpm = Join-Path $env:ProgramFiles 'nodejs\node_modules\corepack\shims\pnpm.cmd'
$backendPort = 8080
$frontendPort = 5173
$frontendUrl = "http://127.0.0.1:$frontendPort/"
$backendUrl = "http://127.0.0.1:$backendPort"

function Resolve-RequiredCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        [string]$FallbackPath
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }
    if ($FallbackPath -and (Test-Path -LiteralPath $FallbackPath)) {
        return $FallbackPath
    }
    throw "Missing required command: $Name. Install the Windows dependency first."
}

function Stop-RepoDevProcesses {
    $snapshot = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, CommandLine
    $stateDirectory = $logDirectory
    $stateRecords = @()
    if (Test-Path -LiteralPath $stateDirectory) {
        foreach ($file in Get-ChildItem -LiteralPath $stateDirectory -Filter $stateFilePattern -File) {
            try {
                $state = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
                if ([string]::Equals([string]$state.repo_root, $repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $stateRecords += [pscustomobject]@{ Path = $file.FullName; State = $state }
                }
            }
            catch {
                Write-Warning "Ignoring invalid Windows development state file: $($file.FullName)"
            }
        }
    }

    $roots = [System.Collections.Generic.HashSet[int]]::new()
    $byId = @{}
    foreach ($p in $snapshot) { $byId[[int]$p.ProcessId] = $p }
    foreach ($r in $stateRecords) {
        $proc = $byId[[int]$r.State.process_id]
        if ($proc -and $proc.Name -eq 'go.exe' -and $proc.CommandLine -match '(?i)run\s+(?:"[^"]*[\\/]|[^\s"]*[\\/])?cmd[\\/]denova') {
            [void]$roots.Add([int]$proc.ProcessId)
        }
    }
    foreach ($node in $snapshot | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -match '[\\/]vite[\\/]bin[\\/]vite\.js' }) {
        $cur = $byId[[int]$node.ParentProcessId]
        while ($cur) {
            if ($cur.Name -in @('denova.exe', 'go.exe')) { [void]$roots.Add([int]$cur.ProcessId); break }
            $cur = $byId[[int]$cur.ParentProcessId]
        }
    }

    if ($roots.Count -eq 0) { return }
    $selected = [System.Collections.Generic.HashSet[int]]::new($roots)
    $queue = [System.Collections.Generic.Queue[int]]::new($roots)
    while ($queue.Count -gt 0) {
        $parent = $queue.Dequeue()
        foreach ($child in $snapshot | Where-Object { $_.ParentProcessId -eq $parent }) {
            if ($selected.Add([int]$child.ProcessId)) { $queue.Enqueue([int]$child.ProcessId) }
        }
    }
    foreach ($id in $selected | Sort-Object -Descending) {
        $p = Get-Process -Id $id -ErrorAction SilentlyContinue
        if ($p) { Stop-Process -InputObject $p -Force -ErrorAction SilentlyContinue }
    }
    foreach ($r in $stateRecords) {
        Remove-Item -LiteralPath $r.Path -Force -ErrorAction SilentlyContinue
    }
}

function Wait-HttpReady {
    param(
        [Parameter(Mandatory)][string]$Url,
        [Parameter(Mandatory)][int]$TimeoutSeconds
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -Method GET
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) { return $true }
        }
        catch {
            $code = $_.Exception.Response.StatusCode.value__
            if ($code -ge 200 -and $code -lt 500) { return $true }
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

try {
    $goExecutable = Resolve-RequiredCommand -Name 'go.exe' -FallbackPath $localGo
    $goBin = Split-Path -Parent $goExecutable
    $pnpmExecutable = Resolve-RequiredCommand -Name 'pnpm.cmd' -FallbackPath $corepackPnpm
    $pnpmBin = Split-Path -Parent $pnpmExecutable
    $env:Path = "$goBin;$pnpmBin;$env:Path"

    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

    Write-Host 'Stopping any prior Denova dev processes for this repo (if any)...'
    Stop-RepoDevProcesses
    Start-Sleep -Seconds 1

    Write-Host 'Starting backend (go run ./cmd/denova --dev --dev-mode --no-open)...'
    $goProcess = Start-Process `
        -FilePath $goExecutable `
        -ArgumentList @('run', './cmd/denova', '--dev', '--dev-mode', '--no-open') `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput (Join-Path $logDirectory 'dev-backend.out.log') `
        -RedirectStandardError  (Join-Path $logDirectory 'dev-backend.err.log') `
        -PassThru

    $statePath = Join-Path $logDirectory "dev-windows-$($goProcess.Id).json"
    @{ process_id = $goProcess.Id; repo_root = $repoRoot; stop_requested = $false } |
        ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8

    Write-Host "Waiting for backend at $backendUrl ..."
    if (-not (Wait-HttpReady -Url $backendUrl -TimeoutSeconds 60)) {
        throw "Backend did not become ready within 60 seconds. Check log\\dev-backend.err.log."
    }
    Write-Host 'Backend is ready.'

    Write-Host 'Starting Vite frontend (pnpm --dir web dev)...'
    $nodeModules = Join-Path $repoRoot 'web\node_modules'
    if (-not (Test-Path -LiteralPath $nodeModules)) {
        throw "web/node_modules is missing. Run 'pnpm install' inside web/ first."
    }
    Start-Process `
        -FilePath $pnpmExecutable `
        -ArgumentList @('--dir', 'web', 'dev', '--port', "$frontendPort", '--host', '127.0.0.1') `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput (Join-Path $logDirectory 'dev-frontend.out.log') `
        -RedirectStandardError  (Join-Path $logDirectory 'dev-frontend.err.log') `
        -PassThru | Out-Null

    Write-Host "Waiting for Vite at $frontendUrl ..."
    if (-not (Wait-HttpReady -Url $frontendUrl -TimeoutSeconds 60)) {
        throw "Vite did not become ready within 60 seconds. Check log\\dev-frontend.err.log."
    }
    Write-Host "Vite is ready. Opening $frontendUrl ..."
    if (-not $SkipBrowser) {
        Start-Process $frontendUrl | Out-Null
    }

    Write-Host ''
    Write-Host 'Denova is running. Close this window or press Ctrl+C to stop.'
    Write-Host "Backend log : log\\dev-backend.out.log"
    Write-Host "Frontend log: log\\dev-frontend.out.log"
    Write-Host ''

    while (-not $goProcess.HasExited) {
        Start-Sleep -Seconds 1
    }
}
finally {
    if ($statePath -and (Test-Path -LiteralPath $statePath)) {
        Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
    }
}
