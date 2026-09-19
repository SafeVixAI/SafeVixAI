# SafeVixAI — Frontend UX 95+ Plan

> Current UX score: **68/100**
> Target: **95/100**
> Estimated effort: **120-160 hours** (3-4 weeks, 1 senior engineer)

---

## Phase 0: Foundation — Design System (40hrs — +15pts)

### 0.1 Component Library (`frontend/components/ui/`)
Create these reusable primitives. Every page must use ONLY these — zero per-page button styling.

| Component | Props | Purpose | Priority |
|-----------|-------|---------|----------|
| `Button` | `variant: primary | emergency | ghost | ghost-danger | filter`, `size: sm | md | lg`, `loading?: boolean`, `icon?: LucideIcon`, `fullWidth?: boolean` | Replaces every `<button>` in the app | P0 |
| `Select` | `options: Option[]`, `value`, `onChange`, `label`, `placeholder`, `error?: string` | Replaces every `<select>` with consistent styled version | P0 |
| `EmptyState` | `icon: LucideIcon`, `title`, `description`, `action?: { label, onClick }` | Universal empty state for all lists | P0 |
| `ErrorState` | `message`, `retry?: () => void`, `icon?: LucideIcon` | Universal error state for all async views | P0 |
| `LoadingSkeleton` | `variant: card | list | page | map`, `count?: number` | Universal skeleton for all loading states | P0 |
| `Toast` | Wraps Sonner with app-specific presets: `toast.success()`, `toast.error()`, `toast.warning()`, `toast.safety()` (critical, duration: 0) | Standardized toast patterns | P1 |
| `Card` | `variant: elevated | outline | hero`, `padding: sm | md | lg`, `accentColor?: string` | Universal card with consistent padding and border radius | P1 |
| `StatusBadge` | `variant: success | warning | error | info | offline`, `pulsing?: boolean`, `label: string` | Universal status indicator | P1 |
| `Modal` | `open`, `onClose`, `title`, `children`, `footer?: ReactNode`, `size: sm | md | lg` | Universal modal with focus trap, Esc to close, backdrop | P1 |
| `ProgressBar` | `value: number`, `max: number`, `variant: determinate | indeterminate`, `color?: string` | Universal progress | P2 |

**Acceptance criteria for Phase 0:**
- `grep -r "bg-red-500\|bg-brand\|bg-\[--emergency\]" frontend/app` returns zero matches for button styling
- Every interactive element passes 44px touch target check
- Every `<select>` in the app uses the `Select` component with `aria-label`

---

### 0.2 Design Tokens Audit (`frontend/app/globals.css`)
- [ ] Add `--radius-sm: 6px`, `--radius-md: 8px`, `--radius-lg: 12px`, `--radius-xl: 16px`, `--radius-hero: 24px` — tokenize ALL border-radius values
- [ ] Add `--color-emergency-rgb: 220, 38, 38` — separate RGB channels for rgba() usage in JS
- [ ] Add `--color-brand-rgb: 26, 92, 56` — same
- [ ] Add `--color-warning-rgb: 217, 119, 6` — same
- [ ] Add `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl` — tokenize ALL shadows
- [ ] Add `--font-size-micro: 10px`, `--font-size-caption: 11px`, `--font-size-body: 14px`, `--font-size-h3: 16px`, `--font-size-h2: 20px`, `--font-size-h1: 24px` — tokenize ALL font sizes
- [ ] Verify `prefers-color-scheme: light` block in globals.css has ALL the same overrides as `[data-theme='light']`

---

## Phase 1: Kill The White Flash (8hrs — +8pts)

### 1.1 Fix `!mounted return null` Pattern
Files that return `null` on first render:

| File | Current | Fix |
|------|---------|-----|
| `FirstAidClient.tsx:166` | `if (!mounted) return null` | Replace with skeleton grid matching the actual layout (6 placeholder cards with shimmer) |
| `report/page.tsx:282` | `if (!mounted) return null` | Replace with skeleton matching the full form layout |
| `emergency/page.tsx:186` | Uses skeleton (good) | Already fixed — verify |
| `track/[session_id]/page.tsx` | Uses spinner (good) | Already fixed |

**Pattern to enforce:** Every client component that uses `mounted` must render a meaningful skeleton/graybox before hydration, never `null`.

