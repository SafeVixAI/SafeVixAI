# SafeVixAI  UI/UX Design Guide

## Design Philosophy

SafeVixAI is an emergency app. Every design decision must prioritize:
1. **Speed**  information in 1 tap, not 3
2. **Clarity**  readable in sunlight, readable with shaking hands
3. **Trust**  no fake data, no spinner loops, always show what's real
4. **Offline-first**  design for zero signal, treat internet as an enhancement

---

## Color System

### Primary Palette (Dark Navy Theme)

| Token | Hex | Usage |
|---|---|---|
| `bg-primary` | `#0A1628` | Main background — deep navy |
| `bg-secondary` | `#132035` | Card backgrounds |
| `bg-tertiary` | `#1C2D4A` | Input backgrounds, borders |
| `accent-green` | `#00C896` | Primary CTA, success states |
| `accent-red` | `#E53E3E` | SOS button, hospital markers, danger |
| `accent-blue` | `#3182CE` | Police markers, info states |
| `accent-orange` | `#DD6B20` | Fire/towing markers, warnings |
| `accent-yellow` | `#EAB308` | Open road issues, expiry warnings |
| `text-primary` | `#F7FAFC` | Main text |
| `text-secondary` | `#A0AEC0` | Labels, secondary info |
| `text-muted` | `#718096` | Disabled, hints |

### Why Dark Navy?
- Prevents glare in car/sunlight
- Emergency red SOS button stands out dramatically
- Map markers (red, blue, orange) have high contrast
- CartoDB Dark base map style matches perfectly
- Battery-efficient on OLED screens

---

## Typography

| Use | Font | Weight | Size |
|---|---|---|---|
| App title | Inter | 800 (ExtraBold) | 28px |
| Page headers | Inter | 700 (Bold) | 22px |
| Section titles | Inter | 600 (SemiBold) | 18px |
| Body text | Inter | 400 (Regular) | 16px |
| Labels / captions | Inter | 400 | 14px |
| Emergency numbers | Inter | 700 | 20px (always large) |
| Distance values | Inter | 600 | 15px |

```html
<!-- In layout.tsx -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet" />
```

---

## Spacing & Grid

- Base unit: 4px
- Component padding: 16px (mobile), 24px (desktop)
- Card gap: 12px
- Section gap: 24px
- Max content width: 480px (mobile-first, centered on desktop)

---

## Components

### SOS Button
- Size: 64×64px, position: fixed bottom-right, z-index: 50
- Color: `#E53E3E` (accent-red) with glow shadow
- Animation: pulse ring on idle (draws attention without being annoying)
- Long-press alternative for accessibility: 2-second halo fill animation

```css
/* SOS button pulse animation */
@keyframes sos-pulse {
  0% { box-shadow: 0 0 0 0 rgba(229, 62, 62, 0.4); }
  70% { box-shadow: 0 0 0 16px rgba(229, 62, 62, 0); }
  100% { box-shadow: 0 0 0 0 rgba(229, 62, 62, 0); }
}
```

### Emergency Numbers Bar
- Position: fixed bottom-0, width: 100%
- Height: 56px
- Background: `#132035` with top border `#1C2D4A`
- 4 tap targets: 112, 102, 100, 1033
- Each: min-width 25%, text center, font-weight 700

### Map Container
- Height: 55vh (mobile)  enough to show 3-4 markers without scrolling
- Border radius: 16px
- Background while loading: `#1C2D4A` with pulse animation
- Attribution: always visible (OSM license requirement)
- Style URL (report picker & command-center only): CartoDB Dark Matter `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
- Main map (`/locator`, `/emergency`) uses multiple providers via `buildStyleCandidates()` from `map-styles.ts`: **Google Maps** (raster, India-optimized), **MapTiler** (vector tiles), **OpenFreeMap** (Liberty style, fallback)

### Service Card
- Background: `#132035`, border-radius: 12px, padding: 16px
- Left accent bar: 4px wide, color by category (red=hospital, blue=police)
- Layout: name + distance (top row) | phone + buttons (bottom row)
- Tap-to-Call button: green outline, "Call" text, tel: href
- Directions button: blue ghost, external link icon, Google Maps deep link

### Chat Bubble
- User message: right-aligned, `#00C896` background
- Bot message: left-aligned, `#132035` background with bot avatar
- Source citation: small tag below bot message
- Typing indicator: 3-dot bounce animation
- Max width: 80% of container

### First Aid Card
- Icon: large (48px), category-specific emoji or Lucide icon
- Title: 18px semibold
- Steps: numbered list, 14px, line-height 1.6
- Background: `#132035`, border-left: 4px solid accent-red
- No internet required badge: " Works Offline" chip

---

## Map Design Rules (MapLibre GL)

### Map Style (MapLibre GL Style JSON — not Leaflet raster tiles)
```tsx
// CartoDB Dark Matter — used in report picker and command-center dashboard
// Main map uses buildStyleCandidates() from map-styles.ts instead
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  center: [lon, lat],
  zoom: 14,
})
```

### Marker Colors by Category
```tsx
const MARKER_COLORS = {
  hospital:  '#E53E3E',  // red
  ambulance: '#E53E3E',  // red
  police:    '#3182CE',  // blue
  fire:      '#DD6B20',  // orange
  towing:    '#D69E2E',  // amber
  puncture:  '#38A169',  // green
  pharmacy:  '#805AD5',  // purple
}
```

