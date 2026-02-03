# PosTracker User Guide

Welcome to PosTracker! This guide will walk you through everything you need to know to monitor your servers and devices.

## What is PosTracker?

PosTracker monitors your Windows servers and POS terminals 24/7, watching for:
- **Device availability** - Is the server online and responding?
- **System health** - CPU, memory, and disk usage
- **Running services** - Are critical services and processes still running?
- **Uptime** - How long since the last reboot?

When something goes wrong, you'll get alerts automatically via ChatWarning.

---

## Getting Started

### 1. Login to PosTracker

Navigate to **https://pos.kimsit.com** and login with your credentials.

You'll see the **Dashboard** showing all your devices at a glance:
- **Green badge (UP)** = Device is healthy
- **Yellow badge (DEGRADED)** = Device has issues (high CPU, memory, or a service down)
- **Red badge (DOWN)** = Device is offline or unreachable
- **Red (Unhealthy, No contact)** = Agent hasn't reported in for 10+ minutes

---

## Setting Up a New Device

**Overview:** You'll add the device, create an API token, then download a pre-configured agent package. The token gets embedded in the package automatically.

### Step 1: Create the Device

From the dashboard, click **Add Device** in the top right. Fill in:

| Field | What to enter | Example |
|-------|---------------|---------|
| **Device Name** | Friendly name | "Iceland Server" or "POS-Terminal-1" |
| **IP Address** | Static IP of the device | 10.18.70.36 |
| **Unit** | Store/location grouping | Tigerstaden |
| **Device Type** | POS or Server | Server |
| **Enable Ping** | Check for local devices, uncheck for remote | ✗ Unchecked for Iceland |

**For remote devices (Iceland, VPN, etc):** Uncheck "Enable Ping" - the agent is your only indicator of status.

Leave the thresholds at defaults. Click **Create Device**.

### Step 2: Create an API Token

Go to **Dashboard** → **API Tokens** → **Create New Token**

1. **Token Name:** Give it a descriptive name like "Iceland Server" or "POS-01"
2. **Device:** Select the device you just created from the dropdown
3. Click **Create Token**

> **⚠️ Critical:** You MUST select the device. The token won't work without it tied to a specific device.

A token will display. Click **Copy** to save it, but **you don't need to remember it** - it gets added to the agent package automatically.

---

## Installing the Agent

Now download and install the pre-configured agent package on the machine you want to monitor.

### Step 1: Download the Agent Package

Go to **Dashboard** → **Download Agent**

1. Select the device from the dropdown (the one you created)
2. Select the API token you just created from the second dropdown
3. Click **Download Agent Package (ZIP)**

**What's in the ZIP:**
- PowerShell agent script
- Installation scripts
- **Pre-configured agent_config.json** with your server URL, device ID, and API token already filled in
- README with instructions

> **The token is already in the package!** You don't need to copy it or edit the config.

### Step 2: Extract and Run on the Target Machine

1. Copy the ZIP file to the Windows machine you want to monitor
2. Extract the ZIP to a folder (e.g., `C:\PosTracker\agent`)
3. Open Command Prompt or PowerShell **as Administrator**
4. Go to the extracted folder:
   ```
   cd C:\PosTracker\agent
   ```
5. Run the installer:
   ```
   .\INSTALL_AGENT.bat
   ```

The agent will be installed as a Windows scheduled task. It runs automatically every minute.

### Step 3: Verify It's Working

Go back to PosTracker. Within 1-2 minutes, you should see:
- Dashboard shows device as **UP** or **DEGRADED** (green or yellow badge)
- Device detail page shows CPU, memory, disk, uptime
- Agent status shows **Healthy** or **Unhealthy**

### If It Doesn't Show Up

On the Windows machine, run:
```
.\CHECK_STATUS.bat
```

This shows if the agent is running and connected. If not:
- Check that the config.json has the correct server URL
- Check that Windows can reach PosTracker (ping or browser test)
- Check Event Viewer → Application for error messages

