# Update Management — Developer Guide

## Architecture

The update management system spans backend API, database, frontend components, Zustand store, and CLI tools.

### Components

- **Backend API** (`backend/api/v1/updates.py`): 15+ REST endpoints for update lifecycle
- **Update Service** (`backend/services/update_service.py`): Business logic for releases, installs, rollbacks
- **Update Scheduler** (`backend/services/update_scheduler.py`): Periodic background check loop
- **DB Models** (`backend/models/update_management.py`): UpdateRelease, UpdateInstallation, UpdateSetting
- **Pydantic Schemas** (`backend/schemas/update_management.py`): All request/response shapes
- **Signature Module** (`backend/core/signature.py`): GPG signature verification
- **Frontend Store** (`frontend/lib/store/update-slice.ts`): Zustand slice
- **Frontend API Client** (`frontend/lib/api/update-api.ts`): 14+ API functions + SSE subscriptions
- **Frontend Components**: UpdateWidget, UpdateBanner, UpdateSettingsSection
- **CLI**: `scripts/safevixai_update.py` (Python), `scripts/safevixai-update.ps1` (PowerShell)

## Adding a New Release Channel

1. Add enum value in `backend/models/update_management.py` `ReleaseChannel` enum
2. Add channel display name in `list_channels()` in `update_service.py`
3. Update `frontend/components/updates/UpdateSettingsSection.tsx` channel selector
4. Add migration if the new channel needs DB validation

## Extending the Update Flow

All update operations follow a pipeline: check -> download -> verify -> verify-signature -> install -> restart.

To add a step:

1. Add service method in `update_service.py`
2. Add endpoint in `updates.py`
3. Wire the step in `UpdateWidget.tsx` `handleUpdateNow()` callback
4. Add tests in `test_update_management.py`

## Running the Scheduler in Dev Mode

```bash
cd backend
.venv\Scripts\Activate.ps1
# The scheduler starts automatically via FastAPI lifespan
# Check status: GET /api/v1/updates/scheduler/status
# Config: UPDATE_CHECK_INTERVAL env var (default: hourly)
```

## Testing Update Flows Locally

Backend tests use mocked DB sessions:

```bash
cd backend
.venv\Scripts\Activate.ps1
pytest tests/test_update_management.py --tb=short -q
pytest tests/test_update_scheduler.py --tb=short -q
```

Frontend tests use Jest with mocked API:

```bash
cd frontend
npx jest --testPathPatterns="update|Update" --no-coverage
```

## CI/CD Integration

The GitHub Releases workflow (`ci/release.yml`) automates:
1. Build artifacts
2. Create GitHub Release
3. Notify backend via webhook
4. Trigger update check on all clients

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| APP_VERSION | 1.0.0 | Current application version |
| GITHUB_REPO | SafeVixAI/SafeVixAI | GitHub repo for release sync |
| UPDATE_MAX_RETRIES | 3 | Max retries for download/install |
| UPDATE_RETRY_BASE_DELAY | 1.0 | Base delay in seconds for exponential backoff |
| UPDATE_CHECK_INTERVAL | 3600 | Scheduler check interval in seconds |

## API Client Patterns

Frontend API functions follow this pattern:

```typescript
import { client } from './client';
export async function fetchSomething(param: string): Promise<ResponseType> {
  const { data } = await client.get('/api/v1/updates/endpoint', { params: { param } });
  return data;
}
```

SSE subscriptions use `EventSource` with cleanup:

```typescript
export function subscribeToProgress(version: string, onProgress, onComplete): () => void {
  const es = new EventSource(`/api/v1/updates/download/${version}/progress`);
  es.onmessage = (e) => { /* parse JSON, call callbacks */ };
  return () => es.close();
}
```
