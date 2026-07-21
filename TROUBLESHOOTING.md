# Troubleshooting Guide

## Build Issues

### Frontend build takes 10+ minutes
**Cause**: `next.config.js` with `output: 'standalone'` triggers Next.js file tracer on all dependencies including three.js (~200MB).
**Fix**: Ensure `STANDALONE=true` is only set in CI/Docker builds. For local dev, run `npm run build` without the env var.
```bash
# Fast local build (~2 min)
npm run build

# Docker/CI build (~10-15 min, but produces smaller image)
STANDALONE=true npm run build
```

### "Cannot find namespace 'React'" in `.next/types/`
**Cause**: Pre-existing bug in Next.js 15 generated type declarations. The `LayoutProps` type references `React.ReactNode` without importing React.
**Impact**: Type-check only — does not affect runtime or production builds.
**Workaround**: Ignore the error — it's in generated code, not your source.
**Fix**: Run `npx tsc --noEmit --skipLibCheck` for CI, or wait for Next.js 15.6+ patch.

## Test Issues

### Backend tests fail locally
**Cause**: Most tests require PostgreSQL + Redis running. 10 tests fail in isolation (state-dependent ordering).
**Workaround**: Run tests against a running Docker Compose stack:
```bash
docker compose up -d postgres redis
cd backend && pytest tests/ -v
```
See `docs/runbooks/` for per-suite troubleshooting.

### Chatbot tests fail locally
**Cause**: 2 tests fail in isolation due to pre-existing ChromaDB mock state.
**Impact**: 0 collection errors; all 1611 other tests pass.
**Workaround**: Run full test suite, not individual files:
```bash
cd chatbot_service && pytest tests/ -v
```

### E2E tests fail in production build
**Cause**: 8 form validation tests fail in `npm run build && npm start` but pass in `npm run dev`.
**Root cause**: React 19 RSC streaming event handler registration timing.
**Impact**: Functional testing in CI uses dev server; production E2E passes all non-form tests.
**Tracking**: [Issue #TBD]

## Runtime Issues

### Backend logs show UnicodeEncodeError on Windows
**Cause**: Emoji characters in log output not supported by Windows console encoding.
**Impact**: No functional impact — logs render correctly on Linux production servers.
**Workaround**: Set `PYTHONIOENCODING=utf-8` before running:
```bash
set PYTHONIOENCODING=utf-8
uvicorn main:app --reload
```

### "Geolocation not supported" in JSDOM tests
**Cause**: JSDOM does not implement `navigator.geolocation`.
**Impact**: 0 test failures — components gracefully degrade with fallback UI.
**Workaround**: None needed — this is expected behavior in test environment.

### WebSocket tracking shows "Connecting..." forever
**Cause**: The tracking WebSocket server requires a running backend. The demo/CI environment needs a WebSocket mock.
**Workaround**: Ensure backend is running on port 8000 before accessing tracking pages.

## Docker Issues

### Docker build fails on Windows
**Cause**: Line ending differences or volume mount path issues.
**Fix**: Use Git Bash or WSL for Docker commands. Ensure `autocrlf` is set to `input`:
```bash
git config core.autocrlf input
```

### Container exits with "permission denied"
**Cause**: The Dockerfile uses a non-root user (`appuser:1001` or `nextjs:1001`).
**Fix**: Ensure all mounted volumes have correct permissions:
```bash
# For bind mounts, the host directory must be readable by UID 1001
chmod -R 755 ./data
```

## Known Issues (v1.0.0)

| ID | Issue | Status | Workaround |
|----|-------|--------|------------|
| K1 | 10 backend tests fail when run in isolation | Known | Run full suite |
| K2 | 2 chatbot tests fail in isolation | Known | Run full suite |
| K3 | 8 E2E form tests fail in production standalone | Known | Test in dev mode |
| K4 | `next lint` shows deprecation warning for App Router | Cosmetic | Run `npx @next/codemod@latest built-in-next-font .` |
| K5 | No WebSocket mock for tracking E2E tests | Known | Manual testing on live backend |

If your issue isn't listed here, search [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues) or open a new one.
