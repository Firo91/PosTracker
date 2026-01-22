@echo off
REM NetWatch Agent Manual Test - Runs the agent once to verify configuration

echo ========================================
echo   NetWatch Agent Test Run
echo ========================================
echo.
echo Running agent check once...
echo.

REM Run agent once with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0netwatch_agent.ps1" --once

echo.
echo ========================================
echo   Test Complete
echo ========================================
echo.
echo Check the output above for any errors.
echo If successful, you should see "Status reported successfully"
echo.

pause
