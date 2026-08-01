# SafeVixAI — Architecture Review (Updated 2026-05-26)

> **SNAPSHOT**: This document reflects the state as of 2026-05-26. For current state see [AGENTS.md](../../../AGENTS.md).

> Verified against actual codebase. Corrections to prior audit noted.

---

## 1. Strengths (Verified)

### Architecture
- **3-service separation** with clear boundaries: frontend (Next.js), backend (FastAPI :8000), chatbot (FastAPI :8010)
- **Factory pattern** in both FastAPI apps: `create_app()` — testable, mockable
- **Proper lifespan management**: `@asynccontextmanager` with complete startup/shutdown lifecycle
- **Service injection via `app.state`**: Consistent DI pattern; no dependency injection framework needed
- **Two isolated virtual environments**: backend and chatbot have separate .venv, .env, requirements.txt

### Resilience
- **10-provider LLM fallback chain**: Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Template (deterministic)
- **3-tier emergency data**: PostGIS DB (~50k facilities) → Local CSV → Overpass API
- **3-tier offline challan**: DuckDB-Wasm → CSV parser → Dict in-memory fallback
- **Circuit breakers**: Per-provider graduated cooldowns (60s for timeout → 24h for quota exhaustion)
- **In-memory fallback for all Redis-dependent systems**: Cache, rate limiting, conversation memory
- **Dual auth validation**: App JWT + Supabase JWT + JWKS optional

### Performance
- **Granular Zustand selectors**: ~30 selector hooks prevent unnecessary re-renders
- **GPU-composited GSAP animations**: Only transform/opacity animated
- **Dynamic imports**: MapLibre, DuckDB-Wasm, WebLLM all SSR-disabled
- **DuckDB-Wasm client-side**: Avoids server round-trip for challan queries
- **Response caching**: Redis + in-memory with configurable TTLs

### DevOps
- **19 CI/CD workflows**: lint → test → security → build → deploy → docs → load test → chaos
- **Blue-green deployment pattern**: Render deploy hooks with pre/post verification
- **Docker Compose with 3 isolated networks**: Data-net, backend-net, frontend-net — prevents lateral movement
- **Non-root containers**: All Dockerfiles use `appuser`
- **Dependabot**: npm + pip + GitHub Actions, weekly schedules, 5 PR limit

---

## 2. Weaknesses (Verified)

### Auth & Security
- **Live credentials in git**: All 3 .env files committed with production secrets (CRITICAL)
- **Single-operator auth**: Backend only supports 1 operator via env vars; no user registration
- **No token revocation**: JWT valid for 24h; no blacklist/refresh mechanism
- **RBAC not enforced**: JWT has `role` claim but most endpoints don't check it
- **No Host header validation**: No ALLOWED_HOSTS — Host header injection possible
- **Chatbot endpoints unauthenticated**: `/chat` and `/chat/stream` rate-limited but no JWT required
- **X-Admin-Key deprecated but still accepted**: Legacy admin auth header still functional

### Observability
- **Prometheus `/metrics` wired but analytics endpoint** returns data for public — not true Prometheus
- **No uptime monitoring**: No UptimeRobot/Pingdom configured
- **Sentry optional**: Only enabled if `SENTRY_DSN` is set; no default
- **Email alerts 5-min cooldown**: Resets on restart (in-memory only)
- **No distributed tracing**: OTLP not configured

### Testing
- **Frontend test coverage**: Only 12 component tests; `useSOS.test.ts` excluded from Jest
- **Chatbot**: 892/892 passing, 95% coverage
- **Backend**: 1365/1365 passing, 59% coverage — service files need live DB
- **No cross-service integration tests**: Frontend↔Backend↔Chatbot not tested together
- **Root `/tests/` directory gitignored**: k6, chaos, and contract tests exist on disk but untracked

### Infrastructure
- **Render free tier oversubscribed**: 2 services × 24h × 30.5d = 1464h vs 750h available
- **No Infrastructure as Code**: Docker Compose + render.yaml only; no Terraform/Pulumi
- **Duplicated render.yaml**: chatbot_service/render.yaml duplicates root render.yaml chatbot service
- **Package manager conflict**: CI uses `npm ci`, AGENTS.md says pnpm; pnpm-lock.yaml gitignored
- **No automated DB rollback**: Alembic downgrade exists but no CI step for it

### Data
- **SOS incidents persist indefinitely**: No cleanup/retention policy
- **Location privacy**: Tracking data stored with no expiry enforcement beyond 4h token
- **All `.env` files track live credentials**: Including Gmail app password for email alerts
- **Sub-gitignore contradicts root**: chatbot_service/.gitignore ignores chroma_db but root explicitly keeps it

---

## 3. Technical Debt

| Item | Impact | Effort | Priority |
|------|--------|--------|----------|
| .env files committed to git | Credentials exposed to all repo users | HIGH (rotate + git filter) | **CRITICAL** |
| SafetyChecker output check never called | Output safety not enforced | Low (4-line call) | HIGH |
| SWR underutilized (1 of 23 pages) | Missing caching/revalidation | MEDIUM (add SWR hooks) | HIGH |
| EmergencyTool instantiated but unwired | Dead tool | Low (wire or remove) | MEDIUM |
| Dead route context methods in context_assembler | 3 methods never called | Low (remove dead code) | MEDIUM |
| torch in chatbot requirements | 800MB dep for optional speech feature | MEDIUM (make optional) | MEDIUM |
| Horverwrite html lang | HARDDED | Low (use env var) | MEDIUM |
| No Host header validation | Head injection risk | Low (add middleware) | MEDIUM |
| X-Admin-Key header still allowed | Dead legacy auth path | Low (remove from CORS) | LOW |
| Duplicated render.yaml | Drift risk | Low (remove one) | LOW |
| next-themes installed but unused | Dead dependency 0.4.6 | Low (remove) | LOW |
| Framer Motion orphaned in lockfile | Dead dep | Low (prune lockfile) | LOW |
