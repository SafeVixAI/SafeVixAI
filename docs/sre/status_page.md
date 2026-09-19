# SafeVixAI â€" Public Status Page

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

A simple, self-hosted status page for monitoring SafeVixAI service health.

## Implementation

The status page is a lightweight HTML page that polls service health endpoints
and displays current status with historical uptime.

### Location
- Frontend: `frontend/app/status/page.tsx`
- API health checks: `/api/v1/status/health`

### Health Check Endpoint

```python
# backend/api/v1/status.py
@router.get('/health')
async def status_health():
    return {
        'status': 'operational',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'backend': await check_backend(),
            'chatbot': await check_chatbot(),
            'database': await check_database(),
            'redis': await check_redis(),
        }
    }
```

### Status Levels
- **Operational** (green): All systems functioning normally
- **Degraded** (yellow): Some services experiencing issues
- **Outage** (red): Critical services unavailable
- **Maintenance** (blue): Scheduled maintenance in progress

### Uptime Monitoring
- Uses simple ping checks every 60 seconds
- Stores last 30 days of status history in Redis
- Displays uptime percentage per service

### Self-Hosting
For initial demo, use a simple static page:
```html
<!DOCTYPE html>
<html>
<head>
  <title>SafeVixAI Status</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 2rem auto; }
    .status { padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }
    .operational { background: #dcfce7; color: #166534; }
    .degraded { background: #fef9c3; color: #854d0e; }
    .outage { background: #fee2e2; color: #991b1b; }
  </style>
</head>
<body>
  <h1>SafeVixAI System Status</h1>
  <div id="status">Loading...</div>
  <script>
    fetch('/api/v1/status/health')
      .then(r => r.json())
      .then(data => {
        const status = data.status;
        const cls = status === 'operational' ? 'operational' : 
                    status === 'degraded' ? 'degraded' : 'outage';
        document.getElementById('status').className = `status ${cls}`;
        document.getElementById('status').textContent = 
          `All systems ${status} as of ${data.timestamp}`;
      });
    // Refresh every 60 seconds
    setInterval(() => location.reload(), 60000);
  </script>
</body>
</html>
```

### Third-Party Alternatives
For production, consider:
- **Statuspal**: Free tier for 1 status page
- **Atlassian Statuspage**: Free for public status pages
- **UptimeRobot**: Free tier with 50 monitors
- **Better Stack**: Free tier with 10 monitors
