# NetWatch Agent - PowerShell Version
# No Python installation required - runs on any Windows machine with PowerShell

# Resolve script directory (works under Scheduled Task where $PSScriptRoot can be empty)
if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    $ScriptDir = $PSScriptRoot
}

# Ensure working directory is the script directory so relative paths/logs land here
Set-Location -Path $ScriptDir

# Configuration
$Config = @{
    ServerUrl = "http://10.18.70.71:8000"
    DeviceId = $null  # Set this to your device ID
    ApiKey = $null    # Required for authentication
    CheckInterval = 60  # Seconds between checks
    Services = @()
    Processes = @()
    LogFile = "netwatch_agent.log"
    LogLevel = "INFO"  # INFO, WARNING, ERROR, DEBUG
}

# Load configuration from file if it exists
$ConfigFile = Join-Path $ScriptDir "agent_config.json"
Write-Host "Looking for config file: $ConfigFile" -ForegroundColor Cyan
if (Test-Path $ConfigFile) {
    Write-Host "Config file found, loading..." -ForegroundColor Green
    try {
        $LoadedConfig = Get-Content $ConfigFile | ConvertFrom-Json
        $Config.ServerUrl = $LoadedConfig.server_url
        $Config.DeviceId = $LoadedConfig.device_id
        $Config.ApiKey = $LoadedConfig.api_key
        $Config.CheckInterval = $LoadedConfig.check_interval
        $Config.Services = $LoadedConfig.services
        $Config.Processes = $LoadedConfig.processes
        $Config.LogFile = $LoadedConfig.log_file
        $Config.LogLevel = $LoadedConfig.log_level
        Write-Host "Config loaded successfully!" -ForegroundColor Green
        Write-Host "  Services: $($Config.Services -join ', ')" -ForegroundColor Cyan
        Write-Host "  Processes: $($Config.Processes -join ', ')" -ForegroundColor Cyan
    }
    catch {
        Write-Host "Warning: Could not load config file: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "Using hardcoded defaults instead" -ForegroundColor Yellow
    }
}
else {
    Write-Host "Config file not found at: $ConfigFile" -ForegroundColor Yellow
    Write-Host "Using hardcoded defaults" -ForegroundColor Yellow
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Cyan
    Write-Host "Script directory: $ScriptDir" -ForegroundColor Cyan
}

# Validate configuration
function Test-Configuration {
    $errors = @()
    
    if ([string]::IsNullOrEmpty($Config.ServerUrl)) {
        $errors += "ERROR: server_url is not configured"
    }
    
    if ($null -eq $Config.DeviceId -or $Config.DeviceId -eq 0) {
        $errors += "ERROR: device_id is not configured"
    }
    
    if ($null -eq $Config.ApiKey -or [string]::IsNullOrEmpty($Config.ApiKey)) {
        $errors += "ERROR: api_key is required for secure authentication"
    }
    
    if ($null -eq $Config.Processes -or $Config.Processes.Count -eq 0) {
        $errors += "WARNING: No processes configured to monitor"
    }
    
    if ($Config.CheckInterval -lt 10) {
        $errors += "ERROR: check_interval must be at least 10 seconds"
    }
    
    return $errors
}

$ValidationErrors = Test-Configuration
if ($ValidationErrors.Count -gt 0) {
    foreach ($err in $ValidationErrors) {
        if ($err.StartsWith("ERROR")) {
            Write-Host $err -ForegroundColor Red
        } else {
            Write-Host $err -ForegroundColor Yellow
        }
    }
    
    $criticalErrors = $ValidationErrors | Where-Object { $_.StartsWith("ERROR") }
    if ($criticalErrors.Count -gt 0) {
        Write-Host "Configuration validation failed. Please fix the errors above." -ForegroundColor Red
        exit 1
    }
}

# Normalize log file path to be absolute under the script directory if relative
if (-not [System.IO.Path]::IsPathRooted($Config.LogFile)) {
    $Config.LogFile = Join-Path $ScriptDir $Config.LogFile
}
Write-Host "Logging to: $Config.LogFile" -ForegroundColor Cyan
Write-Host "Log level: $($Config.LogLevel)" -ForegroundColor Cyan

