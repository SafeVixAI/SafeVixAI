# Issue Reporting Ecosystem

> Enterprise-grade issue, feedback, and crash reporting for SafeVixAI.
> **Last updated:** 2026-07-28

---

## Overview

The Issue Reporting Ecosystem provides a complete pipeline for collecting, categorizing, triaging, and resolving user-reported issues across all SafeVixAI surfaces — web app, API, CLI, and automated error boundaries.

### Capabilities

| Feature | Status |
|---------|--------|
| Bug Reports | ✅ |
| Feature Requests | ✅ |
| General Feedback | ✅ |
| Performance Issues | ✅ |
| Security Reports | ✅ |
| Crash Reports | ✅ |
| AI Feedback | ✅ |
| Screenshot Capture | ✅ |
| Screen Recording | ✅ |
| Logs & System Info | ✅ |
| Environment/Browser/Device Info | ✅ |
| App Version Tracking | ✅ |
| Anonymous Reports | ✅ |
| Authenticated Reports | ✅ |
| Issue Templates | ✅ |
| GitHub Issues Integration | ✅ |
| GitHub Discussions Integration | ✅ |
| Labels/Milestones/Assignees | ✅ |
| Priority/Severity/Status | ✅ |
| Duplicate Detection | ✅ |
| Spam Detection | ✅ |
| AI Categorization | ✅ |
| AI Summarization | ✅ |
| AI Suggested Fixes | ✅ |
| User Tracking Number | ✅ |
| Issue Timeline | ✅ |
| Attachments | ✅ |
| Email/Slack/Discord/Webhook | ✅ |
| Admin Dashboard | ✅ |
| Issue Analytics | ✅ |
| Response SLA | ✅ |
| CLI Tool | ✅ |

---

## Architecture

```
User (Web/CLI/Error Boundary)
    │
    ▼
┌────────────────────────┐
│  Frontend Components   │
│  (FeedbackWidget,      │
│   ErrorDialog,         │
│   CrashScreen,         │
│   IssueForm,           │
│   Dashboard)           │
└─────────┬──────────────┘
          │ POST /api/v1/issues
          ▼
┌────────────────────────┐
│  IssueService          │  ← Spam detection, duplicate detection
│  AIIssueService        │  ← AI categorization, summarization
│  GitHubIntegration     │  ← GitHub Issues + Discussions
│  IssueNotification     │  ← Slack, Discord, Email, Webhooks
└─────────┬──────────────┘
          │
          ▼
┌────────────────────────┐
│  PostgreSQL            │
│  issue_reports         │
│  issue_timeline_events │
└────────────────────────┘
```

---

## API Endpoints

### Issues CRUD

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/issues` | Create a new issue report |
| `GET` | `/api/v1/issues` | List issues (paginated, filterable) |
| `GET` | `/api/v1/issues/{uuid}` | Get issue by UUID |
| `GET` | `/api/v1/issues/tracking/{number}` | Get issue by tracking number |
| `PATCH` | `/api/v1/issues/{uuid}` | Update issue (status, assignee, etc.) |
| `GET` | `/api/v1/issues/stats` | Issue statistics dashboard |
| `GET` | `/api/v1/issues/templates` | Issue templates for each type |

### Issue Actions

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/issues/{uuid}/spam` | Mark issue as spam |
| `POST` | `/api/v1/issues/{uuid}/duplicate/{orig}` | Mark as duplicate |
| `POST` | `/api/v1/issues/{uuid}/sla` | Set SLA deadlines |
| `GET` | `/api/v1/issues/{uuid}/timeline` | Get issue timeline |
| `GET` | `/api/v1/issues/{uuid}/duplicates` | Find similar/depulicate issues |

---

## Issue Types

| Type | Description | Routes to |
|------|-------------|-----------|
| `bug` | Software bug report | GitHub Issue |
| `feature_request` | New feature suggestion | GitHub Discussion |
| `feedback` | General user feedback | GitHub Discussion |
| `performance` | Performance regression | GitHub Issue |
| `security` | Security vulnerability | GitHub Issue (private) |
| `crash` | Application crash | GitHub Issue |
| `ai_feedback` | LLM response quality | GitHub Issue |

---

## Severity & Priority Matrix

| Severity | Description | SLA Response | SLA Resolution |
|----------|-------------|--------------|----------------|
| Critical | System down, data loss | 2h | 8h |
| High | Major feature broken | 4h | 24h |
| Medium | Non-critical bug | 24h | 72h |
| Low | Minor issue, cosmetic | 48h | 7d |
| Cosmetic | Visual only | 7d | 14d |

| Priority | Description |
|----------|-------------|
| Urgent | Blocks release, immediate attention needed |
| High | Should be fixed in current sprint |
| Normal | Default priority |
| Low | Nice to have, backlog |

---

## Issue Lifecycle

```
new → triaged → acknowledged → in_progress → resolved → closed
  ↘              ↘                ↘
  spam          needs_info       wont_fix
  duplicate
```

---

## Database Schema