### 1.2 Skeleton Audit — Every Async View Must Have A Skeleton
- [ ] Challan: add skeleton for result card while SWR loads (instead of `blur-sm` opacity trick)
- [ ] Profile: add skeleton while Zustand hydrates from IndexedDB
- [ ] Tracking: add skeleton for the join form while auth resolves
- [ ] Command Center: add skeleton for KPI cards + table while API loads
- [ ] First Aid: add skeleton grid (done in 1.1)
- [ ] AI Assistant: current typing dots are sufficient
- [ ] Locator: current `SkeletonCard` components are sufficient

---

## Phase 2: Error State Coverage (10hrs — +10pts)

### 2.1 Every API Call Must Have An Error UI
Audit every `fetch`, `axios`, `useSWR`, and `useEffect` data load. If it can fail, the user must see it.

| File | Current Error UX | Fix |
|------|-----------------|-----|
| `challan/page.tsx` | `keepPreviousData` hides failure — shows Rs. 0 | Add `ErrorState` with retry button + "Unable to calculate fine" message |
| `command-center/page.tsx` | API errors silently caught with `console.error` | Add red banner "Dashboard data unavailable — retrying..." with retry button |
| `assistant/page.tsx` | Toast with retry (good) | Already partially fixed |
| `ChatInterface.tsx` | Toast with retry (good) | Already partially fixed |
| `locator/page.tsx` | Route error shown (good) | Adequate |
| `report/page.tsx` | Multiple error paths (excellent) | Reference implementation |
| `bystander/page.tsx` | GPS error shown, backend submit silently caught | Add error toast on submit failure |
| `Family Tracking` | No error on auth failure — button just disabled | Show inline error "Authentication required — please log in" |

### 2.2 Error Recovery Pattern
Every error state must offer:
1. Clear description of what went wrong
2. A `Retry` button that re-triggers the failed action
3. A fallback action (e.g., "Try Offline Mode" / "Call 112 instead")

---

## Phase 3: Light Mode Perfection (12hrs — +8pts)

### 3.1 Audit Every Page for Light Mode
Visit EVERY page in light mode and screenshot. Fix:
- [ ] `sos/page.tsx`: ~15 `dark:text-[#e4bebc]` overrides — remove the `dark:` variants where `text-text-2` already provides correct light-mode color
- [ ] `tracking/page.tsx`: Verify member badges, status badges, leave button in light mode
- [ ] `track/[session_id]/page.tsx`: Verify telemetry grid, call buttons, live badge in light mode
- [ ] `bystander/page.tsx`: Verify steps, call bar, GPS status in light mode
- [ ] `command-center/page.tsx`: Verify KPI cards, tables, leaderboard in light mode
- [ ] `officer/page.tsx`: Verify workload cards, resolution drawer in light mode
- [ ] `login/page.tsx`: Verify card, scan line, inputs in light mode
- [ ] `offline/page.tsx`: Verify card, links in light mode
- [ ] `profile/page.tsx`: Verify vitals cards, achievements in light mode
- [ ] `settings/page.tsx`: Verify theme selector, toggles in light mode

### 3.2 Light Mode QA Checklist
- [ ] All cards have visible borders (1px solid `var(--border)`)
- [ ] Text contrast ≥ 4.5:1 for all body text
- [ ] Skeleton shimmer uses light mode gradient colors
- [ ] Map tiles are CartoDB Light in light mode (not Dark)
- [ ] Shadows are subtle drops (not invisible or too dark)
- [ ] Brand green meets 4.5:1 on white (`#145230` ✓, `#00C896` ✗ on white)

---

## Phase 4: Content Freshness (16hrs — +10pts)

### 4.1 API-Driven Content
Current hardcoded content that must become API/DB-driven:

| Content | Location | Current | Target |
|---------|----------|---------|--------|
| Emergency protocols | `emergency/page.tsx:38-108` | Hardcoded array | `GET /api/v1/protocols` → cached in IndexedDB |
| Bystander steps | `bystander/page.tsx` | Hardcoded array | `GET /api/v1/bystander/steps` → cached offline |
| First aid guides | `public/offline-data/first-aid.json` | Static JSON | `GET /api/v1/first-aid` → cached in service worker |
| CPR guide | `first-aid/page.tsx:26-41` | Hardcoded object | Move to first-aid.json or API |
| Emergency fallback numbers | `locator/locator-utils.ts:105-113` | Hardcoded | `GET /api/v1/emergency/numbers` → cached |
| Protocol categories/colors | `emergency/page.tsx:19` | Hardcoded | `GET /api/v1/protocols/categories` |