# Logging function
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('INFO','WARNING','ERROR','DEBUG')]
        [string]$Level = 'INFO'
    )
    
    # Check if we should log this level
    $levels = @{'ERROR' = 0; 'WARNING' = 1; 'INFO' = 2; 'DEBUG' = 3}
    $currentLogLevel = $levels[$Config.LogLevel]
    $messageLogLevel = $levels[$Level]
    
    if ($messageLogLevel -gt $currentLogLevel) {
        return  # Skip logging this level
    }
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp - $Level - $Message"
    
    # Write to console
    switch ($Level) {
        'ERROR' { Write-Host $LogMessage -ForegroundColor Red }
        'WARNING' { Write-Host $LogMessage -ForegroundColor Yellow }
        'DEBUG' { Write-Host $LogMessage -ForegroundColor Gray }
        default { Write-Host $LogMessage }
    }
    
    # Write to log file
    try {
        Add-Content -Path $Config.LogFile -Value $LogMessage -ErrorAction SilentlyContinue
    }
    catch {
        # Ignore log file errors
    }
}

# Check Windows Service (supports name or display name, plus optional description filter)
function Test-WindowsService {
    param($ServiceConfig)
    
    try {
        # Handle both old string format and new object format
        if ($ServiceConfig -is [string]) {
            $ServiceName = $ServiceConfig
            $DescriptionFilter = $null
        } else {
            $ServiceName = $ServiceConfig.name
            $DescriptionFilter = $ServiceConfig.description_contains
        }

        # Try exact service name first
        $Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

        # If not found, try exact display name
        if ($null -eq $Service) {
            $Service = Get-Service | Where-Object { $_.DisplayName -eq $ServiceName } | Select-Object -First 1
        }

        # If still not found, try partial (case-insensitive contains) on display name
        if ($null -eq $Service) {
            $lowerName = $ServiceName.ToLower()
            $Service = Get-Service | Where-Object { $_.DisplayName.ToLower() -like "*$lowerName*" } | Select-Object -First 1
        }

        if ($null -eq $Service) {
            return @{
                Found = $false
                Running = $false
                Status = "not_found"
                DisplayName = $null
                Error = "Service '$ServiceName' not found"
            }
        }

        # If description filter is specified, capture whether it matches (but do not fail the service)
        $DescriptionMatches = $true
        if ($DescriptionFilter) {
            try {
                $WmiService = Get-WmiObject Win32_Service -Filter "Name='$($Service.Name)'" -ErrorAction SilentlyContinue
                if ($WmiService -and ($WmiService.Description -notlike "*$DescriptionFilter*")) {
                    $DescriptionMatches = $false
                }
            } catch { }
        }

        return @{
            Found = $true
            Running = ($Service.Status -eq 'Running')
            Status = $Service.Status.ToString().ToLower()
            DisplayName = $Service.DisplayName
            ServiceName = $Service.Name
            DescriptionMatches = $DescriptionMatches
            Error = $null
        }
    }
    catch {
        return @{
            Found = $false
            Running = $false
            Status = "error"
            DisplayName = $null
            Error = $_.Exception.Message
        }
    }
}