### `issue_reports`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `SERIAL` | Primary key |
| `uuid` | `UUID` | Public identifier |
| `tracking_number` | `VARCHAR(32)` | User-facing tracking code (e.g. `SAFE-260728-ABC123`) |
| `user_id` | `UUID` | Authenticated user (nullable for anonymous) |
| `issue_type` | `VARCHAR(32)` | bug, feature_request, feedback, etc. |
| `category` | `VARCHAR(32)` | frontend, backend, api, database, etc. |
| `severity` | `VARCHAR(16)` | critical, high, medium, low, cosmetic |
| `priority` | `VARCHAR(16)` | urgent, high, normal, low |
| `status` | `VARCHAR(24)` | new, triaged, acknowledged, in_progress, etc. |
| `title` | `VARCHAR(256)` | Short description |
| `description` | `TEXT` | Full description |
| `environment` | `TEXT` | Browser, OS, app version info |
| `is_spam` | `BOOLEAN` | Spam flag |
| `duplicate_of` | `UUID` | Links to parent duplicate |
| `location` | `GEOMETRY(Point, 4326)` | Geographic location |
| `sla_response_at` | `TIMESTAMPTZ` | SLA response deadline |
| `sla_resolution_at` | `TIMESTAMPTZ` | SLA resolution deadline |

### `issue_timeline_events`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `SERIAL` | Primary key |
| `issue_uuid` | `UUID` | FK to issue_reports |
| `event_type` | `VARCHAR(48)` | created, updated, marked_spam, marked_duplicate |
| `description` | `TEXT` | Human-readable description |
| `actor` | `VARCHAR(128)` | Who performed the action |
| `metadata` | `JSONB` | Extra event data |

---

## Spam Detection

The `IssueService` implements multi-layer spam detection:

1. **Hash-based**: SHA-256 fingerprints of title + description; repeated identical submissions blocked
2. **Keyword-based**: Common spam phrases (`buy now`, `click here`, `free money`)
3. **Domain-based**: Blocked email domains (`tempmail.com`, `throwaway.com`, `mailinator.com`)

## Duplicate Detection

Jaccard similarity on title tokens. Configurable threshold (default: 0.7). When a duplicate is detected:
- Issue status is set to `duplicate`
- `duplicate_of` links to the original issue
- `duplicate_score` stores the similarity score
- Timeline event records the match

## AI Integration

The `AIIssueService` provides zero-dependency keyword-based categorization:
- Maps keywords to 10+ categories: `ui_bug`, `api_error`, `data_loss`, `auth`, `performance`, `crash`, `network`, `security`, `compatibility`
- Generates concise summaries from description text
- Suggests fixes based on category and keyword matching

## Notifications

### Slack
Rich block-message format with severity color coding, labels, and truncated description.

### Discord
Embed-based format with color-coded severity bar, fields for type/severity/status/labels.

### Webhook
Generic JSON payload with the full issue object. Configurable via Settings UI.

---

## CLI Tool

The CLI tool allows reporting issues from the command line:

```bash
python -m api.v1.issues_cli report --type bug --title "Bug title" --desc "Bug description"
python -m api.v1.issues_cli list --status open
python -m api.v1.issues_cli get SAFE-260728-ABC123
python -m api.v1.issues_cli stats
```

---

## Frontend Components

### `FeedbackWidget`
Floating button (bottom-right) that opens a feedback form. Supports:
- Type selection (Bug, Feature, Feedback, Performance)
- Screenshot capture (client-side canvas)
- Auto-populates browser info
- Anonymous submission option

### `ErrorDialog`
Modal dialog triggered by `ErrorBoundary`. Features:
- Error message display
- "What were you doing?" text area
- One-click report submission
- Page reload on recovery

### `CrashScreen`
Full-screen error recovery for fatal crashes. Features:
- Crash report with full system info
- Technical details toggle (stack trace)
- Reload button

### `ErrorBoundary`
React component that catches render errors. Two modes:
- `dialog`: Shows ErrorDialog modal
- `screen`: Shows CrashScreen overlay

### `IssueForm`
Full issue submission form with all fields:
- Issue type (radio group with icons)
- Severity & Priority selects
- Title, Description, Steps to Reproduce
- Expected vs Actual Behavior
- Environment, Labels
- Screenshot capture
- Anonymous toggle

### Dashboard
Full-featured issue management dashboard:
- Stats overview (total, open, resolved, SLA breaches)
- By-type and by-severity breakdowns
- Filterable issue list with search
- Pagination support
- Status badges with color coding

---

## Settings

The settings page (`/settings/issues`) provides:
- Auto-submit error toggle
- Screenshot inclusion toggle
- Console log inclusion toggle
- System info inclusion toggle
- Anonymity default
- Slack/Discord/Webhook URL configuration
- Cache and drafts management

---

## Test Coverage

### Backend Tests
- `test_issue_service.py` — 18 tests covering CRUD, spam detection, duplicate detection, SLA, tracking numbers
- `test_ai_issue_service.py` — 14 tests covering categorization, summarization, suggested fixes
- `test_github_integration.py` — 10 tests covering issue creation, updates, comments, labels, webhook verification

### Frontend Tests
- `tests/issues.test.tsx` — 16 tests covering dashboard, detail page, new issue form, feedback widget, error dialog, crash screen, settings
