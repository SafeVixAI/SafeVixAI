'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import type { MapLibreCurrentLocation, MapLibreFacility, MapLibreIssue, MapLibreRoute } from './map-types';
import {
  ROUTE_SOURCE_ID,
  ROUTE_LINE_LAYER_ID,
  ROUTE_CASING_LAYER_ID,
  ROUTE_ALT_LINE_LAYER_ID,
  ROUTE_ALT_CASING_LAYER_ID,
} from './map-utils';

interface MapRoutingProps {
  map: maplibregl.Map;
  route?: MapLibreRoute | null;
  alternativeRoutes?: MapLibreRoute[];
  styleRevision: number;
  viewportMode?: 'center' | 'fit';
  center: [number, number];
  zoom: number;
  currentLocation?: MapLibreCurrentLocation | null;
  facilities?: MapLibreFacility[];
  issues?: MapLibreIssue[];
}

export function MapRouting({
  map,
  route = null,
  alternativeRoutes = [],
  styleRevision,
  viewportMode = 'center',
  center,
  zoom,
  currentLocation,
  facilities = [],
  issues = [],
}: MapRoutingProps) {
  const liveFacilities = facilities.filter((f) => f.coords);

  // 1. Sync Route Overlay
  useEffect(() => {
    const syncRouteOverlay = () => {
      const hasSource = Boolean(map.getSource(ROUTE_SOURCE_ID));

      const alternativeFeatures = alternativeRoutes
        .filter((candidate) => candidate.path?.length && candidate.path.length >= 2)
        .map((candidate) => ({
          type: 'Feature',
          properties: { kind: 'alternative', routeId: candidate.routeId ?? '' },
          geometry: {
            type: 'LineString',
            coordinates: candidate.path.map((point) => [point.lon, point.lat]),
          },
        }));

      if (!route?.path?.length || route.path.length < 2) {
        if (map.getLayer(ROUTE_LINE_LAYER_ID)) map.removeLayer(ROUTE_LINE_LAYER_ID);
        if (map.getLayer(ROUTE_CASING_LAYER_ID)) map.removeLayer(ROUTE_CASING_LAYER_ID);
        if (map.getLayer(ROUTE_ALT_LINE_LAYER_ID)) map.removeLayer(ROUTE_ALT_LINE_LAYER_ID);
        if (map.getLayer(ROUTE_ALT_CASING_LAYER_ID)) map.removeLayer(ROUTE_ALT_CASING_LAYER_ID);
        if (hasSource) map.removeSource(ROUTE_SOURCE_ID);
        return;
      }

      const routeFeatures = [
        ...alternativeFeatures,
        {
          type: 'Feature',
          properties: { kind: 'primary', routeId: route.routeId ?? '' },
          geometry: {
            type: 'LineString',
            coordinates: route.path.map((point) => [point.lon, point.lat]),
          },
        },
      ] as GeoJSON.Feature<GeoJSON.LineString>[];

      const routeCollection = {
        type: 'FeatureCollection',
        features: routeFeatures,
      } as GeoJSON.FeatureCollection<GeoJSON.LineString>;

      if (hasSource) {
        const source = map.getSource(ROUTE_SOURCE_ID) as maplibregl.GeoJSONSource;
        source.setData(routeCollection);
        return;
      }

      map.addSource(ROUTE_SOURCE_ID, { type: 'geojson', data: routeCollection });
      if (!map.getLayer(ROUTE_ALT_CASING_LAYER_ID)) {
        map.addLayer({
          id: ROUTE_ALT_CASING_LAYER_ID,
          type: 'line',
          source: ROUTE_SOURCE_ID,
          filter: ['==', ['get', 'kind'], 'alternative'],
          layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': 'rgba(255,255,255,0.7)', 'line-width': 7, 'line-opacity': 0.75 },
        });
      }
      if (!map.getLayer(ROUTE_ALT_LINE_LAYER_ID)) {
        map.addLayer({
          id: ROUTE_ALT_LINE_LAYER_ID,
          type: 'line',
          source: ROUTE_SOURCE_ID,
          filter: ['==', ['get', 'kind'], 'alternative'],
          layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: {
            'line-color': '#00c896',
            'line-width': 4,
            'line-opacity': 0.45,
            'line-dasharray': [1, 1.4],
          },
        });
      }
      if (!map.getLayer(ROUTE_CASING_LAYER_ID)) {
        map.addLayer({
          id: ROUTE_CASING_LAYER_ID,
          type: 'line',
          source: ROUTE_SOURCE_ID,
          filter: ['==', ['get', 'kind'], 'primary'],
          layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': 'rgba(255,255,255,0.92)', 'line-width': 10, 'line-opacity': 0.96 },
        });
      }
      if (!map.getLayer(ROUTE_LINE_LAYER_ID)) {
        map.addLayer({
          id: ROUTE_LINE_LAYER_ID,
          type: 'line',
          source: ROUTE_SOURCE_ID,
          filter: ['==', ['get', 'kind'], 'primary'],
          layout: { 'line-cap': 'round', 'line-join': 'round' },
          paint: { 'line-color': '#2563eb', 'line-width': 6, 'line-opacity': 0.98 },
        });
      }
    };

    if (map.isStyleLoaded()) {
      syncRouteOverlay();
    } else {
      map.once('load', syncRouteOverlay);
    }
  }, [map, alternativeRoutes, route, styleRevision]);

  // 2. Viewport Management
  useEffect(() => {
    const allPoints: Array<[number, number]> = [];

    if (currentLocation) allPoints.push([currentLocation.lon, currentLocation.lat]);
    liveFacilities.forEach((facility) => {
      if (facility.coords) allPoints.push([facility.coords[1], facility.coords[0]]);
    });
    issues.forEach((issue) => {
      allPoints.push([issue.coords[1], issue.coords[0]]);
    });
    if (route?.path?.length) {
      route.path.forEach((point) => {
        allPoints.push([point.lon, point.lat]);
      });
    }
    alternativeRoutes.forEach((candidate) => {
      candidate.path.forEach((point) => {
        allPoints.push([point.lon, point.lat]);
      });
    });

    if ((viewportMode === 'fit' || route?.path?.length) && allPoints.length > 1) {
      const bounds = allPoints.reduce(
        (acc, point) => acc.extend(point),
        new maplibregl.LngLatBounds(allPoints[0], allPoints[0])
      );
      map.fitBounds(bounds, {
        padding: { top: 72, right: 56, bottom: 72, left: 56 },
        duration: 900,
        maxZoom: 15.5,
      });
      return;
    }

    map.easeTo({ center: [center[1], center[0]], zoom, duration: 850, essential: true });
  }, [
    map,
    alternativeRoutes,
    center,
    currentLocation,
    issues,
    liveFacilities,
    route,
    styleRevision,
    viewportMode,
    zoom,
  ]);

  return null;
}