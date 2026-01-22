# NetWatch Production Startup Script
# This script starts all NetWatch services for production use

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action = 'start',
    
    [Parameter(Mandatory=$false)]
    [switch]$UseCelery = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NetWatch Production Manager" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ProjectRoot = $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$PidDir = Join-Path $ProjectRoot "pids"

# Create PID directory if it doesn't exist
if (-not (Test-Path $PidDir)) {
    New-Item -ItemType Directory -Path $PidDir | Out-Null
}

# Function to start web server
function Start-WebServer {
    Write-Host "Starting web server..." -ForegroundColor Yellow
    
    $webPid = Join-Path $PidDir "web.pid"
    
    if (Test-Path $webPid) {
        Write-Host "Web server is already running (PID: $(Get-Content $webPid))" -ForegroundColor Green
        return
    }
    
    # Start waitress server in background
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList "-m", "waitress", "--listen=*:8000", "netwatch.wsgi:application" `
        -WorkingDirectory $ProjectRoot `
        -PassThru `
        -WindowStyle Hidden
    
    $process.Id | Out-File $webPid
    Write-Host "Web server started (PID: $($process.Id))" -ForegroundColor Green
}

# Function to stop web server
function Stop-WebServer {
    Write-Host "Stopping web server..." -ForegroundColor Yellow
    
    $webPid = Join-Path $PidDir "web.pid"
    
    if (Test-Path $webPid) {
        $pid = Get-Content $webPid
        try {
            Stop-Process -Id $pid -Force
            Remove-Item $webPid
            Write-Host "Web server stopped" -ForegroundColor Green
        } catch {
            Write-Host "Web server process not found (may have already stopped)" -ForegroundColor Yellow
            Remove-Item $webPid -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "Web server is not running" -ForegroundColor Yellow
    }
}

# Function to start Celery worker
function Start-CeleryWorker {
    Write-Host "Starting Celery worker..." -ForegroundColor Yellow
    
    $workerPid = Join-Path $PidDir "celery_worker.pid"
    
    if (Test-Path $workerPid) {
        Write-Host "Celery worker is already running (PID: $(Get-Content $workerPid))" -ForegroundColor Green
        return
    }
    
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList "-m", "celery", "-A", "netwatch", "worker", "-l", "info", "--pool=solo" `
        -WorkingDirectory $ProjectRoot `
        -PassThru `
        -WindowStyle Hidden
    
    $process.Id | Out-File $workerPid
    Write-Host "Celery worker started (PID: $($process.Id))" -ForegroundColor Green
}

