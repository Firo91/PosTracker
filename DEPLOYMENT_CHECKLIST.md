# NetWatch Deployment Checklist

## Pre-Deployment

- [ ] Python 3.11+ installed on server
- [ ] PostgreSQL installed and configured (production)
- [ ] Redis installed (if using Celery)
- [ ] Network access to monitored devices verified
- [ ] WinRM enabled on target devices
- [ ] Firewall rules configured (allow WinRM port 5985/5986)

## Installation

- [ ] Clone repository to server
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env`
- [ ] Configure `.env` with production settings
- [ ] Generate Django secret key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- [ ] Set `DEBUG=False` in `.env`
- [ ] Configure `ALLOWED_HOSTS` in `.env`
- [ ] Configure database settings (PostgreSQL)
- [ ] Configure email settings for alerts
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Collect static files: `python manage.py collectstatic`

## Configuration

- [ ] Log in to Django Admin
- [ ] Create Credential Profiles for remote access
- [ ] Add all devices to monitor
- [ ] Configure monitoring settings per device
- [ ] Enable devices for monitoring
- [ ] Test email alerts: `python manage.py test_alerts`

## Monitoring Setup

### Option A: Celery (Recommended)
- [ ] Install Redis
- [ ] Start Redis service
- [ ] Test Celery worker: `celery -A netwatch worker -l info --pool=solo`
- [ ] Test Celery beat: `celery -A netwatch beat -l info`
- [ ] Configure Celery as Windows service (nssm or similar)

### Option B: Task Scheduler
- [ ] Edit `task_scheduler_template.xml` with correct paths
- [ ] Import task: `schtasks /Create /XML task_scheduler_template.xml /TN "NetWatch Monitoring"`
- [ ] Verify task in Task Scheduler
- [ ] Run task manually to test

## Testing

- [ ] Run manual check: `python manage.py run_monitoring`
- [ ] Verify check results in admin
- [ ] Check dashboard displays correctly
- [ ] Test device detail pages
- [ ] Verify alerts are sent on status change
- [ ] Test ping checks work
- [ ] Test RDP checks work
- [ ] Test WinRM service checks work
- [ ] Test WinRM process checks work

## Web Server Setup

### Development
- [ ] Run with: `python manage.py runserver 0.0.0.0:8000`

### Production (Choose one)

#### Waitress (Simple Windows option)
- [ ] Install: `pip install waitress`
- [ ] Run: `waitress-serve --listen=*:8000 netwatch.wsgi:application`
- [ ] Configure as Windows service

#### IIS (Enterprise Windows option)
- [ ] Install IIS with CGI support
- [ ] Install wfastcgi: `pip install wfastcgi`
- [ ] Configure IIS site
- [ ] Set up application pool
- [ ] Configure web.config

#### Gunicorn + Nginx (Linux option)
- [ ] Install Gunicorn
- [ ] Create systemd service
- [ ] Configure Nginx reverse proxy

## Security

- [ ] Credentials stored securely
- [ ] `.env` file not in version control
- [ ] `DEBUG=False` in production
- [ ] Secret key is secure and unique
- [ ] WinRM configured with HTTPS (production)
- [ ] Firewall rules restrict access appropriately
- [ ] Database credentials secured
- [ ] Email credentials secured
- [ ] Application accessible only from internal network or via VPN

## Monitoring & Maintenance

- [ ] Set up log rotation
- [ ] Monitor application logs: `logs/netwatch.log`
- [ ] Monitor disk space (check results database growth)
- [ ] Schedule database backups
- [ ] Document escalation procedures
- [ ] Train staff on using dashboard
- [ ] Document device onboarding process

## Post-Deployment

- [ ] Verify monitoring is running 24/7
- [ ] Confirm alerts are being received
- [ ] Monitor application performance
- [ ] Check for any errors in logs
- [ ] Verify all devices are being monitored
- [ ] Document any customizations made
- [ ] Schedule regular reviews of monitored devices

## Troubleshooting Contacts

- Application Issues: ___________________________
- Network Issues: ___________________________
- WinRM Issues: ___________________________
- Database Issues: ___________________________

## Notes

_______________________________________________
_______________________________________________
_______________________________________________
_______________________________________________
