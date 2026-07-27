# Cookbook

> **Recipe-based integration patterns for common SafeVixAI use cases.**

---

## Recipes

| # | Recipe | Description | Difficulty |
|---|--------|-------------|------------|
| 1 | [Emergency Alert System](#1-emergency-alert-system) | Trigger SOS + notify contacts | Beginner |
| 2 | [Road Report Bot](#2-road-report-bot) | Automated pothole reporting | Beginner |
| 3 | [Challan Checker](#3-challan-checker) | Bulk fine calculation | Intermediate |
| 4 | [Family Tracking App](#4-family-tracking-app) | Live location sharing | Intermediate |
| 5 | [Multi-lingual Assistant](#5-multi-lingual-assistant) | Indian language chatbot | Advanced |

---

### 1. Emergency Alert System

```python
"""Trigger SOS and notify emergency contacts."""
import httpx

BACKEND = "http://localhost:8000"

# 1. Get nearest hospital
hospital = httpx.get(f"{BACKEND}/api/v1/emergency/nearby", params={
    "lat": 13.0827, "lon": 80.2707, "type": "hospital", "limit": 1
}).json()

# 2. Trigger SOS (requires auth)
# POST /api/v1/live-tracking/trigger-sos with JWT Bearer token

# 3. Generate WhatsApp share link
whatsapp_link = (
    f"https://wa.me/?text=Emergency!%20"
    f"Location:%20https://maps.google.com/maps?q=13.0827,80.2707"
)
print(f"Share: {whatsapp_link}")
```

### 2. Road Report Bot

```python
"""Automated road issue reporting."""
import httpx

report = {
    "lat": 13.0827,
    "lon": 80.2707,
    "issue_type": "pothole",
    "severity": "high",
    "description": "Deep pothole on Anna Salai near Spencer Plaza",
    "photos": [],  # Add base64 encoded photos
}

resp = httpx.post(
    "http://localhost:8000/api/v1/roadwatch/report",
    json=report,
)
print(f"Report submitted: {resp.json()['uuid']}")
```

### 3. Challan Checker

```python
"""Bulk fine calculation."""
import httpx

violations = [
    ("MVA_185", "tamil_nadu"),
    ("MVA_194D", "karnataka"),
    ("MVA_194B", "mumbai"),
]

for code, state in violations:
    resp = httpx.get(
        "http://localhost:8000/api/v1/challan/calculate",
        params={"violation_code": code, "state": state},
    )
    data = resp.json()
    print(f"{code} in {state}: ₹{data['amount']}")
```

### 4. Family Tracking App

```typescript
/** Live tracking integration pattern. */
const WS_URL = `ws://localhost:8000/api/v1/tracking/${groupId}`;
const ws = new WebSocket(WS_URL);

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'location_update',
    lat: 13.0827,
    lon: 80.2707,
    speed: 0,
    battery: 85,
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Family member location:', data.lat, data.lon);
};
```

### 5. Multi-lingual Assistant

```python
"""Chat in Indian languages via Sarvam AI."""
import httpx

queries = [
    ("தமிழ்", "சென்னையில் அருகில் உள்ள மருத்துவமனை எது?"),
    ("हिन्दी", "तेज़ गति के लिए जुर्माना क्या है?"),
    ("తెలుగు", "దగ్గరలోని పోలీస్ స్టేషన్ ఎక్కడ?"),
]

for lang, query in queries:
    resp = httpx.post(
        "http://localhost:8010/api/v1/chat/",
        json={"message": query, "session_id": f"demo-{lang}"},
    )
    print(f"[{lang}] {resp.json()['response'][:100]}")
```
