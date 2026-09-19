# Frontend + UI/UX Audit Report â€" SafeVixAI

> **SNAPSHOT**: This document reflects the state as of 2026-05-25. For current state see [AGENTS.md](https://github.com/SafeVixAI/SafeVixAI/blob/main/AGENTS.md).

**Initial Date:** 2026-05-19  
**Last Updated:** 2026-05-22  
**Scope:** `frontend/` â€" Next.js 15 PWA (22 routes, 44+ components, 28+ lib modules)  
**Auditor:** Principal Frontend Architect & Performance Engineer  
**Initial Score:** 7.0/10 (B-)  
**Current Score:** 8.0/10 (B+)

---

## Executive Summary

SafeVixAI's frontend is a Next.js 15 App Router PWA with a polished "Tactical Safety Command Terminal" design system. The GSAP migration is complete, Zustand state management uses granular selectors, SWR is configured for API caching, and offline-first capabilities are well-implemented.

**Strengths:** GSAP animation system (Framer Motion removed), Zustand granular selectors, SWR data fetching, PWA offline capabilities, design token consistency, global error boundary, Sentry integration, focus trap in crash dialog.

**Phase 3 Additions:** GSAP migration (useGSAP hook, stagger/split text), SWR provider in layout, language mapping (11 Indian languages), speech synthesis voice output, PostHog analytics provider.

---

## 1. Architecture & Structure

### 1.1 App Router Organization
| Metric | Value | Assessment |
|--------|-------|------------|
| Total routes | 22 | âœ... Appropriate for scope |
| Client components | ~95% | ðŸ"´ Misses SSR opportunities |
| Dynamic imports | MapLibre only | âš ï¸ Should lazy-load heavy components |
| Error boundary | Global `error.tsx` | âœ... Present |
| Loading states | Skeleton components exist | âš ï¸ Not used on all routes |
| Layout nesting | Single root layout | âœ... Correct |
| API routes | 1 (w3w proxy) | âœ... Minimal surface |

### 1.2 NOTE: 100% Client-Side Rendering
**Severity:** MEDIUM (downgraded from CRITICAL â€" intentional for PWA)  
**Scope:** All pages

**Context:** Every page uses `'use client'` directive. This is an INTENTIONAL design choice for this PWA â€" the app is a safety tool that MUST work offline, and Server Components cannot access browser APIs (geolocation, accelerometer, IndexedDB, service worker). SSR would add complexity without benefit for this use case.

**Acceptance:** This is not a bug. For a Project PWA with offline-first requirements, 100% client-side rendering is the correct approach. Revisit if SEO becomes a requirement.

---

## 2. State Management

### 2.1 Zustand Store
| Feature | Status | Assessment |
|---------|--------|------------|
| Granular selectors | âœ... 28 exported | âœ... No full-store subscriptions |
| GPS state | âœ... Isolated | âœ... Doesn't trigger full re-render |
| Auth state | âœ... Isolated | âœ... Clean session management |
| Connectivity state | âœ... Present | âœ... Online/offline detection |
| Persisted state | âš ï¸ Partial | âš ï¸ Some state not persisted |

### 2.2 MEDIUM: No State Persistence Strategy
**Severity:** MEDIUM  
**File:** `frontend/lib/store.ts`

**Problem:** Zustand store is in-memory only. Page refresh loses all state (GPS, services, AI mode).

**Fix:**
1. Add `zustand/middleware` persist for non-sensitive state
2. Use IndexedDB for large state (map preferences)
3. Never persist auth tokens or GPS coordinates

---

## 3. Performance

### 3.1 Bundle Analysis
| Concern | Status | Assessment |
|---------|--------|------------|
| Bundle analysis configured | âŒ Missing | ðŸ"´ No visibility |
| Three.js usage | âš ï¸ Present | âš ï¸ 600KB+ for decorative element |
| MapLibre GL | âœ... Dynamic import | âœ... Loaded on demand |
| WebLLM | âš ï¸ Large | âš ï¸ 2.2GB model download |
| Transformers.js | âš ï¸ Large | âš ï¸ ~2MB+ in bundle |
| GSAP | âœ... Tree-shaken | âœ... Only used hooks imported |

### 3.2 HIGH: No Bundle Analysis
**Severity:** HIGH  
**Scope:** Frontend build

**Problem:** No `@next/bundle-analyzer` configured. Cannot identify bundle bloat or optimize imports.

**Fix:**
1. Add `@next/bundle-analyzer` to `next.config.js`
2. Run analysis before each release
3. Set bundle size budgets (e.g., main chunk < 200KB)

### 3.3 HIGH: Three.js for Decorative Element
**Severity:** HIGH  
**File:** `frontend/components/dashboard/ThreeDrivingScore.tsx`

**Problem:** Three.js (600KB+ gzipped) is used only for a decorative 3D driving score visualization.

**Fix:**
1. Dynamic import: `dynamic(() => import('./ThreeDrivingScore'), { ssr: false, loading: Skeleton })`
2. Consider replacing with CSS animation or SVG
3. Load only when component is in viewport (IntersectionObserver)

---

## 4. API Client

### 4.1 Axios Configuration
| Feature | Status | Assessment |
|---------|--------|------------|
| Base URL config | âœ... Environment-based | âœ... `NEXT_PUBLIC_BACKEND_URL` |
| Timeout | âœ... 8 seconds | âœ... Reasonable |
| CSRF interceptor | âœ... Present | âœ... Reads cookie, sets header |
| Retry interceptor | âœ... Present | âœ... Exponential backoff (1s/2s/4s) |
| Error handling | âš ï¸ Basic | âš ï¸ No structured error types |

### 4.2 âœ... RESOLVED: SWR API Caching Layer Added
**Severity:** MEDIUM â†' RESOLVED  
**File:** `frontend/app/layout.tsx`

**Resolution:** SWRConfig is now configured in the layout.tsx providers stack. API calls are deduplicated with stale-while-revalidate strategy. The `SWRConfig` provider wraps the entire app. Verify individual components use `useSWR` instead of raw fetch where appropriate.

---

## 5. PWA & Offline

### 5.1 Service Worker
| Feature | Status | Assessment |
|---------|--------|------------|
| Cache strategy | âœ... Cache-first for static | âœ... Good |
| Offline data | âœ... GeoJSON, CSV, JSON | âœ... Comprehensive |
| SOS queue | âœ... IndexedDB | âœ... Per-item transactions |
| Auth headers in SW | âœ... Present | âœ... Authorization header included |
| Background sync | âœ... Present | âœ... `sos-queue-flush` tag |

### 5.2 âœ... GOOD: Offline Architecture
The offline-first implementation is enterprise-grade:
- IndexedDB SOS queue with per-item transactions
- Service Worker flushes queue with auth headers
- DuckDB-Wasm for offline challan calculations
- WebLLM for offline AI (Phi-3 Mini)
- Graceful degradation when offline

---

## 6. Accessibility

### 6.1 WCAG Compliance
| Feature | Status | Assessment |
|---------|--------|------------|
| Focus trap (crash dialog) | âœ... Present | âœ... WCAG 2.1 SC 2.4.3 |
| aria-current (nav) | âœ... Present | âœ... WCAG 2.1 SC 4.1.2 |
| prefers-reduced-motion | âœ... Present | âœ... Skips animations |
| Color contrast | âš ï¸ Not verified | âš ï¸ Needs testing |
| Screen reader labels | âš ï¸ Partial | âš ï¸ Some icons lack labels |
| Keyboard navigation | âš ï¸ Partial | âš ï¸ Not all interactive elements focusable |

### 6.2 MEDIUM: Incomplete Accessibility
**Severity:** MEDIUM  
**Scope:** All components

**Problem:** axe-core tests exist but coverage is incomplete. Many components lack proper ARIA labels, roles, and keyboard navigation.

**Fix:**
1. Run full axe-core audit on all pages
2. Add `aria-label` to all icon buttons
3. Ensure all interactive elements are keyboard-focusable
4. Add skip-to-content link

---

## 7. UI Consistency

### 7.1 Design System
| Component | Consistency | Assessment |
|-----------|-------------|------------|
| Color tokens | âœ... Consistent | âœ... Dark navy theme |
| Typography | âœ... Consistent | âœ... Inter + Space Grotesk |
| Spacing | âœ... Consistent | âœ... Tailwind spacing scale |
| Components | âš ï¸ Mixed | âš ï¸ shadcn/ui + custom |
| Animations | âœ... Consistent | âœ... GSAP throughout |

### 7.3 MEDIUM: Mixed Component Libraries
**Severity:** MEDIUM  
**Scope:** All components

**Problem:** Mix of shadcn/ui components, custom components, and inline styles. No unified component library.

**Fix:**
1. Migrate all reusable UI to shadcn/ui
2. Create design token system in CSS variables
3. Document component usage guidelines

---

## Frontend Score Summary

| Area | Score | Grade |
|------|-------|-------|
| Architecture | 7/10 | B- |
| State Management | 8/10 | B+ |
| Performance | 7/10 | B- |
| API Client | 8/10 | B+ |
| PWA/Offline | 9/10 | A- |
| Accessibility | 6/10 | C+ |
| UI Consistency | 8/10 | B+ |
| Animations (GSAP) | 9/10 | A- |
| **Overall** | **8.0/10** | **B+** |

**Phase 3 Improvements:** GSAP migration, SWR caching layer, language mapping, PostHog analytics, speech synthesis output, voice input pipeline.
