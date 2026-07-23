---
name: SafeVixAI Frontend
description: Development guide for the SafeVixAI Next.js 15 frontend — a mobile-first road safety platform with AI features.
---

# SafeVixAI Frontend Skill

## Current Implementation Notes - 2026-06-09 (E2E Hardening)

**GSAP Migration Status:** The frontend is 100% GSAP-powered. All page entries use the `usePageEntry` hook. Timeline cleanups (`gsap.killTweensOf('*')`) are bound to route unmounts inside `GSAPProvider.tsx` to completely prevent animation memory leaks. High-performance GPU-composited properties (`will-change: transform, opacity`) and proper dynamic `clearProps` resets are enforced in `usePageEntry.ts` and `useSplitTextEntry.ts` for 60FPS on high-end and low-end mobile viewports.

**E2E Production Build Notes:** GSAP animations silently fail in the production standalone build (`node .next/standalone/server.js`). All E2E `waitForMount` helpers no longer check for `opacity !== '0'` — instead they wait for `[aria-busy="true"]` loading skeleton to disappear (React RSC streaming complete). Auth-guarded pages use `localStorage.__E2E_SKIP_AUTH__` flag to bypass AuthGuard during tests.

Use these notes before touching the frontend:

- Source of truth for public URLs is `frontend/lib/public-env.ts`.
- Use `NEXT_PUBLIC_API_URL` for the main backend and `NEXT_PUBLIC_CHATBOT_URL` for the chatbot service.
- Do not read `process.env.NEXT_PUBLIC_CHATBOT_BASE_URL` in client components; it is not the validated project env var.
- Chat routes are under `/api/v1/chat/*`.
- Speech routes are under `/speech/*`, not `/api/v1/speech/*`.
- Mic input must call `${PUBLIC_CHATBOT_BASE_URL}/speech/translate`.
- `target_language` must use backend/model codes from `frontend/lib/languages.ts` (4-code mapping: UI→recognition→speechTarget→synthesis).
- Browser recognition codes are locale codes such as `hi-IN`; backend speech target codes are model codes such as `hin`.
- Browser speech output must use `synthesisCode` from language mapping and must provide a stop control.
- Backend speech performs speech-to-text / speech translation only. No backend TTS endpoint exists.
- Keep emergency flows stable: 112, 102, 100, 1033, crash countdown, offline SOS queue, map heatmap, and QR emergency card.
- **Crash Detection Flow Fully Integrated**: `CrashCountdown.tsx` and `ProgressRing.tsx` are fully integrated inside `ClientAppHooks.tsx` crash detection engine. The accelerometer triggers the visually striking countdown overlay before emergency services are dispatched. Includes proper ARIA role (`role="alert"`).
- **Hardened Authentication & API bypass**: Chatbot service integrates with the backend via `X-Internal-Api-Key` service-to-service header injection.

Current verification commands:

```bash
cd frontend && npm run build && npx tsc --noEmit
cd backend && .venv\Scripts\activate && pytest tests/ -v
cd chatbot_service && .venv\Scripts\activate && pytest tests/ -v
cd frontend && npx playwright test e2e/auth-flow.spec.ts   # Single E2E spec
cd frontend && npx playwright test                          # All E2E (55 tests)
```

E2E tests run against production standalone build. Use `CI_SKIP_WEBSERVER=false` for local runs.

---

## What it is
A **Next.js 15** (App Router) + **React 19** + **TypeScript** + **Tailwind CSS** frontend for an AI-powered road safety platform. The design system is called **"Tactical Safety Command Terminal"** — a dark-mode-first interface with emerald-green brand accents and red emergency signals, influenced by Linear (sidebar precision) and VoltAgent (terminal energy).

## Design System — Tactical Safety Command Terminal

> **Source of truth:** `DESIGN.md` at project root. Always consult that file for the complete spec. This section is a quick reference.

### Color Palette
- **Background (Dark):** `#0A0E14` (page canvas) · Light: `#F0F2F5`
- **Surfaces:** `#111520` (cards), `#181D2A` (hover), `#1F2535` (active), `#252B3A` (modals)
- **Brand green:** `#1A5C38` (primary) / `#00C896` (active states, online indicators)
- **Emergency red:** `#DC2626` — used for SOS, emergencies. **Never decorative.**
- **Challan amount:** `#00E676` (monospace fine display)
- **Text (dark):** `#F0F4F8` (primary), `#A8B4C4` (secondary), `#6B7A8D` (tertiary)
- **Text (light):** `#0F1A2E` / `#4A5568` / `#8A95A3`
- **Borders:** `rgba(255,255,255,0.07)` (default dark), `rgba(255,255,255,0.12)` (medium)
- **Warning:** `#D97706` · **Info:** `#3B82F6` · **Ambulance:** `#EA580C`

