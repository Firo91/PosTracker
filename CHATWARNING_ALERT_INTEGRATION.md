# PosTracker Alert Integration for ChatWarning

This document describes how PosTracker sends alerts to ChatWarning and what alerts are triggered.

## Overview

The `postracker_integration.py` module in the PosTracker root directory handles all communication with ChatWarning. It uses **JWT Bearer Token authentication** to send alerts via the ChatWarning API.

## Alert Scenarios

PosTracker monitors devices and sends alerts to ChatWarning for these **4 scenarios**:

### 1. Ping Goes DOWN → Send Alert
- **Trigger**: Device ping fails or timeout occurs
- **Status**: Device switches to `DOWN` or `DEGRADED`
- **Alert Title**: `DeviceName (UnitName): UP → DOWN`
- **Alert Type**: `STATUS_CHANGE`
- **Severity**: `warning`

### 2. Ping Comes UP → Send Recovery Alert
- **Trigger**: Device ping succeeds after previous failure
- **Status**: Device switches from `DOWN`/`DEGRADED` to `UP`
- **Alert Title**: `DeviceName (UnitName): DOWN → UP`
- **Alert Type**: `STATUS_CHANGE`
- **Severity**: `info`

### 3. Agent Goes DOWN → Send Alert
- **Trigger**: Agent stops reporting or reports unhealthy status (failed processes/services)
- **Status**: Device switches to `DEGRADED` or `DOWN`
- **Alert Title**: `DeviceName (UnitName): UP → DEGRADED` or `UP → DOWN`
- **Alert Type**: `STATUS_CHANGE`
- **Severity**: `warning`

### 4. Agent Comes UP → Send Recovery Alert
- **Trigger**: Agent reports healthy status after previous failures
- **Status**: Device switches to `UP`
- **Alert Title**: `DeviceName (UnitName): DEGRADED → UP`
- **Alert Type**: `STATUS_CHANGE`
- **Severity**: `info`

## Alert Message Format

Example alerts sent to ChatWarning:

```
Title: "Caps (Tigerstaden): UP → DOWN"
Description: "Device status update: DOWN. Reason: Ping failed"
Channel: "alerts"
Severity: "warning"
```

```
Title: "Caps (Tigerstaden): DOWN → UP"
Description: "Device status update: UP. Reason: Ping OK and agent healthy"
Channel: "alerts"
Severity: "info"
```

## Configuration

### Environment Variables Required

Set these in PosTracker's `.env` file:

```bash
# ChatWarning API
ALERT_CHAT_BASE_URL=https://chat.kimsit.com
ALERT_CHAT_USER=your_admin_username
ALERT_CHAT_PASS=your_admin_password
```

### Django Settings

In `netwatch/settings.py`:

```python
# Alert modes (choose one)
# Option 1: Send alert on every status change (recommended for ChatWarning)
ALERT_STATUS_ALERT_ONCE_PER_STATUS = False  # Default: sends on every change

# Option 2: Send alert only once per status
ALERT_STATUS_ALERT_ONCE_PER_STATUS = True   # Only sends when status changes

# Option 3: Send status update on every check (verbose)
ALERT_SEND_STATUS_EVERY_CHECK = False  # Default: disabled
```

## How Alerts Are Triggered

### Monitoring Flow

1. **Celery Beat** runs `run_all_monitoring_checks` every minute
2. For each enabled device, `check_device` task executes:
   - **Ping Check** (if `device.ping_enabled = True`)
     - Pings device IP address
     - Records: `check_result.ping_ok` (True/False)
   - **Agent Check** (if agent data exists)
     - Checks if agent report is fresh (< 10 minutes old)
     - Records: `agent_healthy` (True/False/None)
3. **Status Computation**
   - Combines ping and agent status to determine overall device status
   - Possible statuses: `UP`, `DEGRADED`, `DOWN`
4. **Status Change Detection**
   - Compares new status with device's last known status
   - If different, triggers alert
5. **Alert Sending**
   - Calls `send_device_alert()` in `postracker_integration.py`
   - Uses JWT Bearer token to authenticate with ChatWarning
   - Sends formatted alert with device name, unit name, and status transition

### Device Status Logic

```python
# Status is determined as follows:
if ping_enabled:
    if ping_ok:
        overall_status = UP if agent_healthy else DEGRADED
    else:
        overall_status = DOWN (even if agent is healthy)
else:
    # Ping disabled - use agent only
    overall_status = UP if agent_healthy else DOWN/DEGRADED
```

## Examples

### Example 1: Local Device Ping Failure

1. Device "Caps" normally UP (pings successfully)
2. Network issue causes ping to fail
3. Status changes: `UP → DOWN`
4. Alert sent:
   ```
   Title: "Caps (Tigerstaden): UP → DOWN"
   Severity: "warning"
   ```
