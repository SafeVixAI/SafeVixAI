---
title: Issue Service
description: Issue Service module for the Project Overview/Core Modules Overview subsystem.
tags: [Project Overview/Core Modules Overview, issue_service]
owner: docs-team
generated: 2026-07-30
review-by: 2026-07-30
---

# Issue Service

> Source: `backend/services/issue_service.py` | Generated: 2026-07-30

## Overview

Issue Service module for the Project Overview/Core Modules Overview subsystem.

## Classes

| Class | Description |
|---|---|
| `IssueService` | Issueservice |

## Key Functions

| Function | Description |
|---|---|
| `create_issue()` | Create Issue |
| `get_issue()` | Get Issue |
| `get_issue_by_tracking()` | Get Issue By Tracking |
| `update_issue()` | Update Issue |
| `list_issues()` | List Issues |
| `get_stats()` | Get Stats |
| `get_timeline()` | Get Timeline |
| `mark_spam()` | Mark Spam |
| `mark_duplicate()` | Mark Duplicate |
| `set_sla()` | Set Sla |
| `check_sla_breaches()` | Check Sla Breaches |
| `detect_spam()` | Detect Spam |
| `find_duplicates()` | Find Duplicates |

## Dependencies

- `__future__`
- `core`
- `hashlib`
- `logging`
- `models`
- `random`
- `sqlalchemy`
- `string`
- `uuid`


## File Location

```
backend/services/issue_service.py
```
