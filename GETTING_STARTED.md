# Getting Started with NetWatch

Welcome to NetWatch! This guide will walk you through getting the application up and running in just a few minutes.

## Prerequisites

Before you begin, ensure you have:

- ✅ Windows Server 2016+ or Windows 10+
- ✅ Python 3.11 or higher installed
- ✅ Administrator access to your Windows machine
- ✅ Network access to devices you want to monitor

**Check Python version:**
```powershell
python --version
# Should show Python 3.11.0 or higher
```

## Quick Start (5 Minutes)

### Step 1: Download and Extract

Extract the NetWatch application to a folder, for example:
```
C:\NetWatch\
```

### Step 2: Run the Setup Script

Open PowerShell as Administrator in the NetWatch folder and run:

```powershell
.\setup.ps1
```

This script will:
- Create a virtual environment
- Install all dependencies
- Create configuration file
- Set up the database
- Prompt you to create an admin user

**Follow the prompts to create your admin account!**

### Step 3: Start the Application

```powershell
# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Start the server
python manage.py runserver 0.0.0.0:8000
```

### Step 4: Access the Application

Open your web browser and go to:
```
http://localhost:8000
```

**Login with the admin credentials you created in Step 2.**

🎉 **Congratulations! NetWatch is now running!**

## Next Steps

### Add Your First Device