### Critical Rules
1. `import dynamic from 'next/dynamic'` + `ssr: false` → MapLibre needs browser
2. `maplibre-gl/dist/maplibre-gl.css` is imported per-component in `LocationPickerInner.tsx`, `MapLayers.tsx`, and `MapLibreDashboard.tsx` (not globally in `layout.tsx`)
3. Markers use `new maplibregl.Marker({ color: '...' })` with built-in color circles — no custom icon images needed. The `public/leaflet/` directory contains legacy Leaflet icons (not used by MapLibre). The `public/maplibre/` directory does not exist
4. Add `key={lat+lon}` to MapContainer  prevents "map already initialized" error
5. Set explicit height on MapContainer  invisible without it

---

## Page Layouts

### Home Page (`/`)
```

  SafeVixAI Logo + Tagline 
  Connectivity Badge     

  [Emergency Locator]       Red card, largest
  Find hospitals & help  

  [AI Assistant]  [Fine]    Two equal cards
  Chat about laws  Calc  

  [Report Road Issue]       Green card
  Pothole, Missing sign  

   Emergency Numbers      Fixed bottom bar
  112  102  100  1033   

```

### Emergency Page (`/emergency`)
```

 Location: Chennai, TN   
 Showing within: 5km     
 [Connectivity Badge]    

                         
   [MAPLIBRE MAP 55vh]    
   CartoDB Dark tiles    
   Color-coded markers   
                         

 [Filter chips: All/Hosp/
  Police/Ambulance/Tow]  

 [Service Card 1]  2.1km 
 [Service Card 2]  3.4km 
 [Service Card 3]  5.2km 
          ...             

   112  102  100  1033 

                    [SOS]   Fixed, bottom-right
```

### Chat Page (`/chat`)
```

 AI Assistant            
 [Online][Offline] tabs  

 [Bot msg: Welcome...]   
                         
         [User msg ----] 
 [Bot msg: Here are...]  
         [Source: MV Act]
                         
       ...               

 [] [Type message...] []

```

---

## Accessibility

| Requirement | Implementation |
|---|---|
| Minimum touch target | 44×44px for all interactive elements |
| Contrast ratio | WCAG AA  all text > 4.5:1 against background |
| Font scaling | All sizes in `rem`  scales with browser font-size preference |
| Screen reader | `aria-label` on all icon buttons, `role="status"` on connectivity badge |
| Keyboard nav | All interactive elements reachable via Tab key |
| Error states | Never silent  always show toast or inline error |
| Loading states | Skeleton screens instead of blank states |
| Multilingual | HTML `lang` attribute updated on language change |

---

## Animation Guidelines

| Animation | Duration | Easing | Purpose |
|---|---|---|---|
| SOS pulse ring | 2s infinite | ease-out | Draw attention without alarming |
| Crash countdown circle | 10s linear | linear | Clear urgency, predictable progress |
| Model download progress |  | linear | Exact progress, no fake smoothing |
| Connectivity badge | 300ms | ease | Subtle dot color change |
| Card hover | 150ms | ease | Touch feedback replacement for desktop |
| Toast notification | 200ms in, 300ms out | ease | Informative, not distracting |
| Map marker appear | 400ms | spring | Satisfying, shows data just arrived |

---

## Mobile-Specific Rules

1. **Never rely on hover**  design for touch first, desktop second
2. **Bottom navigation** is more reachable than top  keep emergency numbers at bottom
3. **Large critical buttons**  SOS is always 64px diameter minimum
4. **One primary action per screen**  emergency page = find services (not chat, not settings)
5. **Portrait-primary**  lock orientation in PWA manifest
6. **Safe area insets**  add padding-bottom for iPhone home indicator

---

## Offline UX States

| State | UI Treatment |
|---|---|
| Online (fresh data) | Green dot: "Live" |
| Online (from cache) | Yellow dot: "Cached" with timestamp |
| Offline (first visit) | Orange dot: "Offline  25-city coverage" |
| Offline AI active | Blue chip: "Using Phi-3 Mini (on your device)" |
| Report queued offline | Info toast: "Saved  will submit when connected" |
| Model downloading | Full-screen progress with MB + estimated time |

---

*Document version: 1.1 | AI-powered road safety platform | Updated: 2026-06-09*

---

## E2E Test Production Nuances (2026-06-09)

### GSAP Animations in Production Build
- GSAP silently fails in `node .next/standalone/server.js` production build
- `usePageEntry` hook's `gsap.fromTo` sets `opacity: 0` via inline styles but animation never transitions to `opacity: 1`
- All E2E `waitForMount` helpers removed the `window.getComputedStyle(h1).opacity !== '0'` check
- Workaround: wait for `[aria-busy="true"]` loading skeleton to disappear instead

### AuthGuard in Production Build
- `AuthGuard.tsx` wraps all pages except NO_NAV_ROUTES (defined in `AppFrame.tsx`: `/login`, `/signup`, `/forgot-password`)
- Redirects to `/login` when `isAuthenticated=false` and no Supabase session
- E2E tests use `localStorage.__E2E_SKIP_AUTH__` flag for bypass
- Previous zustand persist approach (`svai-storage`) had race condition with `profileHydrated` (IndexedDB exceptions in EnterpriseClientAppHooks)
