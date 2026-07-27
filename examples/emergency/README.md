# Emergency Integration Examples

> **SOS trigger, live tracking, and emergency locator patterns.**

---

## Trigger SOS Programmatically

```python
import httpx

BACKEND = "http://localhost:8000"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Trigger SOS with current location
resp = httpx.post(
    f"{BACKEND}/api/v1/live-tracking/trigger-sos",
    json={"lat": 13.0827, "lon": 80.2707},
    headers=headers,
)
print(resp.json())
```

## Emergency Services Lookup

```python
import httpx

resp = httpx.get(
    "http://localhost:8000/api/v1/emergency/nearby",
    params={"lat": 13.0827, "lon": 80.2707, "radius": 5000},
)

data = resp.json()
print("Hospitals:", [h["name"] for h in data.get("hospitals", [])])
print("Police:", [p["name"] for p in data.get("police", [])])
print("Fire:", [f["name"] for f in data.get("fire", [])])
```

## Offline SOS Queue

```typescript
// Frontend: Queue SOS when offline
import { enqueueSOS } from '@/lib/offline-sos-queue';

if (!navigator.onLine) {
  await enqueueSOS({
    lat: 13.0827,
    lon: 80.2707,
    timestamp: Date.now(),
  });
  console.log('SOS queued for delivery when online');
}
```
