'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

import { client } from '@/lib/api';

interface MapLibreDashboardProps {
  activeCategory?: string;
  zoom?: number;
  center?: [number, number];
}

export default function MapLibreDashboard({ 
  activeCategory = '',
  zoom = 11,
  center = [80.2707, 13.0827]
}: MapLibreDashboardProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // CartoDB Dark Matter is a gorgeous, premium, dark-themed base map
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: center,
      zoom: zoom,
      attributionControl: { compact: false },
    });

    mapRef.current = map;

    map.on('load', async () => {
      setLoading(false);
      
      try {
        // Fetch heatmap geojson
        const { data } = await client.get('/api/v1/analytics/heatmap', {
          params: activeCategory ? { category: activeCategory } : {},
        });

        // Add GeoJSON Source
        map.addSource('complaints', {
          type: 'geojson',
          data: data,
        });

        // Add glowing Heatmap Layer
        map.addLayer({
          id: 'complaints-heatmap',
          type: 'heatmap',
          source: 'complaints',
          maxzoom: 15,
          paint: {
            // Increase the heatmap weight based on severity
            'heatmap-weight': [
              'interpolate',
              ['linear'],
              ['get', 'severity'],
              1, 0.2,
              5, 1
            ],
            // Increase the heatmap color weight by zoom level
            'heatmap-intensity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              0, 1,
              15, 3
            ],
            // Color ramp for heatmap.  Red-orange-yellow-green neon glow
            'heatmap-color': [
              'interpolate',
              ['linear'],
              ['heatmap-value'],
              0, 'rgba(0, 255, 255, 0)',
              0.2, 'rgba(0, 245, 255, 0.2)',
              0.4, 'rgba(168, 85, 247, 0.4)',
              0.6, 'rgba(244, 63, 94, 0.7)',
              0.8, 'rgba(249, 115, 22, 0.8)',
              1, 'rgba(239, 68, 68, 1)'
            ],
            // Adjust the heatmap radius by zoom level
            'heatmap-radius': [
              'interpolate',
              ['linear'],
              ['zoom'],
              0, 5,
              15, 25
            ],
            // Transition out heatmap at higher zoom to reveal individual points
            'heatmap-opacity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              13, 0.8,
              15, 0
            ]
          } as any
        });

        // Add Individual Point Circle Markers Layer
        map.addLayer({
          id: 'complaints-point',
          type: 'circle',
          source: 'complaints',
          minzoom: 12,
          paint: {
            // Size circle markers based on severity
            'circle-radius': [
              'interpolate',
              ['linear'],
              ['get', 'severity'],
              1, 5,
              5, 10
            ],
            // Color code markers by category
            'circle-color': [
              'match',
              ['get', 'category'],
              'roads', '#06b6d4',      // Cyan for roads
              'traffic', '#f97316',    // Orange for traffic
              'streetlight', '#a855f7', // Purple for streetlight
              '#3b82f6'                // Blue default
            ],
            'circle-stroke-width': 2,
            'circle-stroke-color': '#000000',
            // Adjust opacity by zoom
            'circle-opacity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              12, 0,
              13, 1
            ],
            'circle-stroke-opacity': [
              'interpolate',
              ['linear'],
              ['zoom'],
              12, 0,
              13, 1
            ]
          } as any
        });

        // Add click popups
        map.on('click', 'complaints-point', (e) => {
          const coordinates = (e.features?.[0]?.geometry as any)?.coordinates.slice();
          const props = e.features?.[0]?.properties;

          if (!coordinates || !props) return;

          // Make sure the popup is placed correctly
          while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
          }

          new maplibregl.Popup({ className: 'custom-maplibre-popup' })
            .setLngLat(coordinates)
            .setHTML(`
              <div style="font-family: 'Space Grotesk', sans-serif; color: #020617; padding: 6px;">
                <div style="font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b;">
                  ${props.category} INCIDENT
                </div>
                <div style="font-size: 13px; font-weight: 800; margin-top: 4px; color: #0f172a;">
                  Severity Lock: Level ${props.severity}
                </div>
                <div style="margin-top: 6px; font-size: 11px; font-weight: 600; color: #0284c7;">
                  Ref: ${props.uuid.slice(0, 8).toUpperCase()}
                </div>
              </div>
            `)
            .addTo(map);
        });

        // Change cursor on hover
        map.on('mouseenter', 'complaints-point', () => {
          map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', 'complaints-point', () => {
          map.getCanvas().style.cursor = '';
        });

      } catch (err) {
        console.error("Failed to load map data points:", err);
      }
    });

    return () => {
      map.remove();
    };
  }, [activeCategory]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainerRef} className="w-full h-full rounded-[1.8rem] overflow-hidden" />
      {loading && (
        <div className="absolute inset-0 bg-black/40 dark:bg-slate-950/80 flex items-center justify-center rounded-[1.8rem] z-10">
          <div className="flex flex-col items-center gap-3">
            <Loader2 size={32} className="animate-spin text-brand" />
            <span className="text-xs font-semibold uppercase tracking-widest text-text-3">Acquiring GIS Feeds...</span>
          </div>
        </div>
      )}
    </div>
  );
}