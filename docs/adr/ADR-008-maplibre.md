# ADR-008: MapLibre GL over Google Maps / Leaflet

**Date:** 2026-05-25
**Status:** ✅ Accepted
**Author:** SafeVixAI Frontend Team

## Context

The app needs interactive maps for:
- Emergency service locations (hospitals, police, fire stations)
- Road issue visualization (potholes, damaged roads)
- Officer route optimization and dispatch
- GPS tracking display

Cost, offline capability, and customization were primary concerns.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **MapLibre GL (chosen)** | Open-source WebGL map library | Free, no API key, GL styling, vector tiles | Needs tile server (free options available) |
| **Google Maps** | Proprietary Google API | Excellent docs, street view | ₹ cost, API key required, attribution requirements |
| **Leaflet** | Lightweight open-source tiles | Simple, well-known | Raster-only, no 3D, less performant at scale |
| **Mapbox** | MapLibre's proprietary sibling | Great styles, easy setup | Cost after free tier |

## Decision

Use MapLibre GL JS 5.x with:
- Free basemap tiles from CartoDB / OpenFreeMap
- Dynamic import with `{ssr: false}` for Next.js compatibility
- Components: `MapCore`, `MapLayers`, `MapMarkers`, `MapRouting`, `MapLibreCanvas`
- Custom markers via `MapLibreMarker` (not Leaflet — legacy references exist in docs only)

## Consequences

- Zero map API costs at any scale
- Full GL styling (custom layers, heatmaps, 3D buildings)
- Offline tile caching possible via service worker
- Three.js globe on landing page uses separate rendering (not MapLibre)
