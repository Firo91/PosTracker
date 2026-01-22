# NetWatch - Internal LAN Device Monitoring

**NetWatch** is a production-ready Django web application for monitoring Windows POS terminals and servers on an internal network. It provides real-time status monitoring with ping checks, RDP port connectivity, and remote Simphony service/process monitoring via WinRM.

## Features

- 🖥️ **Device Inventory Management**: Track POS terminals and servers with detailed monitoring settings
- 📡 **Multi-Level Monitoring**:
  - Network ping checks
  - TCP port connectivity (RDP)
  - Remote Windows service monitoring via WinRM
  - Remote process monitoring via WinRM
- 📊 **Real-Time Dashboard**: Bootstrap 5 UI with color-coded status indicators
- 📧 **Email Alerts**: Configurable notifications for status changes with throttling
- ⚙️ **Flexible Deployment**: Support for Celery (with Redis) or Windows Task Scheduler
- 🗄️ **Database Support**: PostgreSQL for production, SQLite for local development
- 🔐 **Credential Management**: Secure storage of remote access credentials

## Requirements

- Python 3.11 or higher
- Windows Server (monitoring engine uses Windows-specific commands)
- PostgreSQL (production) or SQLite (development)
- Redis (optional, for Celery)
- Network access to monitored devices
- WinRM enabled on monitored endpoints (for Simphony checks)

## Installation

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd PosTracker
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file and edit it:

```powershell
Copy-Item .env.example .env
notepad .env
```

**Important settings to configure:**

- `DJANGO_SECRET_KEY`: Generate a secure secret key
- `ALLOWED_HOSTS`: Add your server's IP/hostname
- `TIME_ZONE`: Set to your local timezone
- `DATABASE_ENGINE`: Use `sqlite` for dev, `postgresql` for production
- `ALERT_EMAIL_RECIPIENTS`: Comma-separated list of email addresses

### 5. Run Migrations

```powershell
python manage.py migrate
```

### 6. Create Admin User

```powershell
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 7. Create Static Files Directory

```powershell
mkdir static
python manage.py collectstatic --noinput
```

## Running the Application

### Development Server

```powershell
python manage.py runserver 0.0.0.0:8000
```

Access the application at `http://localhost:8000`

### Production Deployment

For production, use a WSGI server like Gunicorn (on Linux) or waitress (on Windows):

```powershell
# Install waitress for Windows
pip install waitress

# Run production server
waitress-serve --listen=*:8000 netwatch.wsgi:application
```

Or use IIS with wfastcgi. See Django deployment documentation for details.

## Setting Up Device Monitoring

### 1. Configure Credential Profiles

1. Log in to Django Admin: `http://localhost:8000/admin/`
2. Go to **Credential Profiles**
3. Click **Add Credential Profile**
4. Enter:
   - **Name**: Descriptive name (e.g., "Local Admin")
   - **Username**: Windows username (format: `DOMAIN\user` or `user@domain`)
   - **Password**: Windows password
   - **Domain**: Optional domain name

**Security Note**: Store credentials securely. Consider using Django's encryption features or environment variables for production.

### 2. Add Devices

1. In Django Admin, go to **Devices**
2. Click **Add Device**
3. Configure:
   - **Basic Info**: Name, IP address, device type, location
   - **Network Checks**: Enable ping and/or RDP checks
   - **Simphony Monitoring**:
     - Select check mode: NONE, WINDOWS_SERVICE, or PROCESS_NAME
     - Enter service name (e.g., `SimphonyService`) or process name (e.g., `simphony`)
     - Select credential profile for remote checks
   - **Check Parameters**: Adjust timeouts, retries, and thresholds

### 3. Enable WinRM on Monitored Devices

For Simphony service/process checks to work, WinRM must be enabled on target devices:

```powershell
# Run on each monitored device (as Administrator)
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
Restart-Service WinRM
```

**Security Note**: In production, configure WinRM with HTTPS and proper authentication. The above is for internal trusted networks only.

Test WinRM connectivity:

```powershell
Test-WSMan -ComputerName <device-ip>
```

## Running Monitoring Checks

### Option 1: Using Celery (Recommended for 24/7 Monitoring)

Celery provides automatic scheduled checks and better concurrency.

**Prerequisites**: Install and start Redis

```powershell
# Download Redis for Windows: https://github.com/microsoftarchive/redis/releases
# Or use Redis in Docker
docker run -d -p 6379:6379 redis:latest
```

**Start Celery Worker**:

```powershell
celery -A netwatch worker -l info --pool=solo
```

**Start Celery Beat** (scheduler):

```powershell
celery -A netwatch beat -l info
```

Celery Beat will automatically run checks every 60 seconds for all enabled devices.

### Option 2: Using Management Command + Task Scheduler

For environments without Redis/Celery, use Windows Task Scheduler:

**Test the command**:

```powershell
python manage.py run_monitoring
```

**Create scheduled task**:

1. Open Task Scheduler
2. Create Basic Task
3. Name: "NetWatch Monitoring"
4. Trigger: Repeat every 1 minute
5. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\PosTracker\manage.py run_monitoring`
   - Start in: `C:\path\to\PosTracker`

**Check specific device**:

```powershell
# By device ID
python manage.py run_monitoring --device-id 1

