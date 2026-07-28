# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# Tutorial: Set up SOS Alerting in 5 Minutes

**Time required:** 5 minutes
**Prerequisites:** Running SafeVixAI instance, JWT token

## Step 1: Open the SOS Page

Navigate to `http://localhost:3000/sos` in your browser. You should see the red SOS button with a circular hold indicator.

## Step 2: Hold to Activate

Press and hold the red SOS button for 2 seconds. The button will:
- Vibrate (on supported devices)
- Show a countdown progress ring
- Activate with a flash animation

Upon activation, the button displays "Dispatch Armed" status with a tracking section below.

## Step 3: Verify the Alert

After activation, check that:
1. A tracking URL is generated (copy it to share with family)
2. An SMS alert is triggered (if emergency contacts are configured)
3. The family tracking section appears with a live shareable link

## Step 4: Test via API

```bash
curl -X POST "http://localhost:8000/api/v1/emergency/sos" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lat": 13.0827, "lon": 80.2707}'
```

Expected response:
```json
{
  "status": "sos_triggered",
  "tracking_url": "http://localhost:3000/track/abc123",
  "emergency_contacts_notified": 2
}
```

## Verification

- The SOS button should show "Dispatch Armed" status
- The backend logs: `Emergency SOS triggered at lat=13.0827, lon=80.2707`
- Family tracking shows "Active" with a shareable link
- Tracking URL at `/track/{session_id}` shows live location

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Button doesn't vibrate | Ensure `navigator.vibrate` is supported (mobile browsers) |
| "Geolocation not supported" | Use HTTPS or localhost; geolocation requires secure context |
| Tracking URL not generated | Check that JWT token includes user profile data |
| SMS not sent | Configure emergency contacts in profile settings |
