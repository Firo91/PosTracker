@echo off
REM NetWatch Agent Installer - Double-click to install as a Scheduled Task
REM This batch file bypasses PowerShell execution policy

echo ========================================
echo   NetWatch Agent Installer
echo ========================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This installer requires Administrator privileges.
    echo Please right-click and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

REM Check if agent_config.json exists (pre-configured from download)
if not exist "%~dp0agent_config.json" (
    echo ERROR: agent_config.json not found!
    echo.
    echo Please download a pre-configured agent package from the web interface:
    echo https://www.pos.kimsit.com/dashboard/download-agent/
    echo.
    echo Or manually edit agent_config.json before running this installer.
    echo.
    pause
    exit /b 1
)

echo.
echo Using pre-configured settings from agent_config.json
echo.
echo ========================================
echo   Installing NetWatch Agent
echo ========================================
echo   Schedule: Every 1 minute
echo   Config: agent_config.json
echo.

REM Run PowerShell installer with execution policy bypass
REM The installer will auto-detect and use agent_config.json
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0install_agent_task.ps1" -Action install -IntervalMinutes 1

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo   Installation Complete!
    echo ========================================
    echo.
    echo The agent will start running in about 1 minute.
    echo.
    echo To verify installation:
    echo   1. Open Task Scheduler (taskschd.msc)
    echo   2. Look for 'NetWatchAgent' task
    echo   3. Or run CHECK_STATUS.bat
    echo.
    echo Logs are written to: %~dp0netwatch_agent.log
    echo.
) else (
    echo.
    echo ========================================
    echo   ERROR: Installation failed
    echo ========================================
    echo.
    echo Check the error messages above.
    echo.
)

pause