# Check Process with optional filtering by parent process
function Test-WindowsProcess {
    param($ProcessConfig)
    
    try {
        # Handle both old string format and new object format
        if ($ProcessConfig -is [string]) {
            $ProcessName = $ProcessConfig
            $Filter = $null
            $ParentProcess = $null
        } else {
            $ProcessName = $ProcessConfig.name
            $Filter = $ProcessConfig.filter
            $ParentProcess = $ProcessConfig.parent_process
        }
        
        # Remove .exe if provided
        $ProcessName = $ProcessName -replace '\.exe$', ''
        
        $Processes = $null
        
        # If parent_process is specified, find child processes of that parent
        if ($ParentProcess) {
            Write-Log "Looking for child processes of '$ParentProcess'" -Level DEBUG
            $ParentProcess = $ParentProcess -replace '\.exe$', ''
            
            # Get parent process(es)
            $parentProcs = Get-Process -Name $ParentProcess -ErrorAction SilentlyContinue
            if ($parentProcs) {
                $parentPids = if ($parentProcs -is [array]) { $parentProcs.Id } else { @($parentProcs.Id) }
                Write-Log "Found parent PIDs: $($parentPids -join ',')" -Level DEBUG
                
                # Find child processes
                $childProcs = Get-WmiObject Win32_Process -ErrorAction SilentlyContinue | 
                    Where-Object { $_.ParentProcessId -in $parentPids -and $_.Name -like "*$ProcessName*" }
                
                if ($childProcs) {
                    $Processes = foreach ($cp in $childProcs) {
                        $procObj = Get-Process -Id $cp.ProcessId -ErrorAction SilentlyContinue
                        if ($procObj) { $procObj }
                    }
                }
            }
        } else {
            # Normal process lookup
            $Processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
        }
        
        if ($null -eq $Processes) {
            # Log all running processes for debugging
            Write-Log "Process '$ProcessName' not found. Available processes:" -Level DEBUG
            $allProcs = Get-Process | Select-Object -ExpandProperty Name -Unique | Sort-Object
            $allProcs | ForEach-Object { Write-Log "  - $_" -Level DEBUG }
            
            return @{
                Running = $false
                Count = 0
                Processes = @()
                Error = $null
            }
        }

        $ProcessList = @()
        $X86List = @()

        foreach ($Proc in $Processes) {
            $path = $null
            $cmdLine = $null
            $arch = "unknown"  # Default to unknown
            
            try { $path = $Proc.Path } catch {}
            
            # Detect process architecture using multiple methods
            try {
                # Method 1: Check StartInfo (most reliable for .NET Process objects)
                # A 32-bit process on 64-bit Windows will have PointerSize = 4
                # This is checked via the process handle's architecture
                $is32Bit = $false
                
                # Check via WMI ExecutablePath for Simphony-specific location
                try {
                    $WmiProc = Get-WmiObject Win32_Process -Filter "ProcessId=$($Proc.Id)" -ErrorAction SilentlyContinue
                    if ($WmiProc) {
                        $cmdLine = $WmiProc.CommandLine
                        $exePath = $WmiProc.ExecutablePath
                        
                        Write-Log "WMI result for PID $($Proc.Id): exePath=$exePath, cmdLine=$cmdLine" -Level DEBUG
                        
                        # Check if executable is in known 32-bit locations
                        if ($exePath -like '*SysWOW64*' -or $exePath -like '*Program Files (x86)*' -or $exePath -like '*C:\Micros\Simphony\WebServer*') {
                            $is32Bit = $true
                            $arch = "x86"
                        } elseif ($exePath) {
                            # If we have a path but it's not in 32-bit locations, it's 64-bit
                            $arch = "x64"
                        }
                    }
                }
                catch { }
                
                # If WMI command line is empty, try alternate method via Get-CimInstance
                if (-not $cmdLine) {
                    try {
                        $cimProc = Get-CimInstance Win32_Process -Filter "ProcessId=$($Proc.Id)" -ErrorAction SilentlyContinue
                        if ($cimProc -and $cimProc.CommandLine) {
                            $cmdLine = $cimProc.CommandLine
                            Write-Log "Got cmdLine via CIM for PID $($Proc.Id): $cmdLine" -Level DEBUG
                        }
                    }
                    catch { }
                }
                
                # Method 2: Check modules if WMI didn't give us a clear answer
                if ($arch -eq "unknown") {
                    try {
                        $modules = $Proc.Modules
                        if ($modules -and $modules.Count -gt 0) {
                            # Check first few modules for SysWOW64
                            $moduleCheck = $modules | Select-Object -First 5
                            foreach ($mod in $moduleCheck) {
                                if ($mod.FileName -like '*SysWOW64*') {
                                    $arch = "x86"
                                    $is32Bit = $true
                                    break
                                }
                            }
                            # If no SysWOW64 found and we have modules, assume 64-bit
                            if ($arch -eq "unknown") {
                                $arch = "x64"
                            }
                        }
                    }
                    catch { }
                }
                
                # Method 3: Fallback to process path check
                if ($arch -eq "unknown" -and $path) {
                    if ($path -like '*SysWOW64*' -or $path -like '*Program Files (x86)*' -or $path -like '*C:\Micros\Simphony\WebServer*') {
                        $arch = "x86"
                    } else {
                        $arch = "x64"
                    }
                }
            }
            catch { }
            
            # Check for filter match
            $matchesFilter = $false
            if ($Filter) {
                # Negative filter: if starts with !, negate the match logic
                if ($Filter.StartsWith('!')) {
                    $negatedFilter = $Filter.Substring(1)
                    # Negative matching (NOT contains)
                    if ($negatedFilter -eq "x86" -or $negatedFilter -eq "32bit" -or $negatedFilter -eq "32-bit") {
                        $matchesFilter = ($arch -ne "x86")
                    } elseif ($negatedFilter -eq "x64" -or $negatedFilter -eq "64bit" -or $negatedFilter -eq "64-bit") {
                        $matchesFilter = ($arch -ne "x64")
                    } else {
                        # General negative text filter: does NOT contain the string
                        $matchesFilter = -not ($cmdLine -like "*$negatedFilter*" -or $path -like "*$negatedFilter*")
                    }
                } else {
                    # Positive filter: standard matching
                    if ($Filter -eq "x86" -or $Filter -eq "32bit" -or $Filter -eq "32-bit") {
                        $matchesFilter = ($arch -eq "x86")
                    } elseif ($Filter -eq "x64" -or $Filter -eq "64bit" -or $Filter -eq "64-bit") {
                        $matchesFilter = ($arch -eq "x64")
                    } else {
                        # General text filter on command line or path
                        $matchesFilter = ($cmdLine -like "*$Filter*" -or $path -like "*$Filter*")
                    }
                }
            } else {
                # No filter, default to 32-bit detection for backward compatibility
                $matchesFilter = ($arch -eq "x86")
            }
            
            $entry = @{
                PID = $Proc.Id
                MemoryMB = [math]::Round($Proc.WorkingSet64 / 1MB, 2)
                CPU = $Proc.CPU
                Path = $path
                CommandLine = $cmdLine
                Architecture = $arch
                MatchesFilter = $matchesFilter
            }
            
            # Debug logging for architecture detection
            Write-Log "Process PID $($Proc.Id): arch=$arch, filter=$Filter, matches=$matchesFilter, path=$path" -Level DEBUG
            
            $ProcessList += $entry
            if ($matchesFilter) { $X86List += $entry }
        }

        $filteredCount = $X86List.Count
        $anyMatched = ($filteredCount -gt 0)

        return @{
            Running = $anyMatched
            Count = $filteredCount
            TotalCount = $Processes.Count
            Processes = $ProcessList
            Error = $null
        }
    }
    catch {
        return @{
            Running = $false
            Count = 0
            Processes = @()
            Error = $_.Exception.Message
        }
    }
}

