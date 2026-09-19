# ADR-009: JWKS Token Validation with Atomic Key Fetching

**Status:** Accepted
**Date:** 2026-06-29
**Deciders:** SafeVixAI Backend Team

## Context

The backend validates JWT tokens from two sources:

1. **Supabase Auth** -- RS256 signed tokens, public keys published at a JWKS endpoint
2. **Direct login** -- HS256 signed tokens using a shared secret

For RS256 validation, the backend needs the JWK Set (public keys) from Supabase. Hardcoding keys means manual rotation. Caching keys with a simple TTL risks serving stale keys during a rotation event -- authentication would fail until the cache expires.

## Decision

Implement atomic JWKS fetching with cache stampede protection in `backend/core/jwks.py`:

1. **JWKSClient** -- fetches and caches the JWK Set from the Supabase JWKS endpoint
2. **Stampede protection** -- uses Redlock distributed lock (ADR-005) to ensure only one worker fetches keys at a time
3. **Stale-while-revalidate** -- cached keys are served during revalidation to prevent authentication failures
4. **Graceful fallback** -- if key fetch fails, continue serving existing cached keys
5. **Periodic refresh** -- background task refreshes keys before they expire

## Consequences

**Positive:**
- Zero-touch key rotation -- Supabase can rotate keys without backend deployment
- Cache stampede protection prevents concurrent JWKS fetches
- Authentication continues working during Supabase JWKS endpoint outages

**Negative:**
- Added complexity vs. simple TTL-based caching
- Requires Redis for distributed stampede protection
- First request after deployment may be slow if cache is cold

## References

- `backend/core/jwks.py` -- JWKSClient implementation
- `backend/core/security.py` -- uses JWKSClient for token validation
