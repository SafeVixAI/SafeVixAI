'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import type { MapLibreCurrentLocation, MapLibreIssue, MapLibreFacility } from './map-types';
import { buildMarkerElement, buildPopupContent, iconForType } from './map-utils';

interface MapMarkersProps {
  map: maplibregl.Map;
  currentLocation?: MapLibreCurrentLocation | null;
  issues?: MapLibreIssue[];
  selectedFacilityId?: string | null;
  facilities?: MapLibreFacility[];
  styleRevision: number;
}

export function MapMarkers({
  map,
  currentLocation,
  issues = [],
  selectedFacilityId,
  facilities = [],
  styleRevision,
}: MapMarkersProps) {
  const markerRefs = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    // Clean up old markers
    markerRefs.current.forEach((marker) => marker.remove());
    markerRefs.current = [];

    // Current location marker
    if (currentLocation) {
      const popup = new maplibregl.Popup({ offset: 18 }).setDOMContent(
        buildPopupContent(
          currentLocation.title ?? 'Current location',
          currentLocation.subtitle,
          currentLocation.accuracy ? [`Accuracy: ${Math.round(currentLocation.accuracy)} m`] : []
        )
      );

      const markerEl = buildMarkerElement({ color: '#00c896', icon: 'my_location', kind: 'current' });
      markerEl.setAttribute('aria-label', `Your location: ${currentLocation.title ?? 'Current position'}`);
      markerEl.setAttribute('role', 'img');
      const markerInstance = new maplibregl.Marker({
        element: markerEl,
        anchor: 'center',
      })
        .setLngLat([currentLocation.lon, currentLocation.lat])
        .setPopup(popup)
        .addTo(map);

      markerRefs.current.push(markerInstance);
    }

    // Issues markers
    issues.forEach((issue) => {
      const [lat, lon] = issue.coords;
      const popup = new maplibregl.Popup({ offset: 22 }).setDOMContent(
        buildPopupContent(
          issue.label,
          issue.overline,
          [issue.roadName, issue.description, issue.status ? `Status: ${issue.status}` : undefined].filter(Boolean) as string[]
        )
      );

      const markerEl = buildMarkerElement({ color: issue.accentColor, icon: issue.icon ?? 'warning', kind: 'issue' });
      markerEl.setAttribute('aria-label', `Road issue: ${issue.label}. ${issue.description ?? ''}`);
      markerEl.setAttribute('role', 'img');
      const markerInstance = new maplibregl.Marker({
        element: markerEl,
        anchor: 'center',
      })
        .setLngLat([lon, lat])
        .setPopup(popup)
        .addTo(map);

      markerRefs.current.push(markerInstance);
    });

    // Selected facility marker
    if (selectedFacilityId) {
      const liveFacilities = facilities.filter((f) => f.coords);
      const selected = liveFacilities.find((f) => f.id === selectedFacilityId);
      if (selected && selected.coords) {
        const markerEl = buildMarkerElement({
          color: selected.accentColor,
          icon: selected.icon || iconForType(selected.type),
          kind: 'standard',
          selected: true,
        });
        markerEl.setAttribute('aria-label', `Emergency facility: ${selected.name ?? selected.type}`);
        markerEl.setAttribute('role', 'img');

        const markerInstance = new maplibregl.Marker({
          element: markerEl,
          anchor: 'center',
        })
          .setLngLat([selected.coords[1], selected.coords[0]])
          .addTo(map);

        markerRefs.current.push(markerInstance);
      }
    }

    return () => {
      markerRefs.current.forEach((marker) => marker.remove());
      markerRefs.current = [];
    };
  }, [map, currentLocation, issues, selectedFacilityId, facilities, styleRevision]);

  // Fly-to listener
  useEffect(() => {
    const handleFlyTo = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.detail && map) {
        map.flyTo({
          center: [customEvent.detail.lng, customEvent.detail.lat],
          zoom: 16,
          essential: true,
        });
      }
    };
    window.addEventListener('svai:fly-to', handleFlyTo);
    return () => window.removeEventListener('svai:fly-to', handleFlyTo);
  }, [map]);

  return null;
}