# NetWatch Quick Start Script
# This script helps you set up and run NetWatch quickly

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NetWatch - Quick Start Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host ".env file not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host ".env file created. Please edit it with your settings!" -ForegroundColor Red
    Write-Host "Opening .env in notepad..." -ForegroundColor Yellow
    notepad .env
    Write-Host "Press any key after saving .env to continue..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Yellow
python manage.py migrate

# Create static directory
if (-Not (Test-Path "static")) {
    Write-Host "Creating static directory..." -ForegroundColor Yellow
    mkdir static
}

# Collect static files
Write-Host "Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

# Create logs directory
if (-Not (Test-Path "logs")) {
    Write-Host "Creating logs directory..." -ForegroundColor Yellow
    mkdir logs
}

# Check if superuser exists
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Admin User Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Do you want to create an admin user? (y/n): " -ForegroundColor Yellow -NoNewline
$createAdmin = Read-Host

if ($createAdmin -eq 'y' -or $createAdmin -eq 'Y') {
    python manage.py createsuperuser
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start the development server:" -ForegroundColor White
Write-Host "   python manage.py runserver 0.0.0.0:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Access the application:" -ForegroundColor White
Write-Host "   http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. To run monitoring checks:" -ForegroundColor White
Write-Host "   Option A (Celery - requires Redis):" -ForegroundColor Gray
Write-Host "     celery -A netwatch worker -l info --pool=solo" -ForegroundColor Cyan
Write-Host "     celery -A netwatch beat -l info" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Option B (Manual/Task Scheduler):" -ForegroundColor Gray
Write-Host "     python manage.py run_monitoring" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Test email alerts:" -ForegroundColor White
Write-Host "   python manage.py test_alerts" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
