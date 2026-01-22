@echo off
REM Start Celery Beat Scheduler for NetWatch
REM This runs scheduled tasks like monitoring checks every 60 seconds

echo.
echo ========================================
echo NetWatch Celery Beat Scheduler
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Celery beat
echo Starting Celery Beat scheduler...
echo Tasks configured:
echo  - run_all_monitoring_checks: every 60 seconds
echo  - cleanup_old_check_results: every 1 hour
echo  - cleanup_old_data: every 24 hours
echo.
celery -A netwatch beat -l info

REM If Celery Beat exits, pause so user sees any errors
pause
