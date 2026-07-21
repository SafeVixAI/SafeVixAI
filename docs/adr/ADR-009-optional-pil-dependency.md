# ADR-009: Optional PIL Dependency for Image Processing

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** SafeVixAI Backend Team

## Context

The RoadWatch service supports photo uploads with EXIF stripping to remove GPS metadata. EXIF stripping requires the Pillow library (PIL), which is a 10MB+ dependency.

Not all deployments need image processing:
- Development environments may skip photo uploads
- Test environments don't need PIL
- Some production deployments may use external image processing

Previous behavior: importing PIL at module level would crash the entire backend if PIL was not installed or if there was a version compatibility issue.

## Decision

Make PIL an optional dependency with graceful degradation:

1. **HAS_PIL flag** -- module-level boolean checked before any PIL-dependent code runs
2. **Guarded import** -- `try/except ImportError` wrapping the PIL import
3. **Graceful fallback** -- when PIL is unavailable, EXIF stripping is silently skipped and the original image is returned
4. **TypeError handling** -- added `TypeError` to the exception clause in `strip_exif()` to handle PIL metaclass conflicts (manifested as `TypeError` during `Image.open()` with certain PIL versions)

## Consequences

**Positive:**
- Backend starts without Pillow installed
- Test environment does not need PIL
- Clear error path for PIL-related issues

**Negative:**
- EXIF stripping is silently skipped when PIL is unavailable (no user notification)
- If PIL is needed for regulatory compliance, installation must be verified separately

## References

- `backend/services/roadwatch_photos.py` -- HAS_PIL flag, guarded import (lines 17-21), strip_exif with TypeError handling (line 66)
- `backend/services/roadwatch_service.py` -- calls strip_exif from roadwatch_photos (lines 471-475), guarded with try/except
