---
title: Probes
description: Probes module for the API Reference subsystem.
tags: [API Reference, probes]
owner: docs-team
generated: 2026-07-30
review-by: 2026-07-30
---

# Probes

> Source: `backend/api/v1/probes.py` | Generated: 2026-07-30

## Overview

Probes module for the API Reference subsystem.

## Key Functions

| Function | Description |
|---|---|
| `set_startup_complete()` | Set Startup Complete |
| `readiness_probe()` | Readiness Probe |
| `liveness_probe()` | Liveness Probe |
| `startup_probe()` | Startup Probe |
| `asyncio_wrap()` | Asyncio Wrap |

## Dependencies

- `__future__`
- `core`
- `fastapi`
- `httpx`
- `time`


## File Location

```
backend/api/v1/probes.py
```