# By device name
python manage.py run_monitoring --device-name "POS-01"
```

## Email Alerts

Configure email settings in `.env`:

### Console Backend (Testing)

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Emails will be printed to the console/logs.

### SMTP Backend (Production)

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=netwatch@yourcompany.com
ALERT_EMAIL_RECIPIENTS=admin@example.com,it@example.com
```

**Test alert configuration**:

```powershell
python manage.py test_alerts
```

### Alert Behavior

- Alerts are sent when device status changes (UP ↔ DOWN, UP ↔ DEGRADED)
- Throttled to prevent spam (10 minute minimum between alerts per device)
- Includes device details, check results, and error messages

## Dashboard

Access the dashboard at `http://localhost:8000/dashboard/`

**Features**:
- Color-coded status summary (UP/DEGRADED/DOWN/UNKNOWN)
- Device list with real-time status
- Filters by device type, status, location, enabled state
- Search by name or IP address
- Device detail pages with check history and statistics
- Auto-refresh every 30 seconds

## Management Commands

```powershell
# Run monitoring checks
python manage.py run_monitoring

# Test email alerts
python manage.py test_alerts

# Create admin user
python manage.py createsuperuser

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic
```

## Database Management

### SQLite (Development)

Default database file: `db.sqlite3` in project root.

### PostgreSQL (Production)

1. Install PostgreSQL
2. Create database:

```sql
CREATE DATABASE netwatch;
CREATE USER netwatch_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE netwatch TO netwatch_user;
```

3. Update `.env`:

```env
DATABASE_ENGINE=postgresql
DB_NAME=netwatch
DB_USER=netwatch_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
```

4. Run migrations:

```powershell
python manage.py migrate
```

## Monitoring Data Cleanup

Check results are automatically cleaned up by Celery Beat task (runs hourly). It keeps the most recent 500 results per device.

**Manual cleanup**:

```powershell
python manage.py shell
>>> from apps.monitoring.tasks import cleanup_old_check_results
>>> cleanup_old_check_results()
```

## Troubleshooting

### WinRM Connection Errors

**Error**: "Connection timeout" or "Access denied"

**Solutions**:
- Verify WinRM is enabled on target device: `Test-WSMan -ComputerName <ip>`
- Check firewall rules (port 5985 for HTTP, 5986 for HTTPS)
- Verify credentials are correct
- Ensure user has admin privileges on target device

### Ping Always Fails

**Check**:
- ICMP is not blocked by firewall
- Device IP is correct
- Network connectivity exists

**Test manually**:
```powershell
ping -n 1 <device-ip>
```

### Celery Not Running Tasks

**Check**:
- Redis is running: `redis-cli ping` (should return PONG)
- Celery worker is running
- Celery beat is running
- Check Celery logs for errors

### No Email Alerts

**Check**:
- `ALERT_EMAIL_RECIPIENTS` is configured in `.env`
- Email backend is configured correctly
- Run test: `python manage.py test_alerts`
- Check logs for SMTP errors

## Project Structure

```
PosTracker/
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── README.md                 # This file
├── netwatch/                 # Project configuration
│   ├── settings.py           # Django settings
│   ├── urls.py               # URL routing
│   ├── celery.py             # Celery configuration
│   └── wsgi.py               # WSGI entry point
├── apps/
│   ├── inventory/            # Device and credential models
│   │   ├── models.py         # Device, CredentialProfile
│   │   └── admin.py          # Admin interface
│   ├── monitoring/           # Monitoring engine
│   │   ├── models.py         # CheckResult, AlertLog
│   │   ├── engine.py         # Ping, TCP, WinRM checks
│   │   ├── tasks.py          # Celery tasks
│   │   ├── alerts.py         # Email alert system
│   │   └── management/commands/
│   │       ├── run_monitoring.py  # Manual check command
│   │       └── test_alerts.py     # Test email command
│   └── dashboard/            # Web UI
│       ├── views.py          # Dashboard views
│       └── urls.py           # Dashboard URLs
├── templates/                # HTML templates
│   ├── base.html
│   └── dashboard/
│       ├── index.html        # Main dashboard
│       └── device_detail.html # Device detail page
└── logs/                     # Application logs
```

## Security Considerations

1. **Credentials**: Store credential profile passwords securely. Consider using:
   - Django's encryption (`cryptography` package)
   - Azure Key Vault or similar secret management
   - Separate credentials database with restricted access

2. **WinRM**: 
   - Use HTTPS for WinRM in production
   - Configure proper authentication (Kerberos preferred)
   - Limit WinRM trusted hosts

3. **Django Secret Key**: Generate a strong secret key and never commit it to version control

4. **Network**: Run on internal network only. If external access needed, use VPN.

5. **Credentials in Logs**: The application avoids logging credentials, but review logs regularly.

## License

Internal use only. Not for public distribution.

## Support

For issues or questions, contact your IT department or the development team.

---

**NetWatch** - Simple, effective LAN device monitoring for Windows environments.