### Typography
- **Font families:** `Inter Variable` (body/UI) with `font-feature-settings: "cv01", "ss03"`, `Space Grotesk` (headings/compressed titles), `JetBrains Mono` (monospace: IDs, coordinates, fine amounts)
- **Terminal overlines:** `text-[11px] font-semibold uppercase tracking-widest text-slate-400 font-space` — "SENTINEL ACTIVE", section headers
- **Page codename:** `text-2xl font-bold tracking-tight` — compressed hero headings
- **Section labels:** `text-[13px] font-semibold uppercase tracking-[0.05em]` — "LOCATION LOCK", "VEHICLE IDENTIFICATION"
- **Body text:** `text-sm font-normal` (weight 400)
- **Caption/micro:** `text-xs font-semibold uppercase tracking-widest` (weight 600, NOT font-black)

**Critical rule:** `font-black` (900 weight) is ONLY for page hero titles and large amounts (₹10,000). Everything else uses `font-semibold` (600) or `font-normal` (400).

### Components & Shapes
- **Cards/panels:** `rounded-lg` (8px) with `bg-[#111520] border border-white/[0.07]`
- **Feature cards (challan vehicles):** `rounded-[10px]` (10px)
- **Buttons/inputs:** `rounded-md` (6px)
- **Emergency SOS hero card:** `rounded-2xl` (16px) — only exception for large radius
- **Micro badges:** `rounded-[4px]` (OFFLINE, PRIORITY P0)
- **Pills/chips:** `rounded-full` (9999px)
- **Avatars/icon buttons:** `rounded-full` (50%)

**Critical rule:** No `rounded-3xl` anywhere. No `rounded-2xl` on regular cards. Cards = `rounded-lg` (8px).

### Letter Spacing
- Terminal overlines: `tracking-widest` (0.1em) — NOT `tracking-[0.3em]`
- Section labels: `tracking-[0.05em]`
- Body text: `tracking-normal`
- Compressed headings: `tracking-tight` (-0.02em)

### Iconography
- **Primary:** Lucide React icons (`lucide-react`)

