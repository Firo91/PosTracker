# Device Status API Testing

## Endpoint
`GET /api/device-status/`

## Authentication
Requires Bearer token in Authorization header (use any valid APIToken from the database)

## Usage

### 1. Get status by device names
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "http://localhost:8000/api/device-status/?devices=Caps,ServerA"
```

### 2. Get status by device IDs
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "http://localhost:8000/api/device-status/?devices=1,2,3"
```

### 3. Get status by IP addresses
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "http://localhost:8000/api/device-status/?devices=10.18.70.36,10.18.70.177"
```

### 4. Get all devices in a unit
```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "http://localhost:8000/api/device-status/?unit=Store1"
```

## Response Format
```json
{
  "status": "success",
  "count": 2,
  "devices": [
    {
      "device_id": 1,
      "device_name": "Caps",
      "ip_address": "10.18.70.36",
      "device_type": "POS",
      "unit": "Store1",
      "location": "Front Desk",
      "enabled": true,
      "status": "UP",
      "agent_healthy": true,
      "reported_at": "2026-01-30T12:00:00Z",
      "uptime_hours": 168.5,
      "uptime_days": 7.0,
      "cpu_percent": 25.5,
      "memory_percent": 60.2,
      "memory_used_gb": 4.8,
      "memory_total_gb": 8.0,
      "disk_percent": 45.0,
      "disk_used_gb": 90.0,
      "disk_free_gb": 110.0,
      "disk_total_gb": 200.0,
      "processes_status": {
        "ServiceHost (POS Program)": {
          "running": true,
          "count": 1
        },
        "ServiceHost (System Service)": {
          "running": true,
          "count": 1
        }
      }
    }
  ]
}
```

## For ChatWarning Integration

The ChatWarning bot can now call this endpoint to get device status and format it nicely in the chat.

Example ChatWarning command implementation:
```
/status Caps ServerA
/status unit:Store1
```

The bot would:
1. Parse the command
2. Call `GET https://your-postracker-url/api/device-status/?devices=Caps,ServerA`
3. Format the response as a chat message
4. Post it to the channel

Token can be stored in ChatWarning's environment variables.
