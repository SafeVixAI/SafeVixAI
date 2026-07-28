---
title: Updates
description: Enterprise update management API endpoints.
tags: [API Reference, updates]
owner: docs-team
generated: 2026-07-28
review-by: 2026-07-28
---

# Updates

> Source: `backend/api/v1/updates.py` | Generated: 2026-07-28

## Overview

Enterprise update management API endpoints.

## Classes

| Class | Description |
|---|---|
| `VerifyFileRequest` | Verifyfilerequest |
| `VerifySignatureRequest` | Verifysignaturerequest |
| `PublicKeyRequest` | Publickeyrequest |
| `RetryOperationRequest` | Retryoperationrequest |
| `ApplyOfflineBundleRequest` | Applyofflinebundlerequest |

## Key Functions

| Function | Description |
|---|---|
| `get_update_service()` | Get Update Service |
| `get_version_info()` | Get Version Info |
| `check_for_updates()` | Check For Updates |
| `list_releases()` | List Releases |
| `get_release()` | Get Release |
| `get_update_history()` | Get Update History |
| `get_installations_by_status()` | Get Installations By Status |
| `sync_releases()` | Sync Releases |
| `download_release()` | Download Release |
| `install_release()` | Install Release |
| `rollback_update()` | Rollback Update |
| `list_channels()` | List Channels |
| `get_scheduler_status()` | Get Scheduler Status |
| `get_update_settings()` | Get Update Settings |
| `update_update_settings()` | Update Update Settings |

## Dependencies

- `__future__`
- `core`
- `fastapi`
- `logging`
- `models`
- `pydantic`
- `schemas`
- `services`
- `sqlalchemy`


## File Location

```
backend/api/v1/updates.py
```
