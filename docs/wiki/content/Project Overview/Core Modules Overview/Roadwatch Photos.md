---
title: Roadwatch Photos
description: Photo validation, EXIF stripping, and upload helpers for RoadWatch.
tags: [Project Overview/Core Modules Overview, roadwatch_photos]
owner: docs-team
generated: 2026-07-24
review-by: 2026-07-24
---

# Roadwatch Photos

> Source: `backend/services/roadwatch_photos.py` | Generated: 2026-07-24

## Overview

Photo validation, EXIF stripping, and upload helpers for RoadWatch.

## Classes

| Class | Description |
|---|---|
| `UploadedPhotoUrl` | Uploadedphotourl |
| `PhotoService` | Photoservice |

## Key Functions

| Function | Description |
|---|---|
| `is_valid_image_magic()` | Is Valid Image Magic |
| `strip_exif()` | Strip Exif |
| `read_upload_chunks()` | Read Upload Chunks |
| `save_photo_to_disk()` | Save Photo To Disk |
| `validate_photo_ai()` | Validate Photo Ai |
| `upload_photo_to_supabase()` | Upload Photo To Supabase |
| `compose_photo_url()` | Compose Photo Url |
| `cleanup_temp_file()` | Cleanup Temp File |
| `validate_and_save()` | Validate And Save |
| `validate_ai()` | Validate Ai |
| `upload_to_storage()` | Upload To Storage |

## Dependencies

- `__future__`
- `aiofiles`
- `contextlib`
- `fastapi`
- `httpx`
- `io`
- `logging`
- `services`


## File Location

```
backend/services/roadwatch_photos.py
```