5. When network recovers and ping succeeds again:
   ```
   Title: "Caps (Tigerstaden): DOWN → UP"
   Severity: "info"
   ```

### Example 2: Remote Device Agent Failure

1. Device "Iceland" has ping disabled (agent-only monitoring)
2. Agent reports: CPU=45%, memory=60%, all services healthy → `UP`
3. One service crashes
4. Agent reports: one process unhealthy → `DEGRADED`
5. Status changes: `UP → DEGRADED`
6. Alert sent:
   ```
   Title: "Iceland (Remote): UP → DEGRADED"
   Severity: "warning"
   ```
7. When service restarts and agent reports healthy:
   ```
   Title: "Iceland (Remote): DEGRADED → UP"
   Severity: "info"
   ```

### Example 3: Complete Agent Failure

1. Device "ServerA" normally `UP`
2. Agent stops sending reports (no update > 10 minutes)
3. Status changes: `UP → DOWN`
4. Alert sent:
   ```
   Title: "ServerA (HQ): UP → DOWN"
   Severity: "warning"
   Reason: "No recent agent data"
   ```

## API Integration Details

### Authentication

- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **Token Fetch**: Automatic via `/api/token/` endpoint
- **Token Caching**: 23-hour cache to minimize requests

### ChatWarning Endpoints Used

1. **GET `/api/chat/channels/`** - Fetch available channels
   - Returns list of channels (used to get `alerts` channel ID)
   
2. **POST `/api/chat/alerts/`** - Send alert
   - Accepts: `channel`, `app_name`, `severity`, `title`, `description`
   - Returns: 200/201 on success

### Error Handling

If ChatWarning is unreachable or authentication fails:
- Errors logged to PosTracker logs
- Alert not sent but monitoring continues
- Automatic retry on next device check

## Testing

### Manual Test (via Django Shell)

```python
python manage.py shell

from postracker_integration import send_device_alert

# Test alert sending
result = send_device_alert(
    device_name='TestDevice',
    status='DOWN',
    alert_type='STATUS_CHANGE',
    message='Test alert from PosTracker',
    channel_name='alerts',
    previous_status='UP',
    severity='warning',
    unit_name='TestUnit'
)

print(f"Alert sent: {result}")
```

### Check Logs

```bash
# View recent alerts
tail -100 logs/postracker.log | grep -i alert

# View ChatWarning integration details
grep -i "chatwarning" logs/postracker.log
```

## Status Codes

| Status | Meaning | Color | Severity |
|--------|---------|-------|----------|
| `UP` | Device healthy (ping OK, agent healthy) | 🟢 Green | info |
| `DEGRADED` | Device reachable but issues detected (agent unhealthy) | 🟡 Yellow | warning |
| `DOWN` | Device unreachable (ping failed, no agent data) | 🔴 Red | warning |

## Important Notes

1. **Ping Disabled**: Remote devices (like Iceland) should have `device.ping_enabled = False` so they're monitored by agent only
2. **Unit Names**: Alerts include unit name in format "DeviceName (UnitName)" for quick identification
3. **One Alert Per Status Change**: By default, one alert is sent per status transition (not on every check)
4. **Channel Required**: 'alerts' channel must exist in ChatWarning
5. **Timezone**: Alerts use server's timezone (set in Django settings)

## Troubleshooting

### Alerts Not Sending?

1. Check environment variables are set:
   ```bash
   python manage.py shell
   import os
   print(os.getenv('ALERT_CHAT_BASE_URL'))
   ```

2. Check ChatWarning is running and accessible:
   ```bash
   curl -I https://chat.kimsit.com
   ```

3. Check logs for errors:
   ```bash
   grep "ChatWarning" logs/postracker.log
   ```

4. Verify channel exists in ChatWarning with exact name 'alerts'

5. Check JWT token can be obtained:
   ```python
   from postracker_integration import ChatWarningIntegration
   integration = ChatWarningIntegration()
   token = integration._get_token()
   print(f"Token obtained: {bool(token)}")
   ```

### Getting 401 Unauthorized?

1. Verify credentials are correct:
   ```bash
   echo "User: $(echo $ALERT_CHAT_USER)"
   echo "Pass: $(echo $ALERT_CHAT_PASS | wc -c) characters"
   ```

2. Test token endpoint manually:
   ```bash
   curl -X POST https://chat.kimsit.com/api/token/ \
     -d "username=YOUR_USER&password=YOUR_PASS"
   ```

3. Check token expiry hasn't passed (23-hour cache)

## Version History

- **v1.0** - Initial JWT bearer token authentication
- **v1.1** - Added unit names to alert titles
- **v1.2** - Dynamic device status based on ping + agent health
