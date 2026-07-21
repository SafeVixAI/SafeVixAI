'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { memo, useMemo } from 'react';

import {
  MapLibreCanvas,
  MapLibreCurrentLocation,
  MapLibreFacility,
  MapLibreRoute,
} from '@/components/maps/MapLibreCanvas';

function iconForType(type: string) {
  const normalized = type.toLowerCase();
  if (normalized.includes('hospital')) return 'local_hospital';
  if (normalized.includes('ambulance')) return 'emergency';
  if (normalized.includes('pharmacy')) return 'medication';
  if (normalized.includes('police')) return 'local_police';
  if (normalized.includes('fire')) return 'local_fire_department';
  if (normalized.includes('tow')) return 'tow';
  if (normalized.includes('mechanic')) return 'build';
  return 'place';
}

interface Facility {
  id: string;
  name: string;
  type: string;
  coords: [number, number] | null;
  accentColor: string;
  distance: string;
  address?: string;
  phone?: string;
}

export interface MapInnerProps {
  center: [number, number];
  facilities: Facility[];
  route?: MapLibreRoute | null;
  alternativeRoutes?: MapLibreRoute[];
  currentLocation?: MapLibreCurrentLocation | null;
  selectedFacilityId?: string | null;
}

const EmergencyMapInner = memo(function EmergencyMapInner({
  center,
  facilities,
  route = null,
  alternativeRoutes = [],
  currentLocation = null,
  selectedFacilityId = null,
}: MapInnerProps) {
  const mapFacilities = useMemo<MapLibreFacility[]>(
    () =>
      facilities.map((facility) => ({
        id: facility.id,
        name: facility.name,
        coords: facility.coords,
        type: facility.type,
        accentColor: facility.accentColor,
        distance: facility.distance,
        address: facility.address,
        phone: facility.phone,
        icon: iconForType(facility.type),
      })),
    [facilities]
  );

  return (
    <MapLibreCanvas
      center={center}
      zoom={14}
      facilities={mapFacilities}
      route={route}
      alternativeRoutes={alternativeRoutes}
      selectedFacilityId={selectedFacilityId}
      currentLocation={currentLocation}
      viewportMode="fit"
      navigationPosition="top-right"
      className="w-full h-full rounded-lg overflow-hidden"
    />
  );
})

export default EmergencyMapInner