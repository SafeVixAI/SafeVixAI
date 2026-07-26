---
title: Schemas Civic
description: Civic intelligence, ward, officer, and municipality Pydantic schemas.
tags: [Database Schema, schemas_civic]
owner: data-team
generated: 2026-07-26
review-by: 2026-07-26
---

# Schemas Civic

> Source: `backend/models/schemas_civic.py` | Generated: 2026-07-26

## Overview

Civic intelligence, ward, officer, and municipality Pydantic schemas.

## Classes

| Class | Description |
|---|---|
| `GeocodeResult` | Geocoderesult |
| `GeocodeSearchResponse` | Geocodesearchresponse |
| `ComplaintEventItem` | Complainteventitem |
| `ComplaintTimelineResponse` | Complainttimelineresponse |
| `WardResponse` | Wardresponse |
| `WardStatsResponse` | Wardstatsresponse |
| `OfficerResponse` | Officerresponse |
| `OfficerCheckinRequest` | Officercheckinrequest |
| `OfficerCheckinResponse` | Officercheckinresponse |
| `HeatmapFeatureGeometry` | Heatmapfeaturegeometry |

## Key Functions

| Function | Description |
|---|---|
| `validate_wkb()` | Validate Wkb |
| `validate_geojson()` | Validate Geojson |

## Dependencies

- `__future__`
- `pydantic`


## File Location

```
backend/models/schemas_civic.py
```
