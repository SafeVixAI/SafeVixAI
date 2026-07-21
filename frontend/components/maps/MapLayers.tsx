'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useAppStore } from '@/lib/store';
import { addTrafficLayer, toggleTrafficLayer } from '@/lib/traffic-layer';
import { addSafeSpacesLayer } from '@/lib/safe-spaces-layer';
import { logClientError } from '@/lib/client-logger';
import type { MapLibreCurrentLocation, MapLibreFacility, MapLibreIssue } from './map-types';
import {
  ACCURACY_SOURCE_ID,
  ACCURACY_FILL_LAYER_ID,
  ACCURACY_LINE_LAYER_ID,
  FACILITY_SOURCE_ID,
  FACILITY_CLUSTER_LAYER_ID,
  FACILITY_CLUSTER_COUNT_LAYER_ID,
  FACILITY_UNCLUSTERED_LAYER_ID,
  FACILITY_SELECTED_LAYER_ID,
  HEATMAP_SOURCE_ID,
  HEATMAP_LAYER_ID,
  buildAccuracyFeature,
  buildFacilityCollection,
  buildPopupContent,
} from './map-utils';

interface MapLayersProps {
  map: maplibregl.Map;
  currentLocation?: MapLibreCurrentLocation | null;
  facilities?: MapLibreFacility[];
  issues?: MapLibreIssue[];
  selectedFacilityId?: string | null;
  styleRevision: number;
}

