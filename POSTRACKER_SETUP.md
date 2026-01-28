# PosTracker + ChatWarning Integration Setup Guide

Welcome! This document will guide you through integrating your PosTracker monitoring system with ChatWarning for real-time alert notifications. This system automatically sends alerts when processes go down, CPU/RAM/storage usage gets too high, or devices have been running for too long without a reboot.

## Prerequisites
✅ ChatWarning is deployed on Heroku  
✅ You have admin access to both apps  
✅ PosTracker repository is ready for modifications

---

## Step 1: Copy Integration Module to PosTracker

The `postracker_integration.py` file is already in your project root. 

**File Location:** `postracker_integration.py` in project root  
**What it does:** Provides easy API to send alerts from PosTracker to ChatWarning  
**Alert Types Supported:**
- Process/Service down
- CPU usage too high
- Memory (RAM) usage too high
- Disk/Storage usage too high
- Device uptime exceeds threshold (recommends reboot)
- Device status changes (UP/DOWN/DEGRADED)

---

## Step 2: Update PosTracker requirements.txt

Add `requests>=2.31.0` to your `requirements.txt` - this has already been added for you!

The integration module uses the `requests` library to make HTTP requests to ChatWarning.

---

## Step 3: Create Alert Channels in ChatWarning

Go to your ChatWarning app and create these channels:

1. **alerts** - All system alerts (processes, CPU, RAM, storage, uptime)
2. **server-monitoring** - Device status changes (UP/DOWN/DEGRADED) [OPTIONAL]

Each channel should be marked as "Alert Channel" (is_alert_channel=true)

---

## Step 4: Set Environment Variables on PosTracker Heroku App

Run these commands (replace with your actual values):

```bash
heroku config:set -a your-postracker-app \
  ALERT_CHAT_BASE_URL='https://chatwarning.herokuapp.com' \
  ALERT_CHAT_USER='admin' \
  ALERT_CHAT_PASS='your-admin-password-here'
```

### Optional: Configure Alert Thresholds

You can customize when alerts trigger:

```bash
heroku config:set -a your-postracker-app \
  ALERT_CPU_THRESHOLD='85' \
  ALERT_MEMORY_THRESHOLD='85' \
  ALERT_DISK_THRESHOLD='90' \
  ALERT_UPTIME_THRESHOLD_DAYS='30'
```

