# NetWatch - Quick Reference Guide

## Common Commands

### Setup & Installation
```powershell
# Run quick setup script
.\setup.ps1

# Manual setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### Running the Application
```powershell
# Development server
python manage.py runserver 0.0.0.0:8000

# Production server (Waitress)
pip install waitress
waitress-serve --listen=*:8000 netwatch.wsgi:application
```

### Monitoring Operations
```powershell
# Run monitoring checks manually
python manage.py run_monitoring

# Check specific device by ID
python manage.py run_monitoring --device-id 1

# Check specific device by name
python manage.py run_monitoring --device-name "POS-01"

# Celery worker (requires Redis)
celery -A netwatch worker -l info --pool=solo

# Celery beat scheduler
celery -A netwatch beat -l info
```

### Database Operations
```powershell
# Create/apply migrations
python manage.py makemigrations
python manage.py migrate

# Database shell
python manage.py dbshell

# Django shell
python manage.py shell
```

### User Management
```powershell
# Create superuser
python manage.py createsuperuser

# Change user password
python manage.py changepassword <username>
```

### Testing & Debugging
```powershell
# Test email alerts
python manage.py test_alerts

# Create sample data
python manage.py create_sample_data

# Run unit tests
python manage.py test

# Check for issues
python manage.py check

# Run test script
python test_monitoring.py
```

### Maintenance
```powershell
# Collect static files
python manage.py collectstatic --noinput

# Clear expired sessions
python manage.py clearsessions

# Show migrations
python manage.py showmigrations

# View logs
Get-Content logs\netwatch.log -Tail 50 -Wait
```

## URLs

- **Dashboard**: http://localhost:8000/
- **Admin Interface**: http://localhost:8000/admin/
- **Device Detail**: http://localhost:8000/dashboard/device/<id>/

## Configuration Quick Reference

### .env File Key Settings
```env
DJANGO_SECRET_KEY=<generate-unique-key>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,<server-ip>
TIME_ZONE=America/New_York
DATABASE_ENGINE=sqlite  # or postgresql
ALERT_EMAIL_RECIPIENTS=admin@example.com,it@example.com
```

### Device Status Logic
- **UP**: Reachable (ping OR RDP) AND (Simphony OK OR not checked)
- **DEGRADED**: Reachable BUT Simphony failed
- **DOWN**: Not reachable (ping AND RDP failed) for >= failure_threshold
- **UNKNOWN**: Never checked

### Check Types
1. **Ping**: Uses Windows `ping` command
2. **RDP**: TCP socket connection to port (default 3389)
3. **Simphony Service**: WinRM query for Windows service status
4. **Simphony Process**: WinRM query for running process

### WinRM Configuration (on monitored devices)
```powershell
# Enable WinRM (run as Administrator)
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
Restart-Service WinRM

# Test WinRM
Test-WSMan -ComputerName <device-ip>

# Production: Configure HTTPS
winrm quickconfig -transport:https
```

## Troubleshooting Quick Fixes

### Issue: "Module not found"
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue: "No such table"
```powershell
python manage.py migrate
```

### Issue: WinRM connection fails
```powershell
# On monitoring server
Test-WSMan -ComputerName <device-ip>

# On target device (as Admin)
Get-Service WinRM
Enable-PSRemoting -Force
```

### Issue: No alerts received
```powershell
# Test alert configuration
python manage.py test_alerts

# Check email settings in .env
# Verify ALERT_EMAIL_RECIPIENTS is set
```

### Issue: Celery not running tasks
```powershell
# Check Redis is running
redis-cli ping  # Should return PONG

# Restart Celery
# Kill existing processes, then:
celery -A netwatch worker -l info --pool=solo
celery -A netwatch beat -l info
```

### Issue: Static files not loading
```powershell
python manage.py collectstatic --noinput
# Ensure STATIC_ROOT and STATIC_URL are configured
```

## Admin Interface Tips

### Adding a Device
1. Login to admin: http://localhost:8000/admin/
2. Click "Devices" → "Add Device"
3. Fill in required fields:
   - Name (unique)
   - IP address
   - Device type (POS/SERVER)
4. Configure monitoring:
   - Enable ping/RDP checks
   - Select Simphony check mode
   - Enter service/process name if applicable
   - Select credential profile
5. Adjust thresholds if needed (defaults are usually fine)
6. Save

### Adding Credential Profile
1. Click "Credential Profiles" → "Add Credential Profile"
2. Enter:
   - Name (descriptive)
   - Username (format: DOMAIN\user or user)
   - Password
3. Save
4. Assign to devices that need remote checks

### Viewing Check Results
1. Click "Check Results"
2. Filter by device, status, or date
3. View detailed check information
4. Export if needed

### Viewing Alert Logs
1. Click "Alert Logs"
2. See all sent alerts with timestamps
3. Verify delivery status
4. Review alert history per device

## Performance Tips

### Database Cleanup
Old check results are automatically cleaned up (keeps 500 per device).
Manual cleanup:
```python
python manage.py shell
>>> from apps.monitoring.tasks import cleanup_old_check_results
>>> cleanup_old_check_results(keep_count=500)
```

### Optimizing Checks
- Adjust `check_interval_seconds` per device (default 60s)
- Reduce `timeout_ms` if network is fast (default 1200ms)
- Decrease `retries` for faster failure detection (default 3)
- Increase `failure_threshold` to avoid false alerts (default 3)

### Monitoring Resource Usage
```powershell
# View process info
Get-Process python

# Monitor CPU/Memory
# Use Task Manager or Performance Monitor

# Check database size
# SQLite: check db.sqlite3 file size
# PostgreSQL: SELECT pg_size_pretty(pg_database_size('netwatch'));
```

## Security Best Practices

1. **Never expose NetWatch to the public internet**
   - Internal network only
   - Use VPN for remote access

2. **Protect credentials**
   - Rotate passwords regularly
   - Use dedicated service accounts
   - Consider credential encryption

3. **Keep software updated**
   - Update Python packages: `pip install --upgrade -r requirements.txt`
   - Apply Windows updates
   - Update Django when security patches released

4. **Monitor logs**
   - Review `logs/netwatch.log` regularly
   - Check for unauthorized access attempts
   - Monitor for unusual activity

5. **Backup regularly**
   - Database backups
   - Configuration backups (.env, settings)
   - Document any customizations

## Support & Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Celery Documentation**: https://docs.celeryproject.org/
- **WinRM Documentation**: https://docs.microsoft.com/en-us/windows/win32/winrm/portal
- **Bootstrap Documentation**: https://getbootstrap.com/docs/

## Logs Location
- Application logs: `logs/netwatch.log`
- Console output when running in terminal

---

**Pro Tip**: Bookmark the dashboard and admin URLs in your browser for quick access!