export function MapLayers({
  map,
  currentLocation,
  facilities = [],
  issues = [],
  selectedFacilityId,
  styleRevision,
}: MapLayersProps) {
  const showTraffic = useAppStore((state) => state.showTraffic);
  const showSafeSpaces = useAppStore((state) => state.showSafeSpaces);
  const showHazardHeatmap = useAppStore((state) => state.showHazardHeatmap);

  const facilityPopupRef = useRef<maplibregl.Popup | null>(null);
  const liveFacilities = facilities.filter((f) => f.coords);

  // 1. Accuracy Overlay
  useEffect(() => {
    const syncAccuracyOverlay = () => {
      const hasSource = Boolean(map.getSource(ACCURACY_SOURCE_ID));

      if (!currentLocation?.accuracy) {
        if (map.getLayer(ACCURACY_FILL_LAYER_ID)) map.removeLayer(ACCURACY_FILL_LAYER_ID);
        if (map.getLayer(ACCURACY_LINE_LAYER_ID)) map.removeLayer(ACCURACY_LINE_LAYER_ID);
        if (hasSource) map.removeSource(ACCURACY_SOURCE_ID);
        return;
      }

      const circleFeature = buildAccuracyFeature(
        currentLocation.lat,
        currentLocation.lon,
        Math.max(currentLocation.accuracy, 35)
      );

      if (hasSource) {
        const source = map.getSource(ACCURACY_SOURCE_ID) as maplibregl.GeoJSONSource;
        source.setData(circleFeature);
        return;
      }

      map.addSource(ACCURACY_SOURCE_ID, { type: 'geojson', data: circleFeature });
      map.addLayer({
        id: ACCURACY_FILL_LAYER_ID,
        type: 'fill',
        source: ACCURACY_SOURCE_ID,
        paint: { 'fill-color': '#00c896', 'fill-opacity': 0.12 },
      });
      map.addLayer({
        id: ACCURACY_LINE_LAYER_ID,
        type: 'line',
        source: ACCURACY_SOURCE_ID,
        paint: { 'line-color': '#00c896', 'line-width': 2, 'line-opacity': 0.55 },
      });
    };

    if (map.isStyleLoaded()) {
      syncAccuracyOverlay();
    } else {
      map.once('load', syncAccuracyOverlay);
    }
  }, [map, currentLocation, styleRevision]);

  // 2. Heatmap Layer
  useEffect(() => {
    const syncHeatmapLayer = () => {
      const hasSource = Boolean(map.getSource(HEATMAP_SOURCE_ID));

      if (!showHazardHeatmap || issues.length === 0) {
        if (map.getLayer(HEATMAP_LAYER_ID)) map.removeLayer(HEATMAP_LAYER_ID);
        if (hasSource) map.removeSource(HEATMAP_SOURCE_ID);
        return;
      }

      const collection = {
        type: 'FeatureCollection',
        features: issues.map((issue) => ({
          type: 'Feature',
          properties: { severity: issue.severity || 1 },
          geometry: { type: 'Point', coordinates: [issue.coords[1], issue.coords[0]] },
        })),
      } as GeoJSON.FeatureCollection<GeoJSON.Point>;

      if (hasSource) {
        (map.getSource(HEATMAP_SOURCE_ID) as maplibregl.GeoJSONSource).setData(collection);
      } else {
        map.addSource(HEATMAP_SOURCE_ID, { type: 'geojson', data: collection });
      }

      if (!map.getLayer(HEATMAP_LAYER_ID)) {
        map.addLayer(
          {
            id: HEATMAP_LAYER_ID,
            type: 'heatmap',
            source: HEATMAP_SOURCE_ID,
            maxzoom: 15,
            paint: {
              'heatmap-weight': ['interpolate', ['linear'], ['get', 'severity'], 1, 0.2, 5, 1],
              'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 15, 3],
              'heatmap-color': [
                'interpolate',
                ['linear'],
                ['heatmap-density'],
                0,
                'rgba(0, 200, 150, 0)',
                0.2,
                '#00c896',
                0.5,
                '#00a87d',
                0.8,
                '#008a67',
              ],
              'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 2, 15, 20],
              'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 7, 1, 15, 0],
            },
          },
          FACILITY_UNCLUSTERED_LAYER_ID
        );
      }
    };

    if (map.isStyleLoaded()) {
      syncHeatmapLayer();
    } else {
      map.once('load', syncHeatmapLayer);
    }
  }, [map, showHazardHeatmap, issues, styleRevision]);

  // 3. Facility Layers (Clusters + Points) + Popups & Click Handlers
  useEffect(() => {
    const popup = facilityPopupRef.current ?? new maplibregl.Popup({ closeButton: false, offset: 22 });
    facilityPopupRef.current = popup;
    const collection = buildFacilityCollection(liveFacilities, selectedFacilityId ?? null);
    let handlersBound = false;

    const syncFacilityLayers = () => {
      const existingSource = map.getSource(FACILITY_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
      if (existingSource) {
        existingSource.setData(collection);
      } else {
        map.addSource(FACILITY_SOURCE_ID, {
          type: 'geojson',
          data: collection,
          cluster: true,
          clusterMaxZoom: 13,
          clusterRadius: 48,
        });
      }

      if (!map.getLayer(FACILITY_CLUSTER_LAYER_ID)) {
        map.addLayer({
          id: FACILITY_CLUSTER_LAYER_ID,
          type: 'circle',
          source: FACILITY_SOURCE_ID,
          filter: ['has', 'point_count'],
          paint: {
            'circle-color': ['step', ['get', 'point_count'], '#00c896', 8, '#00a87d', 16, '#008a67'],
            'circle-radius': ['step', ['get', 'point_count'], 18, 8, 22, 16, 28],
            'circle-opacity': 0.92,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 2,
          },
        });
      }

      if (!map.getLayer(FACILITY_CLUSTER_COUNT_LAYER_ID)) {
        map.addLayer({
          id: FACILITY_CLUSTER_COUNT_LAYER_ID,
          type: 'symbol',
          source: FACILITY_SOURCE_ID,
          filter: ['has', 'point_count'],
          layout: {
            'text-field': ['get', 'point_count_abbreviated'],
            'text-size': 12,
            'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
          },
          paint: { 'text-color': '#ffffff' },
        });
      }

      if (!map.getLayer(FACILITY_SELECTED_LAYER_ID)) {
        map.addLayer({
          id: FACILITY_SELECTED_LAYER_ID,
          type: 'circle',
          source: FACILITY_SOURCE_ID,
          filter: ['all', ['!', ['has', 'point_count']], ['==', ['get', 'selected'], 1]],
          paint: {
            'circle-color': ['get', 'accentColor'],
            'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 18, 14, 22],
            'circle-opacity': 0.28,
            'circle-stroke-width': 0,
          },
        });
      }

      if (!map.getLayer(FACILITY_UNCLUSTERED_LAYER_ID)) {
        map.addLayer({
          id: FACILITY_UNCLUSTERED_LAYER_ID,
          type: 'circle',
          source: FACILITY_SOURCE_ID,
          filter: ['!', ['has', 'point_count']],
          paint: {
            'circle-color': ['get', 'accentColor'],
            'circle-radius': ['interpolate', ['linear'], ['zoom'], 5, 7, 11, 9, 16, 11],
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 2,
            'circle-opacity': 0.95,
          },
        });
      }
    };

    const handleClusterClick = (event: maplibregl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      const clusterId = feature?.properties?.cluster_id;
      if (clusterId == null) return;

      const source = map.getSource(FACILITY_SOURCE_ID) as maplibregl.GeoJSONSource & {
        getClusterExpansionZoom: (_clusterId: number, _callback: (_error: Error | null, _zoom: number) => void) => void;
      };

      source.getClusterExpansionZoom(clusterId, (error, expansionZoom) => {
        if (error || !feature || feature.geometry.type !== 'Point') return;
        map.easeTo({
          center: feature.geometry.coordinates as [number, number],
          zoom: Math.max(expansionZoom, 14),
          duration: 650,
        });
      });
    };

    const handleFacilityClick = (event: maplibregl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (!feature || feature.geometry.type !== 'Point') return;

      const properties = feature.properties as Record<string, string>;
      popup
        .setLngLat(feature.geometry.coordinates as [number, number])
        .setDOMContent(
          buildPopupContent(
            properties.name ?? 'Emergency service',
            [properties.type, properties.distance].filter(Boolean).join(' - '),
            [properties.address, properties.phone ? `Call: ${properties.phone}` : undefined].filter(Boolean) as string[]
          )
        )
        .addTo(map);
    };

    const handlePointerEnter = () => {
      map.getCanvas().style.cursor = 'pointer';
    };
    const handlePointerLeave = () => {
      map.getCanvas().style.cursor = '';
    };

    const bindHandlers = () => {
      if (handlersBound) return;
      map.on('click', FACILITY_CLUSTER_LAYER_ID, handleClusterClick);
      map.on('click', FACILITY_UNCLUSTERED_LAYER_ID, handleFacilityClick);
      map.on('mouseenter', FACILITY_CLUSTER_LAYER_ID, handlePointerEnter);
      map.on('mouseenter', FACILITY_UNCLUSTERED_LAYER_ID, handlePointerEnter);
      map.on('mouseleave', FACILITY_CLUSTER_LAYER_ID, handlePointerLeave);
      map.on('mouseleave', FACILITY_UNCLUSTERED_LAYER_ID, handlePointerLeave);
      handlersBound = true;
    };

    const initializeFacilities = () => {
      syncFacilityLayers();
      bindHandlers();
    };

    if (map.isStyleLoaded()) {
      initializeFacilities();
    } else {
      map.once('load', initializeFacilities);
    }

    return () => {
      map.off('load', initializeFacilities);
      if (handlersBound) {
        map.off('click', FACILITY_CLUSTER_LAYER_ID, handleClusterClick);
        map.off('click', FACILITY_UNCLUSTERED_LAYER_ID, handleFacilityClick);
        map.off('mouseenter', FACILITY_CLUSTER_LAYER_ID, handlePointerEnter);
        map.off('mouseenter', FACILITY_UNCLUSTERED_LAYER_ID, handlePointerEnter);
        map.off('mouseleave', FACILITY_CLUSTER_LAYER_ID, handlePointerLeave);
        map.off('mouseleave', FACILITY_UNCLUSTERED_LAYER_ID, handlePointerLeave);
      }
    };
  }, [map, liveFacilities, selectedFacilityId, styleRevision]);

  // 4. Traffic Layer Toggle
  useEffect(() => {
    if (map.isStyleLoaded()) {
      if (showTraffic && !map.getLayer('traffic-flow')) {
        addTrafficLayer(map);
      }
      toggleTrafficLayer(map, showTraffic);
    }
  }, [map, showTraffic, styleRevision]);

  // 5. Safe Spaces Layer
  useEffect(() => {
    if (!map.isStyleLoaded() || !currentLocation) return;

    if (showSafeSpaces) {
      if (!map.getLayer('safe-spaces-circles')) {
        addSafeSpacesLayer(map, currentLocation.lat, currentLocation.lon).catch((err) => {
          logClientError('Failed to add safe spaces layer', err);
          useAppStore.getState().setShowSafeSpaces(false);
        });
      }
    }
  }, [map, showSafeSpaces, currentLocation, styleRevision]);

  useEffect(() => {
    if (!map.isStyleLoaded()) return;

    if (map.getLayer('safe-spaces-circles')) {
      map.setLayoutProperty('safe-spaces-circles', 'visibility', showSafeSpaces ? 'visible' : 'none');
    }
    if (map.getLayer('safe-spaces-labels')) {
      map.setLayoutProperty('safe-spaces-labels', 'visibility', showSafeSpaces ? 'visible' : 'none');
    }
  }, [map, showSafeSpaces, styleRevision]);

  return null;
}