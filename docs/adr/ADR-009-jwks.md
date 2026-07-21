# ADR-009: JWKS-Based JWT Verification

**Date:** 2026-06-28
**Status:** ✅ Accepted
**Author:** SafeVixAI Backend Team

## Context

The backend authenticates users via Supabase Auth, which issues JWTs signed with RS256. The signing keys can rotate at any time. Hardcoding a single public key would break authentication on key rotation.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **JWKS endpoint (chosen)** | Fetch public keys from `https://project.supabase.co/auth/v1/.well-known/jwks.json` | Handles rotation automatically, standard | Extra HTTP call on cold start |
| **Hardcoded public key** | Download JWK once, hardcode in config | No HTTP call | Breaks on key rotation |
| **Supabase SDK** | Use `@supabase/supabase-js` token verification | Simple | Only works client-side |

## Decision

Implement a `JWKSClient` class that:
1. Fetches JWKS from Supabase on startup
2. Caches keys in Redis with atomic refresh (stampede protection)
3. Verifies JWT signature, expiry, issuer, and audience
4. Falls back to existing keys if refresh fails (stale-while-revalidate)
5. Distributed cache via Redlock prevents all instances refreshing simultaneously

## Consequences

- JWTs verified in ~5ms (cached key) vs ~200ms (fresh fetch)
- Key rotation handled transparently
- Redis required for distributed caching (falls back to in-memory cache)
- JWKS endpoint must be accessible from backend deployment
