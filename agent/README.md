# NetWatch Agent

Lightweight Windows agent that monitors local services and reports status to the NetWatch server.

## Features

- ✅ **NO PYTHON REQUIRED** - Pure PowerShell script
- ✅ **Easy Click-to-Install** - No execution policy issues
- ✅ Check Windows services by name
- ✅ Check running processes
- ✅ Collect system metrics (CPU, memory, disk)
- ✅ Report status to central server via HTTP API
- ✅ Runs as a background Scheduled Task
- ✅ Works on any Windows machine (PowerShell included by default)

## Quick Installation

### 1. Copy the Agent Folder to Target Server

Copy the entire `agent` folder to each POS terminal or server.

### 2. Install as a Background Service

**Right-click** `INSTALL_AGENT.bat` → **"Run as Administrator"**

You'll be prompted for:
- NetWatch server URL (e.g., `http://10.18.70.71:8000`)
- Device ID (find this in the NetWatch dashboard ID column)

The agent will automatically:
- Create a Windows Scheduled Task
- Run every 1 minute in the background
- Start automatically on system boot
- Run under SYSTEM account with highest privileges

> **Important**: You MUST right-click and "Run as Administrator" for installation to work.

## Management Tools

All tools bypass PowerShell execution policy automatically:

### CHECK_STATUS.bat
Double-click to view:
- Task status and last run time
- Recent log entries

### TEST_AGENT.bat
Double-click to run a single check manually:
- Tests configuration before installing
- Useful for debugging

### UNINSTALL_AGENT.bat
**Right-click → Run as Administrator** to remove the scheduled task

## Configuration

Edit `agent_config.json` to customize monitoring:

### Simple Format (String-based)
For basic monitoring:

```json
{
    "server_url": "http://10.18.70.71:8000",
    "device_id": 1,
    "check_interval": 60,
    "services": [
        "Oracle Hospitality Simphony Service Host",
        "Service Host"
    ],
    "processes": [
        "ServiceHost"
    ]
}
```

### Advanced Format (Object-based)
For filtering when you have multiple services/processes with similar names:

```json
{
    "server_url": "http://10.18.70.71:8000",
    "device_id": 1,
    "check_interval": 60,
    "services": [
        {
            "name": "OracleHospitalitySimphonyServiceHost",
            "description_contains": "Oracle Hospitality"
        },
        {
            "name": "ServiceHost",
            "description_contains": null
        }
    ],
    "processes": [
        {
            "name": "ServiceHost",
            "filter": "simphony"
        }
    ]
}
```

**Configuration Options:**
- `server_url`: URL of your NetWatch server
- `device_id`: Device ID from NetWatch dashboard
- `check_interval`: How often to check (in seconds)
- `services`: Windows service names to monitor
  - **String format**: Just the service name (old style)
  - **Object format**: 
    - `name`: Service name or internal service name
    - `description_contains`: Filter by service description (case-insensitive partial match)
- `processes`: Process names to monitor
  - **String format**: Just the process name (old style, defaults to 32-bit detection)
  - **Object format**:
    - `name`: Process name (without .exe)
    - `filter`: Filter by command-line arguments or path (case-insensitive partial match)
      - Example: `"simphony"` matches processes with "simphony" in command line or path
      - Example: `"webserver"` matches paths with "webserver"
- `log_level`: DEBUG, INFO, WARNING, ERROR
- `log_file`: Path to log file

**Tips for Differentiating Services:**
1. Check service description: `Get-Service -Name "ServiceHost" | Select Description`
2. Check service binary path: Registry `HKLM:\System\CurrentControlSet\Services\[ServiceName]` → `ImagePath`
3. Use description_contains filter to differentiate Oracle Hospitality from generic Service Host

**Tips for Differentiating Processes:**
1. Get process command line: `Get-Process ServiceHost | ForEach { (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine }`
2. Use the filter to match specific command-line arguments or file paths
3. If processes have different working directories or executable paths, use filter to match them

### 3. Test the Agent

**Option A: Double-click `TEST_AGENT.bat`**