### 4.2 Admin Dashboard
- [ ] Create `/admin/protocols` page for editing emergency protocols
- [ ] Create `/admin/first-aid` page for editing first aid guides
- [ ] Create `/admin/emergency-numbers` page for editing fallback numbers
- [ ] All admin changes publish to API → auto-sync to app

---

## Phase 5: Consistency Pass (16hrs — +10pts)

### 5.1 Button Standardization
Replace every button in the app with the new `Button` component:

| Current Pattern | Occurrences | Replace With |
|----------------|-------------|--------------|
| `bg-red-500` / `bg-[--emergency]` | ~20 | `<Button variant="emergency">` |
| `bg-brand` / `bg-brand-light` | ~15 | `<Button variant="primary">` |
| `bg-white/5 border-border` | ~25 | `<Button variant="ghost">` |
| Filter chips with per-page styling | ~4 pages | `<Button variant="filter">` |
| SOS floating button | Emergency, SOS page | `<Button variant="emergency" size="xl" isRound>` |

### 5.2 Card Standardization
Replace every card with the `Card` component:
- [ ] Emergency protocol cards
- [ ] First aid guide cards
- [ ] Locator service cards
- [ ] Challan result card
- [ ] Profile vitals cards
- [ ] Tracking member badges
- [ ] Command center KPI cards
- [ ] Bystander step cards

### 5.3 Loading Standardization
Replace every loading pattern with `LoadingSkeleton`:
- [ ] `FirstAidClient:166` → `null` → `<LoadingSkeleton variant="card" count={6} />`
- [ ] `report/page.tsx:282` → `null` → `<LoadingSkeleton variant="page" />`
- [ ] `challan/page.tsx` → `blur-sm` → `<LoadingSkeleton variant="card" />`
- [ ] `profile/page.tsx` → no loading → `<LoadingSkeleton variant="card" />`
- [ ] `settings/page.tsx` → `0.0 KB` → `<LoadingSkeleton variant="list" />`

### 5.4 Empty State Standardization
Replace every empty-list scenario with `EmptyState`:
- [ ] First Aid search 0 results → `<EmptyState icon={SearchX} title="No protocols" action="Clear search" />`
- [ ] Emergency filter 0 results → Done in last session
- [ ] Challan no data → `<EmptyState icon={Scale} title="Select violation" action="Choose from dropdown" />`
- [ ] ChatInterface first visit → add `<SuggestedInquiries />` (copy from assistant page)
- [ ] Command Center empty complaints → `<EmptyState icon={CheckCircle} title="No pending complaints" />`
- [ ] Tracking no members → `<EmptyState icon={Users} title="No members yet" description="Share your group code" />`

### 5.5 Error State Standardization
Replace every error scenario with `ErrorState`:
- [ ] Challan API failure
- [ ] Command Center API failure
- [ ] Bystander submit failure
- [ ] Family Tracking auth failure

---

## Phase 6: Mobile Polish (8hrs — +5pts)

### 6.1 Touch Target Sweep
- [ ] Verify ALL interactive elements are ≥ 44×44px at 375px viewport
- [ ] Fix `bottom-nav` items to 48px min-height
- [ ] Fix filter chips to 44px min-height
- [ ] Fix locator service card buttons to 44px

### 6.2 Keyboard Overlap
- [ ] Chat input: use `visualViewport` API to adjust position when keyboard opens
- [ ] Report form: ensure submit button is visible when keyboard is open

### 6.3 Safe Area Insets
- [ ] Audit every `fixed bottom-*` element for `env(safe-area-inset-bottom)`
- [ ] Audit every `fixed top-*` element for `env(safe-area-inset-top)` (notch)
- [ ] Reference: `globals.css` has `.pb-safe` utility — use it consistently

### 6.4 Map Mobile Size
- [ ] Locator: increase mobile map to `min-h-[40vh]` (currently 320px)
- [ ] Tracking: increase mobile map to `min-h-[40vh]`

---

## Phase 7: Enterprise Animations (8hrs — +5pts)

### 7.1 Gap Fill
Pages missing GSAP entry animations:
- [ ] `/assistant` page — add stagger entry for messages on load
- [ ] `/report` page — add form section entrance on mount
- [ ] `/sos` page — add card stagger on mount
- [ ] `/tracking` page — add form entry animation
- [ ] `/settings` page — add section stagger on mount