**Environment Variables Explained:**
- `ALERT_CHAT_BASE_URL` - ChatWarning app URL (e.g., https://chatwarning.herokuapp.com)
- `ALERT_CHAT_USER` - ChatWarning admin username
- `ALERT_CHAT_PASS` - ChatWarning admin password
- `ALERT_CPU_THRESHOLD` - CPU alert threshold % (default: 85)
- `ALERT_MEMORY_THRESHOLD` - Memory alert threshold % (default: 85)
- `ALERT_DISK_THRESHOLD` - Disk alert threshold % (default: 90)
- `ALERT_UPTIME_THRESHOLD_DAYS` - Uptime alert threshold in days (default: 30)

---

## Step 5: How Alerts Work

### Automatic Alerts Sent By PosTracker

Alerts are automatically checked and sent whenever an agent report is received. The system checks:

1. **Process Alerts** - Any monitored service/process that's not running
2. **CPU Alerts** - When CPU usage exceeds the threshold
3. **Memory Alerts** - When RAM usage exceeds the threshold  
4. **Disk Alerts** - When storage usage exceeds the threshold
5. **Uptime Alerts** - When device has been running > 30 days (reminder to reboot)

### Example: How It Works

```
Agent Report Received → Check Device Metrics → Thresholds Exceeded? → Send Alert to ChatWarning
```

When an agent sends a report like:
```json
{
  "hostname": "SERVER-01",
  "cpu_percent": 92.5,  // <-- EXCEEDS 85% THRESHOLD
  "memory_percent": 78.2,
  "disk_percent": 85.0,
  "uptime_hours": 750.5,
  "services_status": {
    "IIS": {"running": false}  // <-- PROCESS DOWN!
  },
  "agent_healthy": false
}
```

PosTracker automatically sends TWO alerts:
1. IIS service is down (critical alert)
2. CPU usage at 92.5% (warning alert)

---

## Step 6: View Alerts

### In ChatWarning Dashboard

1. Login to your ChatWarning app
2. Go to the **alerts** channel
3. You'll see real-time notifications as they arrive

Each alert includes:
- Device name
- Alert type (PROCESS_DOWN, CPU_HIGH, RAM_HIGH, STORAGE_HIGH, UPTIME_LONG)
- Current metric value
- Threshold that was exceeded
- Severity level (info, warning, critical)

---

## Step 7: Test the Integration Locally (Optional)

Before pushing to production, test locally:

### 1. Start ChatWarning locally
```bash
cd alert_chat_system
daphne -b 0.0.0.0 -p 8000 alert_system.asgi:application
```

### 2. Expose with ngrok
```bash
ngrok http 8000
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

### 3. Set Local Environment Variables
```powershell
$env:ALERT_CHAT_BASE_URL = "https://abc123.ngrok.io"
$env:ALERT_CHAT_USER = "admin"
$env:ALERT_CHAT_PASS = "your-password"
$env:ALERT_CPU_THRESHOLD = "50"  # Lower for testing
$env:ALERT_MEMORY_THRESHOLD = "50"  # Lower for testing
```

### 4. Run PosTracker
```bash
python manage.py runserver 8001
```

### 5. Trigger a Check

Create a test agent report with high CPU:

```python
from apps.monitoring.models import AgentReport
from apps.inventory.models import Device

device = Device.objects.get(name='YOUR_TEST_DEVICE')
AgentReport.objects.create(
    device=device,
    hostname='TEST_DEVICE',
    cpu_percent=95.0,  # Will trigger alert at 50% threshold
    memory_percent=30.0,
    disk_percent=40.0,
    uptime_hours=100.0,
    processes_status={},
    services_status={},
    agent_healthy=True
)
```

You should see alerts appear in ChatWarning within seconds!

---

## Alert Types & Severity

| Alert Type | Status | Severity | Trigger |
|------------|--------|----------|---------|
| PROCESS_DOWN | DOWN | critical | Any monitored service/process not running |
| CPU_HIGH | WARNING | warning | CPU % > threshold (default 85%) |
| RAM_HIGH | WARNING | warning | Memory % > threshold (default 85%) |
| STORAGE_HIGH | WARNING | warning | Disk % > threshold (default 90%) |
| UPTIME_LONG | WARNING | info | Uptime > threshold (default 30 days) |
| STATUS_CHANGE | Varies | Varies | Device status changes (UP/DOWN/DEGRADED) |

---

## Troubleshooting

### Alerts Not Appearing?

1. **Verify environment variables are set:**
   ```bash
   heroku config -a your-postracker-app | grep ALERT
   ```

2. **Check PosTracker logs:**
   ```bash
   heroku logs --tail -a your-postracker-app
   ```
   Look for log messages like:
   ```
   Sending CPU alert for SERVER-01: 92.5%
   Error sending alert to ChatWarning: ...
   ```

3. **Verify agent is sending reports:**
   Check that the agent on your devices is running and sending reports to PosTracker.
   In Django admin: `Monitoring > Agent Reports` should show recent entries.

4. **Test the connection manually:**
   ```bash
   heroku run python manage.py shell -a your-postracker-app
   ```
   Then:
   ```python
   from postracker_integration import send_cpu_alert
   send_cpu_alert(
       device_name='Test Device',
       cpu_percent=95.0,
       threshold=85.0,
       channel_name='alerts'
   )
   ```

### "Channel not found" Error?

- Verify channel exists in ChatWarning
- Check channel name spelling (case-sensitive): `alerts`, not `Alerts`
- Verify admin user has access to the channel

### "Connection refused" Error?

- ChatWarning app is running? Check on Heroku dashboard
- ALERT_CHAT_BASE_URL correct? Should be `https://chatwarning.herokuapp.com` (with https, not http)
- Network firewall blocking requests? This is unlikely on Heroku
- Check PosTracker Heroku logs for details

### Alerts Sending But Not Appearing in ChatWarning?

- Check ChatWarning admin: `Admin > Channels` - is the alerts channel created?
- Verify channel is marked as `is_alert_channel=true`
- Check ChatWarning logs for incoming requests
- Manually refresh ChatWarning dashboard (F5)

---

## Implementation Details

### Where Alerts Are Checked

In `apps/monitoring/tasks.py`, the `_check_and_send_alerts()` function runs after each agent report is received:

```python
@shared_task(bind=True, max_retries=3)
def check_device(self, device_id: int):
    # ... existing monitoring code ...
    
    # Check for alerts and send to ChatWarning
    _check_and_send_alerts(device, latest_agent)
    
    # ... rest of monitoring code ...
```

### Default Thresholds

If you don't set environment variables, these defaults apply:
- CPU Threshold: 85%
- Memory Threshold: 85%
- Disk Threshold: 90%
- Uptime Threshold: 30 days

Customize by setting environment variables on Heroku.

---

## Next Steps

1. ✅ Create alert channels in ChatWarning
2. ✅ Set environment variables on PosTracker Heroku app
3. ✅ Deploy PosTracker with updated code (requests + postracker_integration.py)
4. ✅ Verify agents are sending reports
5. ✅ Monitor ChatWarning dashboard for alerts
6. ✅ Adjust thresholds as needed

---

## Support

For issues or questions:
1. Review the troubleshooting section above
2. Check Heroku logs: `heroku logs --tail -a your-app-name`
3. Check agent logs on monitored devices
4. Review code comments in `postracker_integration.py` and `apps/monitoring/tasks.py`
5. Check ChatWarning admin interface for created channels and incoming alerts
