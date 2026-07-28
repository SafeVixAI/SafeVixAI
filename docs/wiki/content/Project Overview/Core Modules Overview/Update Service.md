---
title: Update Service
description: Enterprise update management service — version checks, releases, installs, rollbacks.
tags: [Project Overview/Core Modules Overview, update_service]
owner: docs-team
generated: 2026-07-28
review-by: 2026-07-28
---

# Update Service

> Source: `backend/services/update_service.py` | Generated: 2026-07-28

## Overview

Enterprise update management service — version checks, releases, installs, rollbacks.

## Classes

| Class | Description |
|---|---|
| `UpdateService` | Updateservice |

## Key Functions

| Function | Description |
|---|---|
| `get_version_info()` | Get Version Info |
| `list_releases()` | List Releases |
| `get_release()` | Get Release |
| `get_latest_release()` | Get Latest Release |
| `check_for_updates()` | Check For Updates |
| `sync_releases_from_github()` | Sync Releases From Github |
| `download_release()` | Download Release |
| `install_release()` | Install Release |
| `rollback()` | Rollback |
| `get_installation_history()` | Get Installation History |
| `get_installations_by_status()` | Get Installations By Status |
| `get_settings()` | Get Settings |
| `update_settings()` | Update Settings |
| `list_channels()` | List Channels |
| `restart_application()` | Restart Application |

## Dependencies

- `__future__`
- `asyncio`
- `hashlib`
- `httpx`
- `logging`
- `models`
- `schemas`
- `sqlalchemy`


## File Location

```
backend/services/update_service.py
```
