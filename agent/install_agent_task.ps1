# Installs NetWatch Agent as a Windows Scheduled Task running at startup
param(
    [Parameter(Mandatory=$false)]
    [string]$TaskName = 'NetWatchAgent',

    [Parameter(Mandatory=$false)]
    [string]$ScriptPath,

    [Parameter(Mandatory=$false)]
    [string]$ServerUrl,

    [Parameter(Mandatory=$false)]
    [int]$DeviceId,

    [Parameter(Mandatory=$false)]
    [int]$IntervalMinutes = 1,

    [Parameter(Mandatory=$false)]
    [ValidateSet('install','uninstall','status')]
    [string]$Action = 'install'
)

$ErrorActionPreference = 'Stop'

# Determine script directory - handle cases where $PSScriptRoot is empty
if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    $ScriptDir = $PSScriptRoot
}

# Set default ScriptPath if not provided
if ([string]::IsNullOrEmpty($ScriptPath)) {
    $ScriptPath = Join-Path $ScriptDir 'netwatch_agent.ps1'
}

# Installer transcript logging
$InstallLog = Join-Path $ScriptDir 'install_agent.log'
$TranscriptStarted = $false
try {
    Start-Transcript -Path $InstallLog -Append -ErrorAction Stop | Out-Null
    $TranscriptStarted = $true
} catch {
    # If transcript cannot start (e.g., already running), ignore
}

function Update-AgentConfig {
    param([string]$ConfigPath, [string]$ServerUrl, [int]$DeviceId)

    if (-not (Test-Path $ConfigPath)) {
        Write-Host "Creating agent_config.json at $ConfigPath" -ForegroundColor Yellow
        $cfg = @{ server_url = $null; device_id = $null; services = @(); processes = @() }
        $cfg | ConvertTo-Json | Out-File -FilePath $ConfigPath -Encoding UTF8
    }

    $content = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    if ($PSBoundParameters.ContainsKey('ServerUrl')) { $content.server_url = $ServerUrl }
    if ($PSBoundParameters.ContainsKey('DeviceId')) { $content.device_id = $DeviceId }
    $content | ConvertTo-Json -Depth 5 | Out-File -FilePath $ConfigPath -Encoding UTF8
    Write-Host "Updated agent_config.json (server_url/device_id)" -ForegroundColor Green
}

try {
    switch ($Action) {
        'install' {
            if (-not (Test-Path $ScriptPath)) { throw "Script not found: $ScriptPath" }

        # Optionally update agent_config.json
        $cfgPath = Join-Path $ScriptDir 'agent_config.json'
        if ($PSBoundParameters.ContainsKey('ServerUrl') -or $PSBoundParameters.ContainsKey('DeviceId')) {
            Update-AgentConfig -ConfigPath $cfgPath -ServerUrl $ServerUrl -DeviceId $DeviceId
        }

            $exe = (Get-Command powershell.exe).Source
            # Use --once when running via a repeating trigger (PowerShell 5.1 compatible)
            if ($IntervalMinutes -gt 0) {
                $onceArg = ' --once'
            } else {
                $onceArg = ''
            }
            $args = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ScriptPath`"$onceArg"

            $taskAction   = New-ScheduledTaskAction -Execute $exe -Argument $args
            if ($IntervalMinutes -gt 0) {
                $start = (Get-Date).AddMinutes(1)
                # Create trigger with indefinite repetition (no RepetitionDuration = runs forever)
                $taskTrigger = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
            } else {
                $taskTrigger = New-ScheduledTaskTrigger -AtStartup
            }
            $taskPrincipal= New-ScheduledTaskPrincipal -UserId 'SYSTEM' -RunLevel Highest
            $taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

            $task = New-ScheduledTask -Action $taskAction -Trigger $taskTrigger -Principal $taskPrincipal -Settings $taskSettings -Description 'NetWatch Agent: posts local service/process status to NetWatch server.'

            try {
                Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force -ErrorAction Stop | Out-Null
                Write-Host "Installed scheduled task '$TaskName' to run every $IntervalMinutes minute(s) as SYSTEM" -ForegroundColor Green
                
                # Verify the task was actually created
                $verifyTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
                if ($verifyTask) {
                    Write-Host "Task verified in Task Scheduler. State: $($verifyTask.State)" -ForegroundColor Green
                    exit 0
                } else {
                    Write-Host "WARNING: Task registration reported success but task not found in Task Scheduler!" -ForegroundColor Red
                    exit 1
                }
            }
            catch {
                Write-Host "ERROR: Failed to register scheduled task: $($_.Exception.Message)" -ForegroundColor Red
                exit 1
            }
        }
        'uninstall' {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
            Write-Host "Uninstalled scheduled task '$TaskName'" -ForegroundColor Yellow
            exit 0
        }
        'status' {
            try {
                $t = Get-ScheduledTask -TaskName $TaskName
                Write-Host "Task '$TaskName': $($t.State)" -ForegroundColor Cyan
                $last = (Get-ScheduledTaskInfo -TaskName $TaskName)
                Write-Host "  Last Run: $($last.LastRunTime) Result: $($last.LastTaskResult)" -ForegroundColor Cyan
                exit 0
            } catch {
                Write-Host "Task '$TaskName' not found" -ForegroundColor Yellow
                exit 1
            }
        }
    }
}
finally {
    if ($TranscriptStarted) {
        try { Stop-Transcript | Out-Null } catch {}
    }
}
