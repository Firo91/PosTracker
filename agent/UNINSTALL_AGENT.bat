@echo off
REM NetWatch Agent Uninstaller - Double-click to remove the Scheduled Task

echo ========================================
echo   NetWatch Agent Uninstaller
echo ========================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This requires Administrator privileges.
    echo Please right-click and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo Removing NetWatch Agent scheduled task...
echo.

REM Run PowerShell uninstaller with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0install_agent_task.ps1" -Action uninstall

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo   Uninstall Complete!
    echo ========================================
    echo.
    echo The NetWatchAgent task has been removed.
    echo.
) else (
    echo.
    echo Note: Task may not have been installed.
    echo.
)

pause
