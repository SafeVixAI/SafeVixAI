'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

/* ────────────────────────────────────────────────────────────
   SafeVixAI Landing — Live Map
   Displays active incidents and monitoring stations in India
   ──────────────────────────────────────────────────────────── */

const CITIES = [
  // Emergency hotspots (red)
  { name: 'Delhi', lng: 77.209, lat: 28.6139, type: 'emergency' },
  { name: 'Mumbai', lng: 72.8777, lat: 19.076, type: 'emergency' },
  { name: 'Chennai', lng: 80.2707, lat: 13.0827, type: 'emergency' },
  { name: 'Kolkata', lng: 88.3639, lat: 22.5726, type: 'emergency' },
  { name: 'Bangalore', lng: 77.5946, lat: 12.9716, type: 'emergency' },
  // Monitoring cities (green)
  { name: 'Hyderabad', lng: 78.4867, lat: 17.385, type: 'monitoring' },
  { name: 'Ahmedabad', lng: 72.5714, lat: 23.0225, type: 'monitoring' },
  { name: 'Pune', lng: 73.8567, lat: 18.5204, type: 'monitoring' },
  { name: 'Jaipur', lng: 75.7873, lat: 26.9124, type: 'monitoring' },
  { name: 'Lucknow', lng: 80.9462, lat: 26.8467, type: 'monitoring' },
  { name: 'Kochi', lng: 76.2673, lat: 9.9312, type: 'monitoring' },
  { name: 'Bhopal', lng: 77.4126, lat: 23.2599, type: 'monitoring' },
  { name: 'Nagpur', lng: 79.0882, lat: 21.1458, type: 'monitoring' },
  { name: 'Chandigarh', lng: 76.7794, lat: 30.7333, type: 'monitoring' },
  { name: 'Guwahati', lng: 91.7362, lat: 26.1445, type: 'monitoring' },
  { name: 'Patna', lng: 85.1376, lat: 25.5941, type: 'monitoring' },
  { name: 'Varanasi', lng: 82.9739, lat: 25.3176, type: 'monitoring' },
];

export default function HeroLiveMap() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    // Use a standard dark raster map style using Carto Dark Matter (no API key required)
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://d.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'
            ],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          }
        },
        layers: [
          {
            id: 'carto-dark-layer',
            type: 'raster',
            source: 'carto-dark',
            minzoom: 0,
            maxzoom: 22
          }
        ]
      },
      center: [78.9629, 22.5937], // Center of India
      zoom: 3.8,
      pitch: 45,
      bearing: 10,
      interactive: false, // Prevent scrolling/panning in Hero section
    });

    map.current.on('load', () => {
      setMapLoaded(true);

      // Add markers
      CITIES.forEach(city => {
        const isEmergency = city.type === 'emergency';
        const color = isEmergency ? '#DC2626' : '#00C896';

        // Create a custom DOM element for the marker to add glowing effect
        const el = document.createElement('div');
        el.className = 'custom-map-marker';
        el.style.width = isEmergency ? '12px' : '10px';
        el.style.height = isEmergency ? '12px' : '10px';
        el.style.backgroundColor = color;
        el.style.borderRadius = '50%';
        el.style.boxShadow = `0 0 ${isEmergency ? '15px' : '10px'} ${color}`;

        // Add a pulsing animation via standard CSS injected dynamically or globally
        el.style.animation = `pulse-marker ${isEmergency ? '1.5s' : '2.5s'} infinite alternate`;

        new maplibregl.Marker({ element: el })
          .setLngLat([city.lng, city.lat])
          .addTo(map.current!);
      });

      // Slowly rotate the map to give it a cinematic feel
      let bearing = 10;
      const rotateCamera = () => {
        if (!map.current) return;
        bearing += 0.05;
        map.current.setBearing(bearing);
        requestAnimationFrame(rotateCamera);
      };
      rotateCamera();
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  return (
    <div className="w-full h-full relative rounded-lg overflow-hidden" style={{ minHeight: '600px' }}>
      {/* Map container */}
      <div ref={mapContainer} className="absolute inset-0 w-full h-full" />
      
      {/* Loading state fallback */}
      {!mapLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#0a3d1f]/10 backdrop-blur-sm z-10">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 rounded-full border-2 border-brand-light border-t-transparent animate-spin mb-4" />
            <span className="text-xs text-brand-light font-mono uppercase tracking-wider animate-pulse">
              Initializing Spatial Grid...
            </span>
          </div>
        </div>
      )}

      {/* Embedded CSS for marker animations */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes pulse-marker {
          0% { transform: scale(0.9); opacity: 0.7; }
          100% { transform: scale(1.3); opacity: 1; }
        }
      `}} />
    </div>
  );
}
