// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useTheme } from '@/components/ThemeProvider';
import { useAppStore } from '@/lib/store';
import { useMapInstance } from '@/hooks/useMapInstance';
import { MapCore } from './MapCore';
import { MapMarkers } from './MapMarkers';
import { MapLayers } from './MapLayers';
import { MapRouting } from './MapRouting';
import type { MapLibreCanvasProps } from './map-types';

// ── Re-export types for backward compatibility ──
export type {
  MapLibreFacility,
  MapLibreIssue,
  MapLibreCurrentLocation,
  MapLibreRoutePoint,
  MapLibreRoute,
} from './map-types';

export function MapLibreCanvas({
  center,
  zoom = Number(process.env.NEXT_PUBLIC_MAP_DEFAULT_ZOOM ?? 13),
  facilities = [],
  issues = [],
  currentLocation,
  route = null,
  alternativeRoutes = [],
  selectedFacilityId = null,
  viewportMode = 'center',
  navigationPosition = 'bottom-left',
  className = 'absolute inset-0 h-full w-full',
}: MapLibreCanvasProps) {
  const showTraffic = useAppStore((state) => state.showTraffic);
  const showSatellite = useAppStore((state) => state.showSatellite);
  const { resolvedTheme } = useTheme();

  const { map, mapNodeRef, status, statusMessage, styleRevision } = useMapInstance({
    center,
    zoom,
    resolvedTheme,
    showSatellite,
    showTraffic,
    navigationPosition,
  });

  return (
    <div className={className}>
      <MapCore mapNodeRef={mapNodeRef} status={status} statusMessage={statusMessage} />
      {map && (
        <>
          <MapMarkers
            map={map}
            currentLocation={currentLocation}
            issues={issues}
            selectedFacilityId={selectedFacilityId}
            facilities={facilities}
            styleRevision={styleRevision}
          />
          <MapLayers
            map={map}
            currentLocation={currentLocation}
            facilities={facilities}
            issues={issues}
            selectedFacilityId={selectedFacilityId}
            styleRevision={styleRevision}
          />
          <MapRouting
            map={map}
            route={route}
            alternativeRoutes={alternativeRoutes}
            styleRevision={styleRevision}
            viewportMode={viewportMode}
            center={center}
            zoom={zoom}
            currentLocation={currentLocation}
            facilities={facilities}
            issues={issues}
          />
        </>
      )}
    </div>
  );
}