# Collect System Information
function Get-SystemInfo {
    try {
        $OS = Get-CimInstance Win32_OperatingSystem
        $CPU = Get-CimInstance Win32_Processor | Select-Object -First 1
        $Disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
        
        # Get CPU usage (averaged over 2 seconds)
        $CPUUsage = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 2 |
            Select-Object -ExpandProperty CounterSamples |
            Measure-Object -Property CookedValue -Average).Average
        
        # Calculate memory in GB
        $MemoryUsedGB = [math]::Round((($OS.TotalVisibleMemorySize - $OS.FreePhysicalMemory) / 1MB), 2)
        $MemoryTotalGB = [math]::Round(($OS.TotalVisibleMemorySize / 1MB), 2)
        $MemoryPercent = [math]::Round(($MemoryUsedGB / $MemoryTotalGB) * 100, 1)
        
        # Calculate disk in GB
        $DiskUsedGB = [math]::Round((($Disk.Size - $Disk.FreeSpace) / 1GB), 2)
        $DiskTotalGB = [math]::Round(($Disk.Size / 1GB), 2)
        $DiskFreeGB = [math]::Round(($Disk.FreeSpace / 1GB), 2)
        $DiskPercent = [math]::Round(($DiskUsedGB / $DiskTotalGB) * 100, 1)
        
        # Calculate uptime in hours
        $Uptime = (Get-Date) - $OS.LastBootUpTime
        $UptimeHours = [math]::Round($Uptime.TotalHours, 1)
        
        # Get process count
        $ProcessCount = (Get-Process).Count
        
        return @{
            Hostname = $env:COMPUTERNAME
            CPUPercent = [math]::Round($CPUUsage, 1)
            MemoryPercent = $MemoryPercent
            MemoryUsedGB = $MemoryUsedGB
            MemoryTotalGB = $MemoryTotalGB
            DiskPercent = $DiskPercent
            DiskUsedGB = $DiskUsedGB
            DiskFreeGB = $DiskFreeGB
            DiskTotalGB = $DiskTotalGB
            UptimeHours = $UptimeHours
            ProcessCount = $ProcessCount
            BootTime = $OS.LastBootUpTime.ToString("yyyy-MM-ddTHH:mm:ss")
            OSVersion = $OS.Caption
        }
    }
    catch {
        Write-Log "Error collecting system info: $($_.Exception.Message)" -Level ERROR
        return @{
            Hostname = $env:COMPUTERNAME
            Error = $_.Exception.Message
        }
    }
}