If you don't see anything after 2 minutes, check:
1. Is the agent running? (Check Task Manager or Services)
2. Is the API token correct? (Exactly copy-pasted?)
3. Is the server URL correct? (Should be https://pos.kimsit.com)

---

## Monitoring Your Devices

### Dashboard View

The **Dashboard** shows all devices at a glance. Click any device to see detailed status.

### Device Detail Page

This shows everything about a device:

**Agent Status Section:**
- **Health** - Is the agent healthy?
  - Green **Healthy** = All monitored services running
  - Red **Unhealthy** = A service or process is down
  - Red **Unhealthy (No contact)** = Agent hasn't reported in 10+ minutes
  - Below shows: **Down for: 2 hours 15 minutes** if disconnected

**System Metrics:**
- **CPU %** - Current processor usage
- **Memory** - RAM usage (shows actual GB used)
- **Disk** - C: drive usage
- **Uptime** - Hours since last reboot

**Processes & Services:**
Table showing each service/process you're monitoring:
- ✓ **Running** = Service is active
- ✗ **Not Running** = Service is down (action needed!)

**Status Changes Section:**
History of when device status changed (UP → DOWN, etc.)

**Agent Check History:**
Detailed timeline of every check showing metrics over time. Useful for troubleshooting.

---

## Understanding Alerts

Alerts are sent automatically to ChatWarning when something changes.

### Alert Types

| Alert | Meaning | Action |
|-------|---------|--------|
| **Device UP → DOWN** | Device went offline | Check if server is on, network connected, or agent crashed |
| **Device DOWN → UP** | Device came back online | No action needed, but verify everything is working |
| **Ping failed** | Device not responding to ping | Network issue (for ping-enabled devices only) |
| **Agent Unhealthy** | A service or process stopped | See the "Not Running" items in processes section |
| **Agent DOWN** | Agent stopped sending reports (10+ min) | Agent crashed or network issue |
| **CPU High** | CPU usage above threshold (default 85%) | Server is overloaded - check what's running |
| **Memory High** | Memory usage above threshold (default 85%) | Server needs more RAM or has a memory leak |
| **Disk Full** | Disk usage above threshold (default 90%) | Clean up old files or add more storage |
| **Reboot Needed** | Uptime over 30 days | Schedule a reboot at convenient time |

### Severity Levels

- 🔴 **Critical** - Device is DOWN
- 🟠 **Warning** - DEGRADED status, high resource usage, or agent unhealthy
- 🟢 **Info** - Status recovered, device came UP

---

## Common Tasks

### Finding Why a Device is Down

1. Go to **Dashboard**
2. Find the red device
3. Click it to see details
4. Check **System Status** to see:
   - Is agent reporting? (If "No contact" → agent crashed)
   - Is ping working? (If disabled, agent is only indicator)
   - What's in the "Not Running" section?

### Starting a Failed Service

If a service shows "Not Running":

1. **SSH or RDP** into the device
2. Open **Services** (services.msc)
3. Find the service in the "Not Running" column
4. Right-click → **Start**
5. Check back in PosTracker (takes 1-2 minutes to update)

### Checking Recent History

To see what happened in the last hour/day:

1. Go to device detail page
2. Click **1 Hour** or **6 Hours** button (top right)
3. Scroll down to see "Agent Check History"
4. This shows exact CPU, memory, and process status at each check

### Monitoring Multiple Stores

If you manage multiple units:

1. Dashboard shows all devices grouped by status
2. Use the **Unit** dropdown (if available) to filter by location
3. Or click individual device names to jump to that device

### Testing the Agent

To verify the agent is working:

1. Check **Agent Status** on device detail page
2. If **Health: Healthy** and metrics showing → Agent working
3. If **Health: Unhealthy** → A service you're monitoring is down
4. If **Health: Unhealthy (No contact)** → Agent not running or crashed

---

## Troubleshooting

### "Device shows DOWN but I know it's online"

**Check 1: Is Ping enabled?**
- For local devices on your network: Ping should be on
- For remote devices (Iceland): Ping should be OFF, agent only

**Check 2: Try pinging manually**
```powershell
ping 10.18.70.36
```
If you can't ping, it's a network issue, not PosTracker.

**Check 3: Is the agent running?**
- RDP/SSH to the device
- Check Task Manager → Services or run: `tasklist | findstr agent`
- If not running, restart it or check config.json

### "Agent shows DOWN (No contact) but device is UP"

**This means:** Device is online but agent hasn't reported in 10+ minutes.

**Quick fix:**
1. RDP/SSH to the device
2. Check if the agent process is running
3. Restart the agent: `net stop PosTrackerAgent` then `net start PosTrackerAgent`
4. Wait 1-2 minutes
5. Check PosTracker again

**Why it happens:**
- Agent crashed
- Network connectivity issue
- Agent process got killed

### "I installed the agent but it's not showing up in PosTracker"

**Checklist:**
1. ✓ Did you create an API token? (Required!)
2. ✓ Did you paste the token in config.json?
3. ✓ Is the agent actually running? (Check Services or Task Manager)
4. ✓ Is the server URL correct? (Should be https://pos.kimsit.com)
5. ✓ Did you wait 2+ minutes? (First report takes a moment)

Check agent logs:
```powershell
# If running as service, check Event Viewer
# Windows Logs → Application

# If running manually, look at console output
```

### "CPU/Memory shows very high"

This is real data - something on that device is using resources.

**What to do:**
1. RDP into the device
2. Open Task Manager
3. Sort by CPU % or Memory %
4. Find the process using the most
5. Is it normal? (Example: Database backup job?)
6. If abnormal, close it or investigate

PosTracker just reports it - you decide if it's a problem.

### "A service shows 'Not Running' but it should be running"

**Quick fix:**
1. RDP into the device
2. Open Services (services.msc)
3. Find the service by name
4. Right-click → Start

**To prevent this in future:**
1. Set service to **Automatic** startup (not Manual)
2. Add a restart policy in Windows Service properties

---

## Tips & Tricks

### Best Practices

1. **Add descriptive names** - "Iceland Server" is better than "server1"
2. **Group by unit** - Assign each device to its unit/store location
3. **Monitor critical services only** - Don't monitor every service, just the ones you care about
4. **Check regularly** - Glance at the dashboard daily to catch issues early
5. **Set up alerts in ChatWarning** - Make sure you're getting notifications

### What to Monitor

**Essential Services:**
- Any database services (MSSQLSERVER, MySQL)
- Web server (IIS, Apache)
- Any business-critical applications

**Essential Processes:**
- Main application executable
- Backup or sync processes
- Monitoring or agent processes

### Performance Tips

1. **Don't lower check interval below 60 seconds** - Wastes resources
2. **On slow networks, increase timeout** - Set to 2000ms or higher
3. **For remote devices, disable ping** - Reduces false "DOWN" alerts
4. **Archive old data regularly** - PosTracker keeps all history; this can grow large

---

## Getting Help

If something isn't working:

1. **Check the dashboard** - What color is the device?
2. **Check device detail page** - Is agent reporting? What's the last status?
3. **Check agent logs** - Is the agent actually running?
4. **Check the config** - API token correct? Server URL correct?
5. **Restart the agent** - Often fixes "No contact" issues

If you get stuck, contact your administrator with:
- Device name
- Device IP address
- Last time it was working
- What you see in PosTracker now
- What you see in agent logs

---

## Quick Reference

### URLs
- **Dashboard**: https://pos.kimsit.com/dashboard/
- **Add Device**: https://pos.kimsit.com/dashboard/devices/add/
- **API Tokens**: https://pos.kimsit.com/dashboard/tokens/

### Agent Commands
```powershell
# Start agent (if stopped)
net start PosTrackerAgent

# Stop agent (to troubleshoot)
net stop PosTrackerAgent

# View agent logs (Windows Event Viewer)
# Windows Logs → Application → look for "PosTracker"

# Manual run (for testing)
cd "C:\Program Files\PosTracker Agent"
python agent.py
```

### Default Thresholds
- CPU Alert: 85%
- Memory Alert: 85%
- Disk Alert: 90%
- Uptime Alert: 30 days (time for reboot)
- Agent Offline: 10 minutes no report

---

## Questions?

This guide covers 95% of what you need to know. PosTracker is designed to be simple - add devices, install agents, and get alerts. That's it!

For specific issues or advanced configuration, ask your administrator.

Happy monitoring! 🎯
