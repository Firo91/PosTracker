@echo off
REM NetWatch Agent Status Checker - Double-click to view task status

echo ========================================
echo   NetWatch Agent Status
echo ========================================
echo.

REM Run PowerShell status check with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0install_agent_task.ps1" -Action status

echo.
echo Recent log entries:
echo ----------------------------------------
if exist "%~dp0netwatch_agent.log" (
    powershell -Command "Get-Content '%~dp0netwatch_agent.log' -Tail 10"
) else (
    echo No log file found yet.
)

echo.
pause
