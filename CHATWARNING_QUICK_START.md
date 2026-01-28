# ChatWarning Integration - Quick Start

## What's Ready to Deploy

Your PosTracker now has a complete automatic alert system. Here's what you need to do:

### 1. Deploy to Heroku
```bash
git add .
git commit -m "Add ChatWarning integration with automatic alerts"
git push heroku main
```

### 2. Set Environment Variables (CRITICAL!)
```bash
heroku config:set -a your-postracker-app \
  ALERT_CHAT_BASE_URL='https://chatwarning.herokuapp.com' \
  ALERT_CHAT_USER='admin' \
  ALERT_CHAT_PASS='your-password'
```

### 3. Create Alert Channel in ChatWarning
1. Go to ChatWarning admin panel
2. Create channel: **`alerts`**
3. Mark as **Alert Channel** (is_alert_channel=true)

### 4. Done! 
Alerts will automatically send when:
- ✅ Any process/service goes down
- ✅ CPU usage > 85%
- ✅ RAM usage > 85%
- ✅ Storage usage > 90%
- ✅ Device running > 30 days

---

## Optional: Customize Alert Thresholds
```bash
heroku config:set -a your-postracker-app \
  ALERT_CPU_THRESHOLD='80' \
  ALERT_MEMORY_THRESHOLD='80' \
  ALERT_DISK_THRESHOLD='85' \
  ALERT_UPTIME_THRESHOLD_DAYS='20'
```

---

## Files Changed
- ✅ Created: `postracker_integration.py` (351 lines)
- ✅ Updated: `requirements.txt` (added requests)
- ✅ Updated: `netwatch/settings.py` (alert config)
- ✅ Updated: `apps/monitoring/tasks.py` (alert checking)
- ✅ Updated: `POSTRACKER_SETUP.md` (setup guide)
- ✅ Created: `CHATWARNING_INTEGRATION_IMPLEMENTED.md` (details)

---

## Test It
```bash
# After deployment, check logs
heroku logs --tail -a your-postracker-app | grep "alert"

# Should see messages like:
# Sending CPU alert for SERVER-01: 92.5%
# Sending process alert for SERVER-01: IIS down
```

---

## How It Works
1. Agent sends report → Device check runs → Metrics compared to thresholds → Alert sent to ChatWarning
2. No code changes needed on devices - completely automatic
3. Alerts appear in ChatWarning dashboard in real-time

That's it! 🎯