### 7.2 Animation Quality
- [ ] Add `will-change: transform, opacity` on persistently animating elements (SOS cards, pulse rings, typing dots)
- [ ] Remove legacy `useGSAP(callback, [])` bare array syntax from `TypingIndicator.tsx:29` and `FirstAidClient.tsx:534`
- [ ] Remove unused GSAP plugin registrations (`ScrollTrigger`, `Flip`, `Observer` in `lib/gsap.ts`)

### 7.3 Progress Indicator
- [ ] Add route transition progress bar (NProgress-style) at the top of `layout.tsx`
- [ ] GSAP-animated bar fills from 0 to 100% during Next.js route transitions
- [ ] Fades out on completion

---

## Phase 8: Accessibility — WCAG 2.1 AA (8hrs — +5pts)

### 8.1 Keyboard Navigation
- [ ] Map: arrow keys pan, +/- zoom — verify current implementation
- [ ] Modal focus traps: verify CommandPalette + KeyboardShortcutsHelp traps (done in last session)
- [ ] Skip link: verify `AppFrame.tsx:54` skip-to-content works on all pages
- [ ] Tab order: verify logical tab flow on every page

### 8.2 Screen Reader
- [ ] Every `<select>` has `aria-label` or associated `<label>`
- [ ] Every icon button has `aria-label`
- [ ] Every loading state has `aria-live="polite"`
- [ ] Every error state has `role="alert"`
- [ ] Every modal has `role="dialog"` + `aria-modal="true"` + `aria-labelledby`

### 8.3 Color Contrast
- [ ] `--text-3` light mode: verify `#5A6A80` on white = 4.5:1 (done in last session)
- [ ] `--brand-light` (`#00C896`) on white = 3.2:1 — fails AA for body text. Only use for large/hero text
- [ ] Verify all status dot colors meet 3:1 (minimum for non-text elements)

### 8.4 Reduced Motion
- [ ] Verify `GSAPProvider` `prefers-reduced-motion: reduce` → `timeScale(1000)` works
- [ ] Verify `globals.css` `animation-duration: 0.01ms !important` works
- [ ] All `repeat: -1` animations (pulse, glow, ping) must respect reduced motion

---

## Phase 9: Content & Copy (6hrs — +4pts)

### 9.1 Microcopy Audit
- [ ] Replace all technical/developer jargon with user-facing language
  - "Tactical Center" → "Emergency Center"
  - "Satellite Lock" → "GPS Active"
  - "Protocol Terminal" → "Emergency Guides"
  - "Intel Folders Accessed" → "Protocols Available"
- [ ] Add helpful tooltips on complex features (family tracking, challan jurisdiction)
- [ ] Add error messages that explain WHAT to do, not just what went wrong

### 9.2 First-Use Experience
- [ ] `/assistant` → add suggested queries on first visit (done)
- [ ] `/locator` → add "Allow location access" prompt explanation before browser dialog
- [ ] `/tracking` → add "How family tracking works" tooltip or info modal
- [ ] `/challan` → add tooltip "What is jurisdiction?" explaining state selection
- [ ] `/report` → add "What happens after I submit?" info section

### 9.3 Empty State Copy
Every empty state must answer these questions:
1. Why is this empty? (e.g., "No protocols match your filter")
2. What should the user do? (e.g., "Try a different category")
3. Is there a quick action? (e.g., "Show All" button)

---

## Phase 10: Performance UX (6hrs — +3pts)

### 10.1 Loading Perception
- [ ] Add instant route transitions (no white flash between pages): use `Next.js` `loading.tsx` files
- [ ] Add `loading.tsx` for: `/locator`, `/emergency`, `/first-aid`, `/challan`, `/assistant`, `/sos`, `/tracking`
- [ ] Preload critical data: emergency numbers, user profile, first aid index
- [ ] Preconnect to API domains: `<link rel="dns-prefetch" href="//api.safevixai.com">`

### 10.2 Perceived Performance
- [ ] Add optimistic UI for toggle actions (settings switches update instantly)
- [ ] Add skeleton thresholds: show skeleton if loading > 300ms, hide after 200ms of content
- [ ] Add stale-while-revalidate pattern: show cached data instantly, refresh in background

---

## Phase 11: Testing UX (8hrs — +3pts)

### 11.1 Visual Regression Tests
- [ ] Add Storybook stories for every component in Phase 0
- [ ] Add Chromatic/Percy visual snapshot tests
- [ ] Run at 375px, 768px, 1280px viewports

