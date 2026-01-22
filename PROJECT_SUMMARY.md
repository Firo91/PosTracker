# NetWatch - Project Summary

## Overview
NetWatch is a production-ready Django web application for monitoring Windows POS terminals and servers on an internal LAN. Built with Python 3.11+ and Django 5+, it provides comprehensive device monitoring with ping checks, RDP connectivity tests, and remote Windows service/process monitoring via WinRM.

## Technology Stack
- **Backend**: Python 3.11+, Django 5+
- **Database**: PostgreSQL (production) / SQLite (development)
- **Task Queue**: Celery + Redis (optional, can use Windows Task Scheduler)
- **Frontend**: Bootstrap 5, vanilla JavaScript
- **Remote Access**: WinRM (pywinrm)
- **Server**: Waitress (Windows) / Gunicorn (Linux)

## Core Features

### 1. Device Inventory Management
- CRUD operations for devices (POS terminals and servers)
- Per-device monitoring configuration
- Credential profile management for remote access
- Location tracking and notes
- Enable/disable monitoring per device

### 2. Multi-Level Monitoring
- **Network Ping**: Windows ping command with configurable timeout
- **TCP Port Check**: Socket-based RDP port connectivity test
- **Remote Service Check**: Query Windows service status via WinRM
- **Remote Process Check**: Query running processes via WinRM
- Configurable timeouts, retries, and failure thresholds

### 3. Status Logic
- **UP**: Device reachable, all services running
- **DEGRADED**: Device reachable but Simphony service/process down
- **DOWN**: Device unreachable (both ping and RDP failed)
- **UNKNOWN**: Never checked or insufficient data
- Smart threshold-based status changes to avoid false alerts

### 4. Dashboard & UI
- Real-time status overview with color-coded badges
- Device list with filtering (type, status, location, enabled state)
- Search by name or IP address
- Device detail pages with check history
- Statistics: uptime percentage, check counts, average response times
- Auto-refresh every 30 seconds
- Mobile-responsive Bootstrap 5 design

### 5. Alert System
- Email notifications on status changes
- Configurable recipients
- Alert throttling (10 minute minimum between alerts per device)
- Detailed alert content with check results and errors
- Alert log for audit trail
- Test command to verify email configuration

### 6. Data Management
- Automatic cleanup of old check results (keeps 500 per device)
- Indexed database for performance
- Efficient queries with select_related/prefetch_related
- Timezone-aware timestamps

## Project Structure

```
PosTracker/
├── manage.py                      # Django CLI
├── requirements.txt               # Dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── README.md                      # Full documentation
├── QUICK_REFERENCE.md             # Command cheat sheet
├── DEPLOYMENT_CHECKLIST.md        # Deployment guide
├── setup.ps1                      # Quick setup script
├── start_netwatch.ps1             # Production startup script
├── task_scheduler_template.xml    # Windows Task Scheduler template
├── test_monitoring.py             # Simple test script
│
├── netwatch/                      # Project configuration
│   ├── __init__.py
│   ├── settings.py                # Django settings
│   ├── urls.py                    # URL routing
│   ├── celery.py                  # Celery configuration
│   ├── wsgi.py                    # WSGI entry point
│   └── asgi.py                    # ASGI entry point
│
├── apps/
│   ├── inventory/                 # Device management
│   │   ├── models.py              # Device, CredentialProfile
│   │   ├── admin.py               # Admin interface
│   │   ├── views.py               # API views (future)
│   │   ├── urls.py
│   │   └── management/commands/
│   │       └── create_sample_data.py
│   │
│   ├── monitoring/                # Monitoring engine
│   │   ├── models.py              # CheckResult, AlertLog
│   │   ├── admin.py               # Admin interface
│   │   ├── engine.py              # Core monitoring logic
│   │   ├── tasks.py               # Celery tasks
│   │   ├── alerts.py              # Email alert system
│   │   ├── tests.py               # Unit tests
│   │   └── management/commands/
│   │       ├── run_monitoring.py  # Manual monitoring
│   │       └── test_alerts.py     # Test email config
│   │
│   └── dashboard/                 # Web UI
│       ├── views.py               # Dashboard views
│       ├── urls.py                # Dashboard URLs
│       └── apps.py
│
├── templates/
│   ├── base.html                  # Base template
│   └── dashboard/
│       ├── index.html             # Main dashboard
│       └── device_detail.html     # Device detail page
│
├── static/                        # Static files (CSS/JS)
├── logs/                          # Application logs
└── pids/                          # Process IDs (production)
```

## Key Models

### Device
- Basic info: name, IP, device type, location
- Network checks: ping, RDP port
- Simphony monitoring: service name, process name, check mode
- Check parameters: interval, timeout, retries, thresholds
- Status cache: last_status, last_check_at, consecutive_failures

### CredentialProfile
- Secure storage of Windows credentials
- Reusable across multiple devices
- Fields: username, password, domain, notes