This will run one check and show you the results.

**Option B: Run from PowerShell:**

```powershell
powershell -ExecutionPolicy Bypass -File netwatch_agent.ps1 --once
```

## Usage

### Run the Agent

**Easiest: Double-click `START_AGENT.bat`**

The agent will run continuously in a window, checking every 60 seconds.

**Or run from PowerShell:**

```powershell
powershell -ExecutionPolicy Bypass -File netwatch_agent.ps1
```

### Run on Startup (Task Scheduler)

1. Open **Task Scheduler** (search in Start Menu)
2. Click **Create Basic Task**
3. Name: `NetWatch Agent`
4. Trigger: **When the computer starts**
5. Action: **Start a program**
   - Program: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\NetWatch\netwatch_agent.ps1"`
   - Start in: `C:\NetWatch\` (or wherever you copied the files)
6. Check: **Run whether user is logged on or not**
7. Check: **Run with highest privileges**
8. Click Finish

The agent will now start automatically when the computer boots.

## How It Works

```
┌─────────────────┐
│  POS Terminal   │
│  (10.18.90.165) │
└────────┬────────┘
         │
         │ 1. Check local services
         │    - Oracle Hospitality Simphony Service Host
         │
         │ 2. Check local processes
         │    - simphony.exe
         │
         │ 3. Collect system info
         │    - CPU, Memory, Disk usage
         │
         ▼
┌─────────────────┐
│ NetWatch Agent  │
│ (This script)   │
└────────┬────────┘
         │
         │ 4. HTTP POST to server
         │    /api/agent-report/
         │
         ▼
┌─────────────────┐
│ NetWatch Server │
│  (10.18.70.71)  │
└─────────────────┘
```

## Finding Service Names

To find the exact service name:

```powershell
# List all services
Get-Service | Select-Object Name, DisplayName, Status

# Search for specific service
Get-Service | Where-Object {$_.DisplayName -like "*Simphony*"}
```

## Logs

Logs are written to `netwatch_agent.log` in the same directory as the script.

View live logs:

```powershell
Get-Content netwatch_agent.log -Wait -Tail 20
```

## Troubleshooting

### PowerShell execution policy error
If you see "running scripts is disabled", run this once as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope LocalMachine
```

Or just use the `.bat` files which bypass the policy.

### Service not found
- Check the exact service name using `Get-Service`
- Service names are case-insensitive
- Use the "Name" not "Display Name"

### Cannot connect to server
- Verify server URL is correct
- Check firewall allows outbound HTTP
- Test with: `curl http://10.18.70.71:8000`

### Agent stops running
- Check logs in `netwatch_agent.log`
- Run `TEST_AGENT.bat` to see errors
- Verify configuration in `agent_config.json`

## Why PowerShell Instead of Python?

- ✅ **No installation needed** - PowerShell comes with Windows
- ✅ **Lightweight** - No dependencies to install or update
- ✅ **Native access** - Direct access to Windows services and processes
- ✅ **Easy deployment** - Just copy 4 files
- ✅ **Reliable** - Uses built-in Windows APIs

## File List

```
agent/
├── netwatch_agent.ps1      # Main PowerShell agent (the actual program)
├── agent_config.json        # Configuration file
├── START_AGENT.bat          # Double-click to run continuously
├── TEST_AGENT.bat           # Double-click to test once
├── netwatch_agent.py        # Python version (optional, if you prefer Python)
├── requirements.txt         # Python dependencies (only if using .py version)
└── README.md                # This file
```

## Security Notes

- Agent only reads local service status (no admin rights needed for reading)
- Communication is HTTP (consider HTTPS for production)
- Optional API key authentication supported
- No credentials stored on agent
- PowerShell script is plain text - you can review what it does

## Next Steps

After deploying the agent, you'll need to:
1. Create an API endpoint on the NetWatch server to receive agent reports (`/api/agent-report/`)
2. Update Device model to store agent-reported service status
3. Update dashboard to show service status from agent reports
4. Set device ID in `agent_config.json` for each terminal
