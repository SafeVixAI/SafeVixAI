---
title: Values
description: Domain value objects — Coordinates, Severity, Distance.
tags: [Database Schema, values]
owner: data-team
generated: 2026-07-23
review-by: 2026-07-23
---

# Values

> Source: `backend/models/values.py` | Generated: 2026-07-23

## Overview

Domain value objects — Coordinates, Severity, Distance.

## Classes

| Class | Description |
|---|---|
| `Coordinates` | Coordinates |
| `Severity` | Severity |
| `Distance` | Distance |

## Key Functions

| Function | Description |
|---|---|
| `distance_to()` | Distance To |
| `as_tuple()` | As Tuple |
| `label()` | Label |
| `is_critical()` | Is Critical |
| `from_int()` | From Int |
| `kilometers()` | Kilometers |

## Dependencies

- `__future__`
- `dataclasses`
- `math`


## File Location

```
backend/models/values.py
```
