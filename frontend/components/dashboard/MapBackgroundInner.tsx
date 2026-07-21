'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useMemo } from 'react';

import { MapLibreCanvas, MapLibreFacility, MapLibreIssue } from '@/components/maps/MapLibreCanvas';
import { formatLocationSubtitle, isApproximateLocation } from '@/lib/location-utils';
import { FALLBACK_MAP_CENTER, FALLBACK_MAP_ZOOM, LIVE_MAP_ZOOM } from '@/lib/map-defaults';
import { useShallow } from 'zustand/react/shallow';
import { NearbyRoadIssue, NearbyService, useAppStore } from '@/lib/store';

function formatDistance(meters: number) {
  return meters >= 1000 ? `${(meters / 1000).toFixed(1)} km` : `${Math.round(meters)} m`;
}

function serviceIcon(category: NearbyService['category']) {
  switch (category) {
    case 'hospital':
      return 'local_hospital';
    case 'police':
      return 'local_police';
    case 'ambulance':
      return 'emergency';
    case 'fire':
      return 'local_fire_department';
    case 'pharmacy':
      return 'medication';
    case 'puncture':
      return 'tire_repair';
    case 'showroom':
      return 'directions_car';
    case 'towing':
    default:
      return 'tow';
  }
}

function serviceColor(category: NearbyService['category']) {
  switch (category) {
    case 'hospital':
      return '#e11d48'; // var(--emergency)
    case 'police':
      return '#3b82f6'; // var(--brand)
    case 'ambulance':
      return '#10b981'; // var(--text-green)
    case 'fire':
      return '#f59e0b'; // var(--text-amber)
    case 'pharmacy':
      return '#06b6d4'; // cyan
    case 'puncture':
      return '#8b5cf6'; // purple
    case 'showroom':
      return '#64748b'; // var(--text-3)
    case 'towing':
    default:
      return '#f59e0b'; // var(--text-amber)
  }
}

function issueColor(issue: NearbyRoadIssue) {
  if (issue.severity >= 4) {
    return '#e11d48'; // var(--emergency)
  }

  const normalizedType = issue.issueType.toLowerCase();
  if (normalizedType.includes('flood') || normalizedType.includes('rain')) {
    return '#3b82f6'; // var(--brand)
  }
  if (normalizedType.includes('traffic') || normalizedType.includes('accident')) {
    return '#f59e0b'; // var(--text-amber)
  }
  return '#f59e0b'; // var(--text-amber)
}

function issueIcon(issue: NearbyRoadIssue) {
  if (issue.severity >= 4) {
    return 'warning';
  }

  const normalizedType = issue.issueType.toLowerCase();
  if (normalizedType.includes('flood') || normalizedType.includes('rain')) {
    return 'rainy';
  }
  if (normalizedType.includes('traffic') || normalizedType.includes('accident')) {
    return 'traffic';
  }
  return 'report_problem';
}

export default function MapBackgroundInner() {
  const { gpsLocation, mapSearchTarget, nearbyRoadIssues, nearbyServices } = useAppStore(useShallow((state) => ({
    gpsLocation: state.gpsLocation,
    mapSearchTarget: state.mapSearchTarget,
    nearbyServices: state.nearbyServices,
    nearbyRoadIssues: state.nearbyRoadIssues,
  })));

  const searchLat = mapSearchTarget?.lat;
  const searchLon = mapSearchTarget?.lon;
  const gpsLat = gpsLocation?.lat;
  const gpsLon = gpsLocation?.lon;

  const center = useMemo<[number, number]>(
    () => {
      if (searchLat != null && searchLon != null) return [searchLat, searchLon];
      if (gpsLat != null && gpsLon != null) return [gpsLat, gpsLon];
      return FALLBACK_MAP_CENTER;
    },
    [searchLat, searchLon, gpsLat, gpsLon]
  );
  
  const approximateLocation = isApproximateLocation(gpsLocation);

  const facilities = useMemo<MapLibreFacility[]>(
    () =>
      nearbyServices.map((service) => ({
        id: service.id,
        name: service.name,
        coords: [service.lat, service.lon],
        type: service.category,
        accentColor: serviceColor(service.category),
        distance: formatDistance(service.distance),
        address: service.address,
        phone: service.phone,
        icon: serviceIcon(service.category),
      })),
    [nearbyServices]
  );

  const issues = useMemo<MapLibreIssue[]>(
    () =>
      nearbyRoadIssues.map((issue) => ({
        id: issue.uuid,
        label: issue.issueType,
        coords: [issue.lat, issue.lon],
        accentColor: issueColor(issue),
        icon: issueIcon(issue),
        overline: `Severity ${issue.severity} - ${formatDistance(issue.distance)}`,
        description: issue.description,
        status: issue.status.replaceAll('_', ' '),
        roadName: issue.roadName,
        severity: issue.severity,
      })),
    [nearbyRoadIssues]
  );

  return (
    <div className="absolute inset-0 z-0 h-full min-h-full w-full overflow-hidden">
      <MapLibreCanvas
        center={center}
        zoom={gpsLocation || mapSearchTarget ? LIVE_MAP_ZOOM : FALLBACK_MAP_ZOOM}
        facilities={facilities}
        issues={issues}
        currentLocation={
          gpsLocation
            ? {
                lat: gpsLocation.lat,
                lon: gpsLocation.lon,
                accuracy: gpsLocation.accuracy,
                title: 'Current location',
                subtitle: formatLocationSubtitle(gpsLocation),
              }
            : null
        }
        viewportMode="center"
        navigationPosition="bottom-left"
      />
      {mapSearchTarget ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-24 z-20 flex justify-center px-4">
          <div className="rounded-full border border-brand-light/30 bg-surface-1/80 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-text-1 backdrop-blur-xl">
            Search area - {mapSearchTarget.label}
          </div>
        </div>
      ) : !gpsLocation ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-24 z-20 flex justify-center px-4">
          <div className="rounded-full border border-white/20 bg-surface-1/80 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-white/85 backdrop-blur-xl">
            Allow location to find hospitals near you
          </div>
        </div>
      ) : approximateLocation ? (
        <div className="pointer-events-none absolute inset-x-0 bottom-24 z-20 flex justify-center px-4">
          <div className="rounded-full border border-warning/30 bg-surface-1/80 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-warning backdrop-blur-xl">
            Approximate device location · move outdoors or enable precise GPS
          </div>
        </div>
      ) : null}
    </div>
  );
}