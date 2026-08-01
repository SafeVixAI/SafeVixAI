# Examples

> **Sample code, templates, and cookbook recipes for SafeVixAI integration.**

This directory contains ready-to-run examples demonstrating how to use SafeVixAI's APIs, chatbots, and emergency features.

---

## Contents

| Example | Description | Files |
|---------|-------------|-------|
| [`api-client/`](api-client/) | Python & TypeScript API client classes | `client.py`, `client.ts` |
| [`emergency/`](emergency/) | SOS trigger, emergency lookup, offline queue | `emergency.py`, `offline-queue.ts` |
| [`challan/`](challan/) | Online + DuckDB-Wasm offline challan calc | `calculate.py`, `offline.ts`, `query.sql` |
| [`chatbot/`](chatbot/) | Simple, streaming, provider override, tool routing | `examples.py` |
| [`cookbook/`](cookbook/) | 5 integration recipes + WebSocket tracking | `recipes.py`, `tracking.ts` |

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

- [`SDK_GUIDE.md`](../docs/api-reference/SDK_GUIDE.md) — comprehensive API integration guide
- [`docs/INTEGRATION_GUIDE.md`](../docs/api-reference/INTEGRATION_GUIDE.md) — third-party integrations
- [`docs/WEBHOOKS.md`](../docs/api-reference/WEBHOOKS.md) — webhook events
- [`docs/PLUGIN_SYSTEM.md`](../docs/api-reference/PLUGIN_SYSTEM.md) — plugin development
