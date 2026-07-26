# Best Practices

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [STYLE_GUIDE.md](../STYLE_GUIDE.md), [TESTING_POLICY.md](./TESTING_POLICY.md), [SECURITY.md](./Security.md)

---

## API Design

### RESTful Conventions
- Use nouns for resources: `/api/v1/emergency`, `/api/v1/challan`
- Use HTTP methods for actions: GET (read), POST (create), PUT (replace), PATCH (partial update), DELETE (remove)
- Version the API from day one: `/api/v1/`
- Return consistent error responses with error codes
- Use cursor-based pagination for list endpoints

### Request/Response Patterns
```json
// Request
POST /api/v1/roads/report
{
  "location": { "lat": 13.0827, "lon": 80.2707 },
  "category": "pothole",
  "description": "Deep pothole on Anna Salai"
}

// Response (success)
{
  "id": "rep_abc123",
  "status": "submitted",
  "created_at": "2026-07-26T10:00:00Z"
}

// Response (error)
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid location coordinates",
    "details": [{ "field": "lat", "message": "Must be between -90 and 90" }],
    "request_id": "req_abc123"
  }
}
```

### Versioning
- URL path versioning: `/api/v1/`
- Backward-compatible additions only within a major version
- Deprecated endpoints return `DeprecationWarning` header
- See [VERSIONING.md](../VERSIONING.md) for full policy

---

## Database

### Indexing Strategy
- **GiST indexes** on PostGIS geometry columns for spatial queries
- **BTREE indexes** on foreign keys, status fields, and timestamp columns
- **Covering indexes** (`INCLUDE` columns) for frequent queries
- Avoid over-indexing — monitor query performance

```sql
-- Spatial index (PostGIS)
CREATE INDEX idx_road_issues_location ON road_issues USING GIST (location);

-- Covering index
CREATE INDEX idx_issues_status ON road_issues (status) INCLUDE (category, created_at);
```

### Query Optimization
- Use `EXPLAIN ANALYZE` to identify slow queries
- Prefer `SELECT` specific columns over `SELECT *`
- Use connection pooling (SQLAlchemy pool_size=20, max_overflow=10)
- Use `::geography` cast for accurate meter-distance calculations
- Batch updates when modifying multiple rows

### Migration Patterns
```python
"""Add road_issues covering indexes.

Revision ID: e7b9a1_indexes
"""
from alembic import op

def upgrade():
    op.create_index("idx_road_issues_location", "road_issues", ["location"], postgresql_using="gist")
    op.create_index("idx_issues_status_cat", "road_issues", ["status"], postgresql_include=["category", "created_at"])
```

---

## Security

### Input Validation
- Validate all user inputs at the API boundary
- Use Pydantic models for request validation
- Sanitize file uploads (validate MIME type, size, dimensions)
- Use parameterized queries for all database operations (never string interpolation)

### Output Encoding
- Escape all user-generated content in HTML responses
- Set `Content-Type: application/json` for API responses
- Never return stack traces in production

### Rate Limiting
- Apply rate limits to all endpoints
- Use Redis-backed rate limiter for distributed deployments
- Return `Retry-After` header on 429 responses

### Authentication & Authorization
- JWT with RS256 signatures
- JWKS endpoint for public key distribution
- Role-based access control (citizen, operator, admin)
- Short token expiry (1 hour), refresh tokens for longer sessions

---

## Frontend

### Component Composition
- Prefer composition over inheritance
- Extract reusable UI patterns into components
- Keep components focused on a single responsibility
- Use `'use client'` directive only when interactivity is needed

### State Management (Zustand)
- Keep global state minimal — colocate state when possible
- Use `useShallow` for selective subscriptions
- Persist critical state (auth, profile) to IndexedDB
- Reset store state on logout

### Code Splitting
```typescript
// Dynamic imports for heavy components
const MapLibreCanvas = dynamic(() => import('@/components/maps/MapLibreCanvas'), {
  ssr: false,
  loading: () => <MapLoadingFallback />,
});
```

### Image Optimization
- Use `next/image` for automatic optimization
- Serve images in WebP format
- Lazy load images below the fold
- Set explicit width/height to prevent layout shift

---

## Chatbot

### Prompt Engineering
- Use structured prompts with clear instructions
- Include context from RAG retrieval
- Set temperature based on task (0.1 for factual, 0.7 for creative)
- Limit response length with max_tokens

### Tool Design
- Each tool has a single, well-defined purpose
- Tools return structured data (not free text)
- Tool descriptions are written for the LLM (not humans)
- Validate tool inputs before execution

### Safety Checks
```python
# Every user message goes through the SafetyChecker
safety_result = await safety_checker.evaluate(user_message)
if safety_result.blocked:
    return {"response": "I cannot process this request.", "blocked": True}
```

---

## Testing

### Test Pyramid
- **Unit tests** (80%): Test individual functions and components in isolation
- **Integration tests** (15%): Test service interactions with real/stub dependencies
- **E2E tests** (5%): Test full user flows in production-like environment

### Coverage Targets
| Service | Lines | Branches |
|---------|-------|----------|
| Backend | 100% | 100% |
| Chatbot | 97%+ | — |
| Frontend | 86%+ | 72%+ |

### Test Patterns
```python
# Backend: Use fixtures and factories
async def test_emergency_nearby(db_session):
    facilities = await EmergencyFactory.create_batch(5)
    result = await emergency_service.get_nearby(lat=13.08, lon=80.27)
    assert len(result) > 0
```

```typescript
// Frontend: Use screen queries
it('renders emergency button', () => {
  render(<SosButton />);
  expect(screen.getByRole('button', { name: /sos/i })).toBeInTheDocument();
});
```

---

## Deployment

### Immutable Infrastructure
- Build Docker images once, deploy everywhere
- Tag images with git SHA and version
- Never SSH into production servers
- Use health checks for rolling updates

### Secrets Management
- Use GitHub Secrets for CI/CD
- Never commit `.env` files
- Rotate secrets regularly (90-day policy)
- Use gitleaks as pre-commit hook

### Graceful Shutdown
```python
# FastAPI lifespan handles graceful shutdown
async def lifespan(app: FastAPI):
    # Startup
    await create_cache()
    yield
    # Shutdown
    await close_db_connections()
    await close_redis()
```

---

## Performance

- Use async/await for all I/O operations
- Cache expensive computations (Redis, in-memory)
- Use connection pooling for databases and HTTP clients
- Profile before optimizing (measure, identify bottleneck, fix)
- Set appropriate timeouts for external service calls
- Monitor p95/p99 latency, not just averages

---

## Documentation

- Document public APIs with OpenAPI/Swagger
- Keep docs close to code (docstrings, JSDoc)
- Update docs when changing behavior
- Include examples in API documentation
- Cross-reference related documents
- Follow Google-style docstrings for Python
