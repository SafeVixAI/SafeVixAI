'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useEffect, useRef, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapPin, Loader2, Navigation } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface LocationPickerInnerProps {
  lat: number;
  lon: number;
  onLocationChange: (_lat: number, _lon: number, _address: string) => void;
  className?: string;
}

function LocationPickerInner({ lat, lon, onLocationChange, className }: LocationPickerInnerProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const marker = useRef<maplibregl.Marker | null>(null);
  const { t } = useTranslation('common');
  const [address, setAddress] = useState(t('report.detecting_location', 'Detecting location...'));
  const [loading, setLoading] = useState(false);

  // Reverse geocode using BigDataCloud (free, no API key needed)
  const reverseGeocode = useCallback(async (latitude: number, longitude: number) => {
    setLoading(true);
    try {
      const res = await fetch(
        `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`
      );
      const data = await res.json();
      const parts = [data.locality, data.city, data.principalSubdivision].filter(Boolean);
      const addr = parts.join(', ') || `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
      setAddress(addr);
      onLocationChange(latitude, longitude, addr);
    } catch {
      const addr = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
      setAddress(addr);
      onLocationChange(latitude, longitude, addr);
    } finally {
      setLoading(false);
    }
  }, [onLocationChange]);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [lon, lat],
      zoom: 15,
      attributionControl: { compact: false },
    });

    m.addControl(new maplibregl.NavigationControl(), 'top-right');

    // Draggable marker
    const mk = new maplibregl.Marker({ color: '#ef4444', draggable: true })
      .setLngLat([lon, lat])
      .addTo(m);

    mk.on('dragend', () => {
      const lngLat = mk.getLngLat();
      reverseGeocode(lngLat.lat, lngLat.lng);
    });

    marker.current = mk;
    map.current = m;

    // Initial geocode
    if (lat !== 0 && lon !== 0) {
      reverseGeocode(lat, lon);
    }

    return () => {
      m.remove();
      map.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update marker when lat/lon props change
  useEffect(() => {
    if (marker.current && map.current && lat !== 0 && lon !== 0) {
      marker.current.setLngLat([lon, lat]);
      map.current.flyTo({ center: [lon, lat], zoom: 15 });
      reverseGeocode(lat, lon);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lon]);

  const centerOnUser = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        if (marker.current && map.current) {
          marker.current.setLngLat([longitude, latitude]);
          map.current.flyTo({ center: [longitude, latitude], zoom: 16 });
          reverseGeocode(latitude, longitude);
        }
      },
      null,
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  return (
    <div className={className}>
      {/* Map */}
      <div className="relative rounded-xl overflow-hidden border border-border">
        <div ref={mapContainer} className="w-full h-[300px] sm:h-[350px]" />

        {/* Recenter button */}
        <button
          onClick={centerOnUser}
          className="absolute bottom-3 right-3 p-2.5 bg-surface-1/90 backdrop-blur-sm border border-border rounded-xl text-brand-light hover:bg-surface-2 transition-colors shadow-lg"
          aria-label={t('report.recenter_map', 'Recenter map on your location')}
          title={t('report.center_on_my_location', 'Center on my location')}
        >
          <Navigation size={18} />
        </button>
      </div>

      {/* Address display */}
      <div className="mt-3 flex items-center gap-2 p-3 rounded-xl bg-surface-2 border border-border">
        {loading ? (
          <Loader2 size={14} className="animate-spin text-brand-light shrink-0" />
        ) : (
          <MapPin size={14} className="text-brand-light shrink-0" />
        )}
        <p className="text-sm text-text-2 truncate">{address}</p>
      </div>

      <p className="mt-2 text-[10px] text-text-3 uppercase tracking-wider font-semibold">
        {t('report.drag_pin_hint', 'Drag the pin to adjust location')}
      </p>
    </div>
  );
}

export default LocationPickerInner;