'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';

import type { MapInnerProps } from '@/components/EmergencyMapInner';
import type { MapLibreCurrentLocation, MapLibreRoute } from '@/components/maps/MapLibreCanvas';

// Load the browser-only map renderer dynamically so SSR stays stable.
const EmergencyMapInner = dynamic<MapInnerProps>(
  () => import('@/components/EmergencyMapInner'),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full relative isolate rounded-lg overflow-hidden border border-[var(--border)] bg-[var(--surface-1)] flex flex-col items-center justify-center gap-3">
        <Loader2 size={24} className="animate-spin text-[var(--brand)] opacity-50" />
        <span className="text-xs font-bold uppercase tracking-widest text-[var(--text-2)]">
          Initializing Map Subsystem...
        </span>
      </div>
    ),
  }
);

export function EmergencyMap({
  center,
  facilities,
  route = null,
  alternativeRoutes = [],
  currentLocation = null,
  selectedFacilityId = null,
}: {
  center: [number, number];
  facilities: Array<{
    id: string;
    name: string;
    type: string;
    coords: [number, number] | null;
    accentColor: string;
    distance: string;
  }>;
  route?: MapLibreRoute | null;
  alternativeRoutes?: MapLibreRoute[];
  currentLocation?: MapLibreCurrentLocation | null;
  selectedFacilityId?: string | null;
}) {
  return (
    <EmergencyMapInner
      center={center}
      facilities={facilities}
      route={route}
      alternativeRoutes={alternativeRoutes}
      currentLocation={currentLocation}
      selectedFacilityId={selectedFacilityId}
    />
  );
}