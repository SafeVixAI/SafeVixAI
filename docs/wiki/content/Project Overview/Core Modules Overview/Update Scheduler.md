---
title: Update Scheduler
description: Background scheduler for periodic update checks.
tags: [Project Overview/Core Modules Overview, update_scheduler]
owner: docs-team
generated: 2026-07-28
review-by: 2026-07-28
---

# Update Scheduler

> Source: `backend/services/update_scheduler.py` | Generated: 2026-07-28

## Overview

Background scheduler for periodic update checks.

## Classes

| Class | Description |
|---|---|
| `UpdateScheduler` | Updatescheduler |

## Key Functions

| Function | Description |
|---|---|
| `is_running()` | Is Running |
| `last_check()` | Last Check |
| `start()` | Start |
| `stop()` | Stop |
| `get_status()` | Get Status |

## Dependencies

- `__future__`
- `asyncio`
- `contextlib`
- `logging`
- `models`
- `services`
- `sqlalchemy`


## File Location

```
backend/services/update_scheduler.py
```
