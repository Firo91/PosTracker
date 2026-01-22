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

REM Prompt for configuration
set /p SERVER_URL="Enter NetWatch server URL (e.g., http://10.18.70.71:8000): "
set /p DEVICE_ID="Enter Device ID from dashboard: "

echo.
echo Installing NetWatch Agent with:
echo   Server: %SERVER_URL%
echo   Device ID: %DEVICE_ID%
echo   Schedule: Every 1 minute
echo.

REM Run PowerShell installer with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0install_agent_task.ps1" -Action install -ServerUrl "%SERVER_URL%" -DeviceId %DEVICE_ID% -IntervalMinutes 1

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
