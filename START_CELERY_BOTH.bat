@echo off
REM Start both Celery services for NetWatch
REM Launches both Worker and Beat in separate windows

echo.
echo ========================================
echo NetWatch Celery Services (Both)
echo ========================================
echo.

REM Check if another instance is running
tasklist /FI "IMAGENAME eq python.exe" | find /I "celery" >nul
if %errorlevel%==0 (
    echo WARNING: Celery services may already be running
    echo.
)

REM Start Celery Worker in new window
echo Launching Celery Worker in new window...
start "NetWatch Celery Worker" cmd /k START_CELERY_WORKER.bat

REM Wait a moment before starting beat
timeout /t 2 /nobreak

REM Start Celery Beat in new window
echo Launching Celery Beat Scheduler in new window...
start "NetWatch Celery Beat" cmd /k START_CELERY_BEAT.bat

echo.
echo Both services launched!
echo - Worker window: Processes background tasks
echo - Beat window: Schedules tasks to run
echo.
echo Press Ctrl+C in either window to stop that service.
echo Close the windows to stop.
echo.
timeout /t 3 /nobreak
