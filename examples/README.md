# Examples

> **Sample code, templates, and cookbook recipes for SafeVixAI integration.**

This directory contains ready-to-run examples demonstrating how to use SafeVixAI's APIs, chatbots, and emergency features.

---

## Contents

| Example | Description | Language |
|---------|-------------|----------|
| [`api-client/`](api-client/) | Python & TypeScript API client examples | Python + TS |
| [`emergency/`](emergency/) | Emergency locator and SOS integration | Python |
| [`challan/`](challan/) | Challan calculation examples | Python + SQL |
| [`chatbot/`](chatbot/) | Chatbot API integration patterns | Python |
| [`webhooks/`](webhooks/) | Webhook receiver and sender examples | Python |
| [`offline/`](offline/) | Offline-first PWA patterns | TypeScript |
| [`cookbook/`](cookbook/) | Recipe-based integration patterns | Various |

---

## Prerequisites

```bash
pip install httpx           # Python examples
npm install @safevixai/sdk  # TypeScript examples (when published)
```

---

## Quick Start Example

```python
import httpx

BASE_URL = "http://localhost:8000"

# Get nearby emergency services
resp = httpx.get(
    f"{BASE_URL}/api/v1/emergency/nearby",
    params={"lat": 13.0827, "lon": 80.2707, "radius": 5000}
)
data = resp.json()
print(f"Found {len(data['hospitals'])} nearby hospitals")

# Calculate a challan
resp = httpx.get(
    f"{BASE_URL}/api/v1/challan/calculate",
    params={"violation_code": "MVA_185", "state": "tamil_nadu"}
)
print(f"Fine amount: ₹{resp.json()['amount']}")
```

---

## Related

- [`SDK_GUIDE.md`](../SDK_GUIDE.md) — comprehensive API integration guide
- [`docs/INTEGRATION_GUIDE.md`](../docs/INTEGRATION_GUIDE.md) — third-party integrations
- [`docs/WEBHOOKS.md`](../docs/WEBHOOKS.md) — webhook events
- [`docs/PLUGIN_SYSTEM.md`](../docs/PLUGIN_SYSTEM.md) — plugin development
