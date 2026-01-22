@echo off
REM Start Celery Worker for NetWatch
REM This handles background tasks like running monitoring checks

echo.
echo ========================================
echo NetWatch Celery Worker
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Celery worker
echo Starting Celery worker with solo pool mode...
celery -A netwatch worker -l info --pool=solo

REM If Celery exits, pause so user sees any errors
pause