1. Go to **Admin** (http://localhost:8000/admin/)
2. Click **Devices** → **Add Device**
3. Fill in the form:
   - **Name**: `Test-Localhost`
   - **IP Address**: `127.0.0.1`
   - **Device Type**: `Server`
   - **Location**: `Local Testing`
   - **Enable ping checks**: ✓ Checked
   - **Enable RDP checks**: ✗ Unchecked (not needed for localhost)
   - **Simphony check mode**: `No Simphony Check`
4. Click **Save**

### Run Your First Check

Open a new PowerShell window (keep the server running) and run:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run monitoring check
python manage.py run_monitoring
```

You should see output like:
```
Found 1 enabled devices
→ Checking Test-Localhost (127.0.0.1)...
  ✓ Test-Localhost: UP

Monitoring check cycle completed
```

### View Results in Dashboard

Go back to your browser and visit:
```
http://localhost:8000/dashboard/
```

You should see your device listed with a **green "UP" badge**! 🟢

### Create Sample Data (Optional)

Want to see more example devices? Run:

```powershell
python manage.py create_sample_data
```

This creates several sample devices you can use for testing. Don't forget to update their IP addresses to match your network!

## Setting Up Real Device Monitoring

### 1. Create a Credential Profile (for Simphony checks)

If you want to monitor Windows services or processes on remote devices:

1. Go to **Admin** → **Credential Profiles** → **Add**
2. Enter:
   - **Name**: `Local Admin`
   - **Username**: `Administrator` (or your admin username)
   - **Password**: `your-password`
3. Click **Save**

### 2. Add a Real Device

1. Go to **Admin** → **Devices** → **Add Device**
2. Fill in your device details:
   - **Name**: `POS-Terminal-01`
   - **IP Address**: `192.168.1.101` (your device's IP)
   - **Device Type**: `POS`
   - **Location**: `Front Counter`
3. Configure monitoring:
   - ✓ **Enable ping checks**
   - ✓ **Enable RDP checks**
   - **Simphony check mode**: `Check Windows Service`
   - **Service name**: `SimphonyService` (your Simphony service name)
   - **Credential profile**: Select `Local Admin`
4. Click **Save**

### 3. Enable WinRM on the Remote Device

For Simphony service/process checks to work, WinRM must be enabled on the target device.

**On the device you want to monitor** (run as Administrator):

```powershell
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
Restart-Service WinRM
```

**Test WinRM from your monitoring server:**

```powershell
Test-WSMan -ComputerName 192.168.1.101
```

If successful, you'll see XML output showing the WinRM configuration.

### 4. Run a Check

```powershell
python manage.py run_monitoring --device-name "POS-Terminal-01"
```

## Scheduling Automatic Checks

You have two options for running checks automatically:

### Option A: Windows Task Scheduler (Simple)

1. Edit `task_scheduler_template.xml` and update these paths:
   - `<Command>C:\NetWatch\venv\Scripts\python.exe</Command>`
   - `<Arguments>C:\NetWatch\manage.py run_monitoring</Arguments>`
   - `<WorkingDirectory>C:\NetWatch</WorkingDirectory>`

2. Import the task:
```powershell
schtasks /Create /XML task_scheduler_template.xml /TN "NetWatch Monitoring"
```

3. Verify in Task Scheduler (taskschd.msc)

### Option B: Celery (Advanced - Requires Redis)

If you have Redis installed:

**Start Celery Worker (in one terminal):**
```powershell
celery -A netwatch worker -l info --pool=solo
```

**Start Celery Beat (in another terminal):**
```powershell
celery -A netwatch beat -l info
```

Celery Beat will automatically run checks every 60 seconds.

## Setting Up Email Alerts

### 1. Configure Email Settings

Edit your `.env` file:

```env
# For testing (prints to console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# For production (real email)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=netwatch@yourcompany.com
ALERT_EMAIL_RECIPIENTS=admin@example.com,it@example.com
```

### 2. Test Email Configuration

```powershell
python manage.py test_alerts
```

You should receive a test email at the configured addresses.

## Troubleshooting

### "Module not found" errors
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### "No such table" errors
```powershell
# Run database migrations
python manage.py migrate
```

### Can't access from other computers
```powershell
# Make sure you started with 0.0.0.0:8000
python manage.py runserver 0.0.0.0:8000

# Add your server IP to .env ALLOWED_HOSTS
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50
```

### WinRM connection fails
- Verify WinRM is enabled on target: `Test-WSMan -ComputerName <ip>`
- Check firewall allows port 5985
- Verify credentials are correct
- Ensure user has admin privileges on target device

## Where to Go Next

- 📖 Read the full [README.md](README.md) for detailed documentation
- 📋 Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command cheat sheet
- 🚀 Review [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for production deployment
- 📊 Explore the dashboard at http://localhost:8000/dashboard/
- ⚙️ Configure more devices in the admin interface

## Common Tasks

### View Application Logs
```powershell
Get-Content logs\netwatch.log -Tail 50 -Wait
```

### Create Additional Admin Users
```powershell
python manage.py createsuperuser
```

### Check All Devices Now
```powershell
python manage.py run_monitoring
```

### Backup Database (SQLite)
```powershell
Copy-Item db.sqlite3 db.backup.sqlite3
```

## Production Deployment

For production use, see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for:
- PostgreSQL setup
- Web server configuration (Waitress/IIS)
- Security hardening
- Backup strategies
- Monitoring and maintenance

## Getting Help

If you encounter issues:

1. Check the logs: `logs\netwatch.log`
2. Review the troubleshooting section in README.md
3. Verify your configuration in `.env`
4. Check Python and dependency versions
5. Contact your IT department or development team

## Key Files to Know

- **`.env`** - Configuration (database, email, etc.)
- **`logs/netwatch.log`** - Application logs
- **`db.sqlite3`** - SQLite database (development)
- **`manage.py`** - Django management script
- **`requirements.txt`** - Python dependencies

## Security Reminders

⚠️ **Important Security Notes:**

- Keep `.env` file secure (never commit to Git)
- Use strong passwords for admin accounts
- Only run on internal networks or via VPN
- Regularly update dependencies: `pip install --upgrade -r requirements.txt`
- Rotate credential profile passwords periodically
- Monitor logs for suspicious activity

---

**You're all set!** NetWatch is now monitoring your devices. 

Visit the dashboard regularly to check device status, or configure email alerts to be notified automatically of any issues.

Happy monitoring! 🎯