### 11.2 UX Integration Tests
- [ ] Test: "User sees skeleton on page load → content appears → error shows retry → retry succeeds"
- [ ] Test: "User submits form offline → toast shows queued → goes online → auto-submits"
- [ ] Test: "User in light mode → all pages have visible borders and adequate contrast"
- [ ] Test: "User tabs through modal → focus wraps → Escape closes → focus returns"

### 11.3 Accessibility Tests
- [ ] Add `jest-axe` tests for every page
- [ ] Target: 0 accessibility violations

---

## Scoring Matrix

| Phase | Hours | Score Impact | Cost per Point |
|-------|-------|-------------|----------------|
| 0 — Design System | 40 | +15pts | 2.7hrs/pt |
| 1 — Kill White Flash | 8 | +8pts | 1.0hrs/pt |
| 2 — Error States | 10 | +10pts | 1.0hrs/pt |
| 3 — Light Mode | 12 | +8pts | 1.5hrs/pt |
| 4 — Content Freshness | 16 | +10pts | 1.6hrs/pt |
| 5 — Consistency Pass | 16 | +10pts | 1.6hrs/pt |
| 6 — Mobile Polish | 8 | +5pts | 1.6hrs/pt |
| 7 — Animations | 8 | +5pts | 1.6hrs/pt |
| 8 — Accessibility | 8 | +5pts | 1.0hrs/pt |
| 9 — Content & Copy | 6 | +4pts | 1.5hrs/pt |
| 10 — Performance UX | 6 | +3pts | 2.0hrs/pt |
| 11 — Testing | 8 | +3pts | 2.7hrs/pt |
| **Total** | **146** | **+86pts** | **1.7hrs/pt avg** |

**Note:** 146 hours would bring theoretical max to 68+86 = 154/100. Realistically, the combination of improvements will compound to ~95/100 as the worst items get fixed.

---

## Quick Wins (First 24 Hours)

Focus these in order for maximum score per hour:

| Hr | Task | +pts |
|----|------|------|
| 1-2 | Create `Button` component, replace all buttons on 3 most-visited pages | +3 |
| 3-4 | Create `EmptyState` + `ErrorState` components, fix Challan + First Aid | +4 |
| 5-6 | Create `LoadingSkeleton` component, fix First Aid + Report white flash | +6 |
| 7-8 | Light mode pass on SOS page + tracking page | +3 |
| 9-10 | Error retry buttons on Challan + Command Center silent failures | +4 |
| 11-12 | SuggestedInquiries on ChatInterface + tracking help tooltip | +3 |
| 13-14 | Add `loading.tsx` for all pages + route transition bar | +2 |
| 15-16 | Microcopy audit: replace tactical jargon with plain language | +2 |
| 17-18 | Keyboard nav + screen reader labels on remaining pages | +3 |
| 19-20 | Mobile touch target sweep + safe-area audit | +3 |
| 21-22 | GSAP gap fill: missing page entry animations | +2 |
| 23-24 | Empty state copy pass + first-use tooltips | +2 |
| **Total** | **24 hours** | **+37pts → 105** |

After 24 hours: UX would be ~87/100. Remaining hours polish to 95+.

---

## Do Not Touch (Current State Is Already 95+ Worthy)

The following are genuinely enterprise-grade and should not be changed:
- **Offline architecture**: IndexedDB queues, Background Sync, service worker, offline fallback
- **GSAP animation system**: centralized registration, `useGSAP` exclusive usage, route change cleanup, reduced-motion handling
- **Theme switching**: flash-free inline script, CSS variable system, GSAP transition, system preference support
- **QR Emergency Card**: real user data, focus trap, share, analytics, dynamic import
- **CommandPalette**: cmdk integration, GSAP animations, keyboard shortcut, accessible markup
- **Offline AI**: 3-tier fallback (Chrome built-in → Transformers.js → keyword), progress indicator, user consent
- **DuckDB-Wasm**: 3-tier offline challan fallback with CSV loading
- **MapLibre clustering**: GeoJSON cluster source, expansion zoom, heatmap, traffic layer
- **Crash detection**: real DeviceMotion API, iOS permission handling, real SOS dispatch
- **Offline/Online/ServerWarming banners**: all built, animated, accessible, globally wired

---

*Created: 2026-05-23 | Target: 95/100 UX | SafeVixAI Enterprise Frontend*