## Project Structure
```
frontend/
├── app/
│   ├── page.tsx              ← Dashboard / Map Home
│   ├── layout.tsx            ← Root layout (fonts, providers, theme)
│   ├── error.tsx             ← Global error boundary (catches unhandled errors)
│   ├── globals.css           ← Design tokens + CSS variables + Tailwind config
│   ├── assistant/page.tsx    ← AI Chat Assistant (SSE streaming)
│   ├── bystander/page.tsx    ← Bystander Mode (witness accident assistance)
│   ├── locator/page.tsx      ← Emergency Service Locator + Map
│   ├── first-aid/page.tsx    ← First Aid Guide + AI Vision
│   ├── report/page.tsx       ← Road Hazard Reporter
│   ├── challan/page.tsx      ← Traffic Challan Calculator
│   ├── emergency/page.tsx    ← Emergency Protocol Terminal
│   ├── sos/page.tsx          ← SOS Dispatch Terminal
│   ├── profile/page.tsx      ← Operator Identity Matrix (+ QR Emergency Card)
│   ├── login/page.tsx        ← Operator Authentication (OTP flow)
│   ├── emergency-card/[userId]/page.tsx ← Public QR Emergency Card (no login)
│   ├── settings/page.tsx     ← System Settings
│   ├── share-receive/page.tsx ← Share/Receive location via deep link
│   ├── track/page.tsx        ← Family live tracking viewer (Supabase Realtime)
│   └── tracking/page.tsx     ← GPS tracking management
├── components/
│   ├── AppSidebar.tsx        ← Desktop sidebar navigation (192px, full-height)
│   ├── AuthorityCard.tsx     ← Road authority info card
│   ├── ChallanCalculator.tsx ← Challan computation component
│   ├── ChatInterface.tsx     ← Chat UI (online/offline toggle)
│   ├── ClientAppHooks.tsx    ← Global sensor listeners (crash detection, offline sync)
│   ├── ConnectivityBadge.tsx ← Online/Offline status indicator
│   ├── ConnectivityProvider.tsx ← Network state context provider
│   ├── DrivingScoreBar.tsx   ← Driving safety score display
│   ├── EmergencyMap.tsx      ← Emergency map wrapper (dynamic)
│   ├── EmergencyMapInner.tsx ← Map rendering internals
│   ├── EmergencyNumbers.tsx  ← 112/102/100 quick dial grid
│   ├── EnterpriseClientAppHooks.tsx ← Enterprise-grade sensor hooks
│   ├── FirstAidCard.tsx      ← First aid scenario card
│   ├── GlobalSOS.tsx         ← Floating SOS button (all pages except map/sos)
│   ├── ModelLoader.tsx       ← AI model loading indicator
│   ├── NetworkMonitor.tsx    ← Network connectivity monitor
│   ├── PageShell.tsx         ← Layout wrapper with GlobalSOS
│   ├── PotholeDetector.tsx   ← In-browser YOLO pothole detection
│   ├── ReportForm.tsx        ← Road report submission form
│   ├── ServiceCard.tsx       ← Emergency service result card
│   ├── SOSButton.tsx         ← SOS dispatch button with pulse animation
│   ├── ThemeProvider.tsx     ← Theme context provider
│   ├── ViolationsList.tsx    ← Traffic violations list
│   ├── VoiceInput.tsx        ← Web Speech API voice input
│   ├── dashboard/            ← 15 dashboard components (BottomNav, SystemHeader, SystemSidebar, TopSearch, ProfileCard, FloatingSidebarControls, Toast, SkeletonCard, etc.)
│   ├── chat/                 ← multimodal-ai-chat-input.tsx
│   ├── maps/                 ← MapLibreCanvas.tsx (dynamic import, SSR disabled)
│   ├── profile/              ← QREmergencyCard.tsx
│   ├── report/               ← HazardViewfinder.tsx (camera viewport)
│   └── ui/                   ← shadcn/ui primitive components
└── lib/
    ├── store.ts              ← Zustand global state (GPS, services, AI mode, auth)
    ├── api.ts                ← Backend API client (JWT Bearer token injected)
    ├── public-env.ts         ← Validated NEXT_PUBLIC env vars (fail-fast if missing)
    ├── safety-constants.ts   ← Crash/SOS/tracking constants (thresholds, timeouts)
    ├── client-logger.ts      ← Client-side error logging utility
    ├── geolocation.ts        ← GPS utilities
    ├── sos-share.ts          ← SOS link generators
    ├── offline-sos-queue.ts  ← IndexedDB queue for offline SOS dispatch
    ├── crash-detection.ts    ← DeviceMotionEvent crash detection engine
    ├── live-tracking.ts      ← Family live tracking via Supabase Realtime
    ├── deep-link.ts          ← App deep linking (share/receive)
    ├── navigation-launch.ts  ← Turn-by-turn navigation launcher
    ├── routing.ts            ← Route calculation (OSRM)
    ├── share.ts              ← Web Share API utilities
    ├── emergency-numbers.ts  ← Emergency number database
    ├── analytics-provider.tsx ← PostHog analytics wrapper
    ├── offline-ai.ts         ← WebLLM Phi-3 offline AI
    ├── duckdb-challan.ts     ← DuckDB-Wasm offline challan calculator
    ├── traffic-layer.ts      ← Traffic data map layer
    ├── safe-spaces-layer.ts  ← Safe spaces map layer
    ├── edge-ai.ts            ← Edge AI model utilities
    ├── location-tracker.ts   ← Background location tracking
    ├── location-utils.ts     ← Location calculation utilities
    ├── reverse-geocode.ts    ← Reverse geocoding
    ├── geocoding.ts          ← Forward geocoding (Photon/BigDataCloud)
    ├── map-defaults.ts       ← Map default settings (center, zoom)
    ├── maps-fallback.ts      ← Map tile fallback logic
    ├── offline-rag.ts        ← Offline RAG search
    ├── india-locations.ts    ← India city/state data
    ├── user-profile.ts       ← User profile management
    └── utils.ts              ← Shared utility functions
```

## Navigation Architecture
- **Mobile:** `TopSearch` (top) + `BottomNav` (bottom, 64px) + `SystemSidebar` (hamburger drawer)
- **Desktop (lg+):** `SystemHeader` (top bar 52px with search/theme/connectivity) + sidebar 192px (collapsed) / 280px (expanded with emergency dial)
- **SOS:** `GlobalSOS` component floats on all interior pages; hidden on `/`, `/sos`, `/emergency`