### CheckResult
- Stores results of each monitoring check
- Fields: ping_ok, ping_ms, rdp_ok, rdp_ms, simphony_ok, simphony_status
- Overall status determination
- Error messages and check duration

### AlertLog
- Audit trail of sent alerts
- Tracks recipients, success/failure, timestamps
- Used for alert throttling

## Monitoring Engine

### Check Pipeline (per device)
1. **Ping Check**: `ping -n 1 -w <timeout> <ip>`
2. **RDP Check**: TCP socket connect to port 3389
3. **Simphony Check** (if enabled and device reachable):
   - Service mode: WinRM → `Get-Service -Name <service>`
   - Process mode: WinRM → `Get-Process -Name <process>`

### Status Determination
```python
if not (ping_ok OR rdp_ok):
    return DOWN
elif simphony_check_enabled and not simphony_ok:
    return DEGRADED
else:
    return UP
```

### Threshold Logic
- **failure_threshold**: Consecutive failures before marking DOWN (default: 3)
- **success_threshold**: Consecutive successes to recover (default: 1)
- Prevents flapping and false alerts

## Deployment Options

### Option 1: Celery (Recommended for 24/7)
- Requires Redis
- Automatic scheduled checks (every 60 seconds)
- Better concurrency and scalability
- Run: `celery -A netwatch worker --pool=solo` + `celery -A netwatch beat`

### Option 2: Windows Task Scheduler
- No Redis required
- Simpler setup for single-server deployments
- Schedule: Run `python manage.py run_monitoring` every 1 minute
- Template provided: `task_scheduler_template.xml`

### Option 3: Hybrid
- Web server always running
- Choose monitoring method based on environment

## Security Features
- No hardcoded credentials
- Environment variable configuration
- Django secret key protection
- Credentials not logged
- Admin-only access to dashboard (login required)
- CSRF protection
- SQL injection protection (Django ORM)
- Internal network deployment recommended

## Performance Considerations
- Indexed database fields for fast queries
- Automatic old data cleanup (keeps 500 results per device)
- Efficient ORM queries with select_related
- Configurable check intervals per device
- Timeout controls prevent hanging checks
- Connection pooling for database

## Testing Features
- Unit tests for monitoring engine
- Sample data creation command
- Test monitoring script
- Email alert test command
- Console email backend for testing

## Documentation
- **README.md**: Complete setup and usage guide
- **QUICK_REFERENCE.md**: Command cheat sheet
- **DEPLOYMENT_CHECKLIST.md**: Production deployment steps
- Inline code documentation
- Type hints throughout

## Management Commands
```bash
python manage.py run_monitoring          # Run checks
python manage.py test_alerts             # Test email
python manage.py create_sample_data      # Create test devices
python manage.py createsuperuser         # Create admin
python manage.py migrate                 # Run migrations
python manage.py collectstatic           # Collect static files
```

## Configuration via .env
- Django secret key
- Debug mode
- Allowed hosts
- Time zone
- Database settings (SQLite/PostgreSQL)
- Celery broker URL
- Email SMTP settings
- Alert recipients
- Log level

## Browser Support
- Modern browsers (Chrome, Firefox, Edge, Safari)
- Mobile responsive
- Bootstrap 5 compatibility

## Future Enhancements (Potential)
- [ ] REST API for external integrations
- [ ] Webhook notifications
- [ ] SMS/Slack alerts
- [ ] Custom dashboards per user
- [ ] Historical trend charts
- [ ] Report generation (PDF/Excel)
- [ ] Device groups/categories
- [ ] Scheduled maintenance windows
- [ ] SLA tracking
- [ ] Multi-tenant support

## Known Limitations
- Windows-only monitoring server (uses Windows ping command)
- WinRM requires configuration on target devices
- No built-in HTTPS (use reverse proxy)
- Single language (English)
- Basic authentication (no SSO/LDAP)

## System Requirements

### Monitoring Server
- Windows Server 2016+ (or Windows 10+)
- Python 3.11 or higher
- 2GB RAM minimum (4GB recommended)
- 10GB disk space minimum
- Network access to monitored devices

### Monitored Devices
- Windows (any version with WinRM support)
- Static IP addresses
- WinRM enabled (for Simphony checks)
- Network reachability from monitoring server

### Optional Components
- PostgreSQL 12+ (production database)
- Redis 6+ (Celery message broker)
- SMTP server (email alerts)

## License & Support
- Internal use only
- Not for public distribution
- Support: Contact IT department

## Contributors
- Developed by: [Your Team]
- Maintained by: IT Operations

## Version History
- v1.0.0 (2026-01-08): Initial release
  - Device inventory management
  - Multi-level monitoring (ping, RDP, WinRM)
  - Real-time dashboard
  - Email alerts
  - Celery and Task Scheduler support
  - Complete documentation

---

**NetWatch** - Simple, powerful, production-ready LAN device monitoring for Windows environments.
