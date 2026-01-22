# NetWatch Improvements - Completed

All improvements have been successfully implemented. Here's what changed:

## 1. ✅ Reset Log Level to INFO
- **File**: `agent/agent_config.json`
- Changed `log_level` from `DEBUG` to `INFO`
- Reduces verbose logging and improves performance

## 2. ✅ API Token Authentication
- **New Model**: `APIToken` in `apps/inventory/models.py`
  - Unique token per device for secure authentication
  - Tracks token creation and last usage
  - Can be enabled/disabled

- **Updated API**: `apps/monitoring/api_views.py`
  - All agent POSTs now require `Authorization: Bearer <token>` header
  - Returns 401 if token is missing or invalid
  - Logs token usage

- **New Command**: `python manage.py generate_api_token <device_id>`
  - Generates secure random token for each device
  - Shows token in console for agent_config.json

**Setup Instructions**:
```bash
# Generate token for device
python manage.py generate_api_token 100 --name "POS-01"

# Copy token to agent_config.json:
"api_key": "<generated_token>"
```

## 3. ✅ Agent Retry Logic with Exponential Backoff
- **File**: `agent/netwatch_agent.ps1`
- Retries failed POSTs up to 3 times
- Delays: 1s, 2s, 4s between retries
- Falls back gracefully if all retries fail
- Logs each attempt

## 4. ✅ Process Instance Details
- **File**: `agent/netwatch_agent.ps1`
- Each process now includes:
  - Process ID (PID)
  - Memory usage (MB)
  - CPU percentage
- API payload includes `instances` array per process:
```json
"processes": {
  "ServiceHost (POS Program)": {
    "running": true,
    "count": 1,
    "instances": [
      {"pid": 1234, "memory_mb": 125.5, "cpu": 5.2}
    ]
  }
}
```

## 5. ✅ Status Change History
- **New Model**: `StatusChangeHistory` in `apps/monitoring/models.py`
  - Tracks all device status transitions
  - Records reason for change
  - Queryable for reporting

- **Updated Views**: `apps/dashboard/views.py`
  - Device detail page shows recent status changes
  - Displays UP/DEGRADED/DOWN transitions with timestamps

- **Updated Template**: `templates/dashboard/device_detail.html`
  - New "Recent Status Changes" section above check history
  - Shows time, status change, and reason

## 6. ✅ Config Validation
- **File**: `agent/netwatch_agent.ps1`
- Validates on startup:
  - ✓ server_url configured
  - ✓ device_id configured
  - ✓ api_key provided (REQUIRED)
  - ✓ processes configured (warning if missing)
  - ✓ check_interval >= 10 seconds
- Exits with code 1 if validation fails
- Displays clear error messages

## 7. ✅ Data Retention Policy
- **New Task**: `cleanup_old_data()` in `apps/monitoring/tasks.py`
- Runs daily via Celery Beat
- Deletes check results older than 7 days
- Deletes agent reports older than 7 days
- Logs deletion counts

- **Celery Beat Schedule Updated**:
```python
'cleanup-old-data': {
    'task': 'apps.monitoring.tasks.cleanup_old_data',
    'schedule': 86400.0,  # Run daily
}
```

## 8. ✅ Log Level Respect
- **File**: `agent/netwatch_agent.ps1`
- Updated `Write-Log` function to respect log level
- INFO level skips DEBUG messages
- Reduces console spam in production

## 9. ✅ Dashboard Improvements
- Removed services from all views (process-focused)
- Added status change history to device detail
- Cleaner agent payload (processes only)

---

## Database Migrations

Run these to apply all changes:
```bash
python manage.py makemigrations  # Already done
python manage.py migrate          # Already done
```

Two new migrations created:
- `inventory/migrations/0004_apitoken.py` - API token model
- `monitoring/migrations/0004_statuschangehistory.py` - Status history tracking

---

## Next Steps for Production

### 1. Generate API Tokens for All Devices
```bash
# For each device:
python manage.py generate_api_token 100 --name "POS-01"
python manage.py generate_api_token 101 --name "POS-02"
# etc...
```

### 2. Update agent_config.json on Each Agent
Add the generated token:
```json
{
    "server_url": "http://10.18.70.71:8000",
    "device_id": 100,
    "api_key": "<generated_token>",
    "check_interval": 60,
    "processes": [...]
}
```

### 3. Reinstall Agent
```batch
INSTALL_AGENT.bat
```

### 4. Verify Setup
```batch
TEST_AGENT.bat
# Should show successful POST with HTTP 200
```

### 5. Create Django Admin User (if needed)
```bash
python manage.py createsuperuser
```

---

## Security Notes

- API tokens are long random strings (48 bytes, URL-safe)
- Tokens are stored in database and checked on every POST
- Tokens can be regenerated if compromised
- Disabled tokens are ignored
- No password needed for agents (token-based only)

---

## Monitoring & Troubleshooting

### View Token Usage
```bash
# In Django shell:
python manage.py shell
>>> from apps.inventory.models import APIToken
>>> token = APIToken.objects.get(token="<token_string>")
>>> token.last_used
```

### Check Data Cleanup
Look in logs for:
```
INFO - cleanup_old_data - Data retention: deleted X check results and Y agent reports
```

### View Status Changes
```bash
# In Django shell:
>>> from apps.monitoring.models import StatusChangeHistory
>>> changes = StatusChangeHistory.objects.filter(device_id=100)
>>> for c in changes: print(f"{c.changed_at}: {c.old_status} → {c.new_status}")
```

---

## Configuration Summary

**agent_config.json** (Required fields):
```json
{
    "server_url": "http://10.18.70.71:8000",
    "device_id": 100,
    "api_key": "<required>",
    "check_interval": 60,
    "processes": [
        {
            "name": "ServiceHost",
            "label": "ServiceHost (POS Program)",
            "filter": "!-service"
        }
    ],
    "log_level": "INFO",
    "log_file": "netwatch_agent.log"
}
```

---

## Summary of Changes

| Component | Before | After |
|-----------|--------|-------|
| API Auth | None | Token-based (required) |
| Agent Retries | No | 3 retries with backoff |
| Process Details | Count only | Count + instances (PID, memory, CPU) |
| Status History | Not tracked | Full history with reasons |
| Data Cleanup | Manual | Automatic daily |
| Config Validation | Minimal | Comprehensive checks |
| Log Level | Not respected | Fully respected |

All improvements are production-ready and tested!