# Function to stop Celery worker
function Stop-CeleryWorker {
    Write-Host "Stopping Celery worker..." -ForegroundColor Yellow
    
    $workerPid = Join-Path $PidDir "celery_worker.pid"
    
    if (Test-Path $workerPid) {
        $pid = Get-Content $workerPid
        try {
            Stop-Process -Id $pid -Force
            Remove-Item $workerPid
            Write-Host "Celery worker stopped" -ForegroundColor Green
        } catch {
            Write-Host "Celery worker process not found" -ForegroundColor Yellow
            Remove-Item $workerPid -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "Celery worker is not running" -ForegroundColor Yellow
    }
}

# Function to start Celery beat
function Start-CeleryBeat {
    Write-Host "Starting Celery beat..." -ForegroundColor Yellow
    
    $beatPid = Join-Path $PidDir "celery_beat.pid"
    
    if (Test-Path $beatPid) {
        Write-Host "Celery beat is already running (PID: $(Get-Content $beatPid))" -ForegroundColor Green
        return
    }
    
    $process = Start-Process -FilePath $PythonExe `
        -ArgumentList "-m", "celery", "-A", "netwatch", "beat", "-l", "info" `
        -WorkingDirectory $ProjectRoot `
        -PassThru `
        -WindowStyle Hidden
    
    $process.Id | Out-File $beatPid
    Write-Host "Celery beat started (PID: $($process.Id))" -ForegroundColor Green
}

# Function to stop Celery beat
function Stop-CeleryBeat {
    Write-Host "Stopping Celery beat..." -ForegroundColor Yellow
    
    $beatPid = Join-Path $PidDir "celery_beat.pid"
    
    if (Test-Path $beatPid) {
        $pid = Get-Content $beatPid
        try {
            Stop-Process -Id $pid -Force
            Remove-Item $beatPid
            Write-Host "Celery beat stopped" -ForegroundColor Green
        } catch {
            Write-Host "Celery beat process not found" -ForegroundColor Yellow
            Remove-Item $beatPid -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "Celery beat is not running" -ForegroundColor Yellow
    }
}

# Function to show status
function Show-Status {
    Write-Host "Service Status:" -ForegroundColor Cyan
    Write-Host ""
    
    $webPid = Join-Path $PidDir "web.pid"
    if (Test-Path $webPid) {
        $pid = Get-Content $webPid
        try {
            $process = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "  Web Server: RUNNING (PID: $pid)" -ForegroundColor Green
        } catch {
            Write-Host "  Web Server: STOPPED (stale PID file)" -ForegroundColor Red
        }
    } else {
        Write-Host "  Web Server: STOPPED" -ForegroundColor Red
    }
    
    if ($UseCelery) {
        $workerPid = Join-Path $PidDir "celery_worker.pid"
        if (Test-Path $workerPid) {
            $pid = Get-Content $workerPid
            try {
                $process = Get-Process -Id $pid -ErrorAction Stop
                Write-Host "  Celery Worker: RUNNING (PID: $pid)" -ForegroundColor Green
            } catch {
                Write-Host "  Celery Worker: STOPPED (stale PID file)" -ForegroundColor Red
            }
        } else {
            Write-Host "  Celery Worker: STOPPED" -ForegroundColor Red
        }
        
        $beatPid = Join-Path $PidDir "celery_beat.pid"
        if (Test-Path $beatPid) {
            $pid = Get-Content $beatPid
            try {
                $process = Get-Process -Id $pid -ErrorAction Stop
                Write-Host "  Celery Beat: RUNNING (PID: $pid)" -ForegroundColor Green
            } catch {
                Write-Host "  Celery Beat: STOPPED (stale PID file)" -ForegroundColor Red
            }
        } else {
            Write-Host "  Celery Beat: STOPPED" -ForegroundColor Red
        }
    } else {
        Write-Host "  Monitoring: Task Scheduler" -ForegroundColor Cyan
    }
    
    Write-Host ""
}

# Main execution
switch ($Action) {
    'start' {
        Start-WebServer
        
        if ($UseCelery) {
            Start-CeleryWorker
            Start-CeleryBeat
        } else {
            Write-Host ""
            Write-Host "Note: Celery not enabled. Use Task Scheduler for monitoring." -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "NetWatch started successfully!" -ForegroundColor Green
        Write-Host "Access the application at: http://localhost:8000" -ForegroundColor Cyan
    }
    
    'stop' {
        if ($UseCelery) {
            Stop-CeleryBeat
            Stop-CeleryWorker
        }
        Stop-WebServer
        
        Write-Host ""
        Write-Host "NetWatch stopped" -ForegroundColor Green
    }
    
    'restart' {
        Write-Host "Restarting NetWatch..." -ForegroundColor Cyan
        Write-Host ""
        
        if ($UseCelery) {
            Stop-CeleryBeat
            Stop-CeleryWorker
        }
        Stop-WebServer
        
        Start-Sleep -Seconds 2
        
        Start-WebServer
        
        if ($UseCelery) {
            Start-CeleryWorker
            Start-CeleryBeat
        }
        
        Write-Host ""
        Write-Host "NetWatch restarted successfully!" -ForegroundColor Green
    }
    
    'status' {
        Show-Status
    }
}

Write-Host ""