# Perform all checks
function Invoke-StatusCheck {
    Write-Log "Starting check cycle"
    
    # Collect raw system info
    $Sys = Get-SystemInfo

    # Build payload using snake_case keys expected by server
    $Results = @{
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        device_id = $Config.DeviceId
        system_info = @{
            hostname = $Sys.Hostname
            cpu_percent = $Sys.CPUPercent
            memory_percent = $Sys.MemoryPercent
            memory_used_gb = $Sys.MemoryUsedGB
            memory_total_gb = $Sys.MemoryTotalGB
            disk_percent = $Sys.DiskPercent
            disk_used_gb = $Sys.DiskUsedGB
            disk_free_gb = $Sys.DiskFreeGB
            disk_total_gb = $Sys.DiskTotalGB
            uptime_hours = $Sys.UptimeHours
            process_count = $Sys.ProcessCount
        }
        services = @{}
        processes = @{}
    }
    
    # Check services
    foreach ($ServiceConfig in $Config.Services) {
        # Extract name and label
        if ($ServiceConfig -is [string]) {
            $ServiceName = $ServiceConfig
            $ServiceLabel = $ServiceConfig
        } else {
            $ServiceName = $ServiceConfig.name
            $ServiceLabel = if ($ServiceConfig.label) { $ServiceConfig.label } else { $ServiceConfig.name }
        }
        
        Write-Log "Checking service: $ServiceName (label: $ServiceLabel)" -Level DEBUG
        $svc = Test-WindowsService -ServiceConfig $ServiceConfig
        # Normalize keys to snake_case for server
        $Results.services[$ServiceLabel] = @{
            running = $svc.Running
            status = $svc.Status
            found  = $svc.Found
        }
    }
    
    # Check processes
    foreach ($ProcessConfig in $Config.Processes) {
        # Extract name and label
        if ($ProcessConfig -is [string]) {
            $ProcessName = $ProcessConfig
            $ProcessLabel = $ProcessConfig
        } else {
            $ProcessName = $ProcessConfig.name
            $ProcessLabel = if ($ProcessConfig.label) { $ProcessConfig.label } else { $ProcessConfig.name }
        }
        
        Write-Log "Checking process: $ProcessName (label: $ProcessLabel)" -Level DEBUG
        $proc = Test-WindowsProcess -ProcessConfig $ProcessConfig
        # Build process entry with instance details
        $instances = @()
        if ($proc.Processes -and $proc.Processes.Count -gt 0) {
            foreach ($p in $proc.Processes) {
                if ($p.MatchesFilter) {
                    $instances += @{
                        pid = $p.PID
                        memory_mb = $p.MemoryMB
                        cpu = $p.CPU
                    }
                }
            }
        }
        # Normalize keys to snake_case for server
        $Results.processes[$ProcessLabel] = @{
            running = $proc.Running
            count   = $proc.Count
            instances = $instances
        }
    }
    
    # Log summary
    $ServiceSummary = @()
    foreach ($ServiceName in $Results.Services.Keys) {
        $Info = $Results.Services[$ServiceName]
        $Status = if ($Info.Running) { "RUNNING" } else { "STOPPED" }
        $ServiceSummary += "$ServiceName`: $Status"
    }
    
    $ProcessSummary = @()
    foreach ($ProcessName in $Results.Processes.Keys) {
        $Info = $Results.Processes[$ProcessName]
        $Status = if ($Info.Running) { "RUNNING ($($Info.Count) instances)" } else { "NOT RUNNING" }
        $ProcessSummary += "$ProcessName`: $Status"
    }
    
    if ($ServiceSummary.Count -gt 0) {
        Write-Log "Services: $($ServiceSummary -join ', ')"
    }
    if ($ProcessSummary.Count -gt 0) {
        Write-Log "Processes: $($ProcessSummary -join ', ')"
    }
    
    return $Results
}