## Key Conventions
1. Every page is `'use client'` (client-side interactivity required everywhere)
2. Use **Tailwind utility classes** exclusively (no inline `style={}`)
3. Bottom nav auto-detects active route via `usePathname()`
4. All pages use `pb-44` on `<main>` to clear the floating BottomNav
5. Fixed header: `z-50`, `backdrop-blur`, content starts at `pt-28 lg:pt-24`
6. Map components use `dynamic(() => import(...), { ssr: false })` to avoid hydration issues
7. Theme: dark-mode-first, `data-theme` attribute set via blocking `theme-init.js` script in `public/` (loaded via `<Script strategy="beforeInteractive" />` — no dangerouslySetInnerHTML)
8. Emergency numbers: 112 (universal), 102 (ambulance), 100 (police), 101 (fire), 1033 (NHAI)
9. **No login button in header** — login is only accessible via `/login` URL
10. CSS variables defined in `:root` of `globals.css` — always use these, not hardcoded hex
11. **Global error boundary** (`app/error.tsx`) catches all unhandled errors — never shows white screen
12. **Environment validation** — all `NEXT_PUBLIC_*` URLs validated via `lib/public-env.ts` — missing vars throw at import time

## CSS Variables (Quick Reference)
```css
:root {
  --navbar-bottom-h: 64px;
  --card-radius:     8px;   /* rounded-lg */
  --btn-radius:      6px;   /* rounded-md */
  --sidebar-width:   192px;
}
```

## Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| Next.js | 15.x | React framework (App Router) |
| React | 19.x | UI library |
| Tailwind CSS | 3.x | Utility-first CSS |
| `gsap` | 3.15.x | Core animation engine |
| `@gsap/react` | 2.1.x | React GSAP hooks |
| `maplibre-gl` | 5.x | Vector map rendering |
| `zustand` | 5.x | Global state management |
| `lucide-react` | 0.4x | Icon library |
| `@mlc-ai/web-llm` | - | Offline AI (browser-based LLM) — partially implemented, 2.2GB model download |
| `@turf/turf` | - | Geospatial utilities |
| `qrcode.react` | - | QR code generation for Emergency Card |
| `posthog-js` | - | Product analytics |
| `@supabase/supabase-js` | - | Supabase Realtime for live tracking |

## Instructions for building new pages
1. Import the shared layout components: `SystemHeader`, `TopSearch`, `SystemSidebar`, `BottomNav`
2. Use theme-consistent backgrounds via CSS variables (never hardcode hex colors)
3. Wrap content in `<main className="flex-1 w-full max-w-2xl mx-auto pt-28 lg:pt-24 pb-44 px-6">`
4. Use section overline labels: `text-[11px] font-semibold uppercase tracking-widest text-slate-400 font-space`
5. Use standard cards: `rounded-lg bg-[#111520] dark:bg-[#111520] border border-white/[0.07]`
6. Test at 390px (mobile), 768px (tablet), and 1440px (desktop) breakpoints
7. All interactive elements must have `active:scale-95 transition-all` and min 44×44px touch targets
8. **Never use `font-black`** for labels, captions, or body text — only for page hero titles
9. **Never use `rounded-2xl` or `rounded-3xl`** for cards — use `rounded-lg` (8px)
10. **Never use `tracking-[0.3em]`** — use `tracking-widest` (0.1em) for overlines

## Backend & Chatbot (for full-stack context)

| Service | Port | Key Tech | Tests |
|---|---|---|---|---|
| Backend | `:8000` | FastAPI, PostgreSQL + PostGIS, Redis | **1365/1365** passing, hardened |
| Chatbot | `:8010` | FastAPI, 9 LLMs providers, ChromaDB, 13 agent tools | **892/892** passing, 95% cov |
| Frontend | `:3000` | Next.js 15, MapLibre GL, Zustand, WebLLM Phi-3 | **572/572** passing, 0 lint warnings |

### Production Alerting
- `alert_service.py` at project root — shared by both backend and chatbot
- Sends email on: all LLM providers failing, database down, external API 5xx, unhandled exceptions
- Each alert includes 3 solutions + 5-min cooldown
- Config: `ALERT_EMAIL` + `ALERT_EMAIL_PASSWORD` (Gmail App Password) in `.env`

### Auto-Generated Documentation
- 231 wiki pages in `docs/wiki/content/` — generated by `scripts/wiki_manager.py`
- Uses OpenRouter → Mistral → Gemini fallback chain
- Includes mermaid diagrams, tables, and architecture sections
- CI triggers on push via `sync-wiki.yml`; DOCX master doc via `update-master-doc.yml`
- **Do not manually edit** wiki content files — they are overwritten by automation
