# PosTracker ChatWarning Integration - Implementation Summary

## What's Been Implemented

You now have a complete automatic alert system that sends warnings to ChatWarning when:

1. **Process/Service Down** - Any monitored service or process stops running
2. **CPU Too High** - CPU usage exceeds threshold (default: 85%)
3. **RAM Too High** - Memory usage exceeds threshold (default: 85%)
4. **Storage Too High** - Disk usage exceeds threshold (default: 90%)
5. **Equipment Running Too Long** - Uptime exceeds 30 days (recommends reboot)

---

## Files Created/Modified

### New Files
- **`postracker_integration.py`** - Integration module with alert functions
  - `send_device_alert()` - Send custom alerts
  - `send_process_alert()` - Send process down alerts
  - `send_cpu_alert()` - Send CPU high alerts
  - `send_memory_alert()` - Send memory high alerts
  - `send_storage_alert()` - Send storage high alerts
  - `send_uptime_alert()` - Send uptime alerts

### Modified Files
- **`requirements.txt`** - Added `requests>=2.31.0` dependency
- **`netwatch/settings.py`** - Added alert configuration:
  - `ALERT_CHAT_BASE_URL` - ChatWarning base URL
  - `ALERT_CHAT_USER` - ChatWarning admin username
  - `ALERT_CHAT_PASS` - ChatWarning admin password
  - `ALERT_CPU_THRESHOLD` - CPU alert threshold (default: 85%)
  - `ALERT_MEMORY_THRESHOLD` - Memory alert threshold (default: 85%)
  - `ALERT_DISK_THRESHOLD` - Disk alert threshold (default: 90%)
  - `ALERT_UPTIME_THRESHOLD_DAYS` - Uptime alert threshold (default: 30)
  
- **`apps/monitoring/tasks.py`** - Added alert checking logic:
  - `_check_and_send_alerts()` - Helper function that checks metrics and sends alerts
  - Integrated into `check_device()` task to run after each agent report

- **`POSTRACKER_SETUP.md`** - Updated with complete setup guide and implementation details

---

## How It Works

### Automatic Workflow

```
Agent Reports → Device Check → Alert Thresholds Checked → ChatWarning Alerts
```

1. Agent on device sends report with system metrics
2. PosTracker receives AgentReport
3. `check_device()` task processes the report
4. `_check_and_send_alerts()` checks all metrics against thresholds
5. If any metric exceeds threshold, alert is sent to ChatWarning
6. Alert appears in ChatWarning dashboard in real-time

### Example Flow

When device agent reports:
```json
{
  "device": "SERVER-01",
  "cpu_percent": 92.0,
  "memory_percent": 78.0,
  "disk_percent": 88.0,
  "uptime_hours": 750.0,
  "services_status": {
    "IIS": {"running": false},
    "SQL": {"running": true}
  }
}
```

Alerts sent:
1. **Critical**: IIS service is down
2. **Warning**: CPU at 92.0% (exceeds 85% threshold)

---

## Setup Instructions

### 1. Deploy to Heroku
```bash
git add .
git commit -m "Add ChatWarning integration with automatic alerts"
git push heroku main
```

### 2. Set Environment Variables
```bash
heroku config:set -a your-postracker-app \
  ALERT_CHAT_BASE_URL='https://chatwarning.herokuapp.com' \
  ALERT_CHAT_USER='admin' \
  ALERT_CHAT_PASS='your-admin-password'
```

### 3. Create Alert Channels in ChatWarning
1. Go to ChatWarning admin
2. Create channel named `alerts`
3. Mark as "Alert Channel" (is_alert_channel=true)

### 4. (Optional) Customize Thresholds
```bash
heroku config:set -a your-postracker-app \
  ALERT_CPU_THRESHOLD='80' \
  ALERT_MEMORY_THRESHOLD='80' \
  ALERT_DISK_THRESHOLD='85' \
  ALERT_UPTIME_THRESHOLD_DAYS='20'
```

### 5. Verify Agents Are Running
Make sure agents on your devices are configured to send reports to PosTracker.

---

## Testing Locally

```powershell
# Set environment variables
$env:ALERT_CHAT_BASE_URL = "http://localhost:8000"
$env:ALERT_CHAT_USER = "admin"
$env:ALERT_CHAT_PASS = "your-password"
$env:ALERT_CPU_THRESHOLD = "50"  # Lower for testing

# Run PosTracker
python manage.py runserver 8001

# Create test agent report with high CPU
python manage.py shell
```

```python
from apps.monitoring.models import AgentReport
from apps.inventory.models import Device

device = Device.objects.first()
AgentReport.objects.create(
    device=device,
    hostname='TEST',
    cpu_percent=95.0,  # Exceeds 50% test threshold
    memory_percent=30.0,
    disk_percent=40.0,
    uptime_hours=100.0,
    agent_healthy=True,
    services_status={},
    processes_status={}
)
```

Check ChatWarning dashboard - alert should appear!

---

## Alert Channels

All alerts go to the **`alerts`** channel in ChatWarning.

Each alert includes:
- Device name
- Current value (CPU %, RAM %, Disk %, Uptime hours, or process name)
- Threshold that was exceeded
- Alert type (PROCESS_DOWN, CPU_HIGH, RAM_HIGH, STORAGE_HIGH, UPTIME_LONG)
- Severity level (info, warning, critical)

---

## Troubleshooting

### Check if alerts are being detected
```bash
heroku logs --tail -a your-postracker-app | grep "Sending.*alert"
```

### Check if ChatWarning is receiving alerts
```bash
heroku logs --tail -a your-chatwarning-app | grep "api/alerts"
```

### Verify configuration
```bash
heroku config -a your-postracker-app | grep ALERT
```

### Manual test
```bash
heroku run python manage.py shell -a your-postracker-app
```

```python
from postracker_integration import send_cpu_alert
send_cpu_alert('TEST-DEVICE', 92.0, threshold=85.0)
```

---

## Notes

- Alerts are sent only when thresholds are exceeded
- No spam prevention is implemented yet (same alert can be sent multiple times if metric stays high)
- Uptime alerts check against 30-day threshold (recommend reboot)
- Process alerts are sent only if service/process is found but not running
- All alerts go to the same `alerts` channel
- Integration gracefully handles connection failures (logs error, continues monitoring)

---

## Next: Spam Prevention (Optional)

If you want to prevent repeated alerts for the same condition, consider adding:
1. Alert rate limiting (don't send same alert more than once per hour)
2. Alert deduplication (track sent alerts)
3. Alert recovery notifications (alert when condition clears)

These can be added to `postracker_integration.py` in the future.