# Report status to server
function Send-StatusReport {
    param($Results)
    
    if ([string]::IsNullOrEmpty($Config.ServerUrl)) {
        Write-Log "No server URL configured" -Level ERROR
        return $false
    }
    
    if ($null -eq $Config.DeviceId) {
        Write-Log "No device ID configured" -Level ERROR
        return $false
    }
    
    try {
        $Url = "$($Config.ServerUrl)/api/agent-report/"
        $Headers = @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $($Config.ApiKey)"
        }
        
        $Body = $Results | ConvertTo-Json -Depth 10

        Write-Log "POSTing to: $Url" -Level DEBUG
        
        # Retry logic with exponential backoff
        $maxRetries = 3
        $retryDelays = @(1, 2, 4)  # Seconds: 1s, 2s, 4s
        $lastError = $null
        
        for ($attempt = 0; $attempt -lt $maxRetries; $attempt++) {
            try {
                $Response = Invoke-RestMethod -Uri $Url -Method Post -Headers $Headers -Body $Body -TimeoutSec 10
                Write-Log "Status reported successfully (attempt $($attempt + 1))"
                return $true
            }
            catch {
                $lastError = $_.Exception.Message
                if ($attempt -lt ($maxRetries - 1)) {
                    $delaySeconds = $retryDelays[$attempt]
                    Write-Log "POST failed (attempt $($attempt + 1)/$maxRetries): $lastError. Retrying in $delaySeconds seconds..." -Level WARNING
                    Start-Sleep -Seconds $delaySeconds
                }
            }
        }
        
        # All retries exhausted
        Write-Log "Failed to report status after $maxRetries attempts: $lastError" -Level ERROR
        return $false
    }
    catch {
        Write-Log "Error reporting status: $($_.Exception.Message)" -Level ERROR
        return $false
    }
}

# Main execution
function Start-Agent {
    param([switch]$Once)
    
    Write-Log "NetWatch Agent started"
    Write-Log "Server: $($Config.ServerUrl)"
    Write-Log "Device ID: $($Config.DeviceId)"
    Write-Log "Check interval: $($Config.CheckInterval) seconds"
    
    if ($null -eq $Config.DeviceId) {
        Write-Log "WARNING: Device ID is not configured. Please edit agent_config.json" -Level WARNING
        Write-Log "You can find your Device ID in the NetWatch admin interface" -Level WARNING
    }
    
    do {
        try {
            $Results = Invoke-StatusCheck
            Send-StatusReport -Results $Results
        }
        catch {
            Write-Log "Error in check cycle: $($_.Exception.Message)" -Level ERROR
        }
        
        if (-not $Once) {
            Write-Log "Waiting $($Config.CheckInterval) seconds until next check..."
            Start-Sleep -Seconds $Config.CheckInterval
        }
    } while (-not $Once)
}

# Check command line arguments
if ($args -contains "--once" -or $args -contains "-Once") {
    Start-Agent -Once
}
else {
    Start-Agent
}
