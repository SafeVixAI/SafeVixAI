// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import maplibregl from 'maplibre-gl';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { MapStyleCandidate } from '@/components/maps/map-types';
import { buildStyleCandidates } from '@/components/maps/map-styles';
import { useAppStore } from '@/lib/store';
import { addTrafficLayer, toggleTrafficLayer } from '@/lib/traffic-layer';

interface UseMapInstanceProps {
  center: [number, number];
  zoom: number;
  resolvedTheme: string | undefined;
  showSatellite: boolean;
  showTraffic: boolean;
  navigationPosition?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

export function useMapInstance({
  center,
  zoom,
  resolvedTheme,
  showSatellite,
  showTraffic,
  navigationPosition = 'bottom-left',
}: UseMapInstanceProps) {
  const mapNodeRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const activeStyleIndexRef = useRef(0);
  const styleReadyRef = useRef(false);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [statusMessage, setStatusMessage] = useState<string>('Loading map...');
  const [styleRevision, setStyleRevision] = useState(0);

  const setMapState = useAppStore((state) => state.setMapState);
  const initialCenterRef = useRef(center);
  const initialZoomRef = useRef(zoom);
  const showTrafficRef = useRef(showTraffic);

  useEffect(() => {
    showTrafficRef.current = showTraffic;
  }, [showTraffic]);

  const STYLE_CANDIDATES = useMemo<MapStyleCandidate[]>(
    () => buildStyleCandidates(resolvedTheme, showSatellite),
    [resolvedTheme, showSatellite]
  );

  const candidatesRef = useRef(STYLE_CANDIDATES);
  useEffect(() => {
    candidatesRef.current = STYLE_CANDIDATES;
  }, [STYLE_CANDIDATES]);

  // Style switching when theme/satellite option changes
  useEffect(() => {
    if (mapRef.current && mapRef.current.isStyleLoaded()) {
      const activeCandidate = STYLE_CANDIDATES[activeStyleIndexRef.current];
      /* istanbul ignore next */
      if (activeCandidate) {
        styleReadyRef.current = false;
        setStatus('loading');
        setStatusMessage(`Loading ${activeCandidate.label}...`);
        setMapState({
          mapStatus: 'loading',
          mapProvider: activeCandidate.kind,
          mapError: null,
        });
        setStyleRevision((revision) => revision + 1);
        mapRef.current.setStyle(activeCandidate.style as maplibregl.StyleSpecification);
      }
    }
  }, [STYLE_CANDIDATES, setMapState]);

  // Map initialization
  useEffect(() => {
    if (!mapNodeRef.current || mapRef.current) {
      return;
    }

    let disposed = false;
    let map: maplibregl.Map | null = null;
    let resizeTimeout: number | undefined;

    const handleResize = () => {
      /* istanbul ignore next */
      if (map) map.resize();
    };

    async function initializeMap() {
      setStatus('loading');
      setStatusMessage('Loading map...');
      activeStyleIndexRef.current = 0;
      styleReadyRef.current = false;

      /* istanbul ignore next */
      if (disposed || !mapNodeRef.current) {
        return;
      }

      const getActiveCandidate = () => candidatesRef.current[activeStyleIndexRef.current];
      setMapState({
        mapStatus: 'loading',
        mapProvider: getActiveCandidate().kind,
        mapError: null,
      });

      map = new maplibregl.Map({
        container: mapNodeRef.current!,
        style: getActiveCandidate().style as maplibregl.StyleSpecification,
        center: [initialCenterRef.current[1], initialCenterRef.current[0]],
        zoom: initialZoomRef.current,
        maxZoom: 18,
        minZoom: 3,
        renderWorldCopies: false,
        pitchWithRotate: false,
        cooperativeGestures: false,
        fadeDuration: 0,
      });

      const applyNextStyle = (message: string) => {
        /* istanbul ignore next */
        if (!map) {
          return;
        }

        const nextIndex = activeStyleIndexRef.current + 1;
        /* istanbul ignore next */
        if (nextIndex >= candidatesRef.current.length) {
          setStatus('error');
          setStatusMessage('Map service is unavailable right now.');
          setMapState({
            mapStatus: 'error',
            mapProvider: getActiveCandidate()?.kind ?? null,
            mapError: 'Map service is unavailable right now.',
          });
          return;
        }

        const nextCandidate = candidatesRef.current[nextIndex];
        activeStyleIndexRef.current = nextIndex;
        styleReadyRef.current = false;
        setStatus('loading');
        setStatusMessage(message);
        setMapState({
          mapStatus: 'loading',
          mapProvider: nextCandidate.kind,
          mapError: null,
        });
        setStyleRevision((revision) => revision + 1);
        map.setStyle(nextCandidate.style as maplibregl.StyleSpecification);
      };

      /* istanbul ignore next */
      const handleMapError = (event: unknown) => {
        const errorEvent = event as {
          error?: { message?: string; status?: number };
          sourceId?: string;
        };
        const message = (errorEvent?.error?.message ?? '').toLowerCase();
        const activeCandidate = getActiveCandidate();

        const isHardFailure =
          message.includes('401') ||
          message.includes('403') ||
          message.includes('fetch') ||
          message.includes('failed to fetch') ||
          (message.includes('maptiler') && (message.includes('unavailable') || message.includes('error')));

        if (isHardFailure && activeCandidate.kind !== 'openfreemap') {
          applyNextStyle(`Service unavailable, switching to fallback map...`);
          return;
        }

        if (activeCandidate.kind === 'openfreemap' && !styleReadyRef.current) {
          setStatus('error');
          setStatusMessage('Map service is unavailable right now.');
          setMapState({
            mapStatus: 'error',
            mapProvider: activeCandidate.kind,
            mapError: 'Map service is unavailable right now.',
          });
        }
      };

      /* istanbul ignore next */
      const handleStyleImageMissing = (event: unknown) => {
        const imageEvent = event as { id?: string };
        const activeCandidate = getActiveCandidate();
        const missingId = typeof imageEvent?.id === 'string' ? imageEvent.id.trim() : '';

        if (activeCandidate.kind === 'maptiler-vector' && missingId.length === 0) {
          applyNextStyle('MapTiler vector assets unavailable, trying raster fallback...');
        }
      };

      const syncReadyState = () => {
        /* istanbul ignore next */
        if (!map || styleReadyRef.current) {
          return;
        }

        /* istanbul ignore next */
        if (map.isStyleLoaded() && map.areTilesLoaded()) {
          styleReadyRef.current = true;
          setStatus('ready');
          setMapState({
            mapStatus: 'ready',
            mapProvider: getActiveCandidate().kind,
            mapError: null,
          });
        }
      };

      map.addControl(
        new maplibregl.NavigationControl({
          showCompass: false,
          visualizePitch: false,
        }),
        navigationPosition
      );
      map.dragRotate.disable();
      map.touchZoomRotate.disableRotation();
      map.once('load', () => {
        /* istanbul ignore next */
        map?.resize();
        /* istanbul ignore next */
        map?.jumpTo({
          center: [initialCenterRef.current[1], initialCenterRef.current[0]],
          zoom: initialZoomRef.current,
        });
        /* istanbul ignore next */
        if (map) {
          addTrafficLayer(map);
          toggleTrafficLayer(map, showTrafficRef.current);
        }
      });
      map.on('idle', syncReadyState);
      map.on('sourcedata', syncReadyState);
      map.on('error', handleMapError);
      map.on('styleimagemissing', handleStyleImageMissing);

      window.addEventListener('resize', handleResize);
      resizeTimeout = window.setTimeout(handleResize, 150) as unknown as number;

      mapRef.current = map;

      window.setTimeout(() => {
        /* istanbul ignore next */
        if (!disposed && map && !styleReadyRef.current) {
          const activeCandidate = getActiveCandidate();
          /* istanbul ignore next */
          if (activeCandidate.kind !== 'openfreemap') {
            applyNextStyle('Map connection timed out, switching to fallback...');
            return;
          }
          setStatus('error');
          setStatusMessage('Map style did not finish loading.');
          setMapState({
            mapStatus: 'error',
            mapProvider: activeCandidate.kind,
            mapError: 'Map style did not finish loading.',
          });
        }
      }, 12000);
    }

    /* istanbul ignore next */
    initializeMap().catch(() => {
      if (!disposed) {
        setStatus('error');
        setStatusMessage('Unable to initialize the map.');
        setMapState({
          mapStatus: 'error',
          mapProvider: null,
          mapError: 'Unable to initialize the map.',
        });
      }
    });

    return () => {
      disposed = true;
      window.removeEventListener('resize', handleResize);
      /* istanbul ignore next */
      if (resizeTimeout) window.clearTimeout(resizeTimeout);
      /* istanbul ignore next */
      map?.remove();
      mapRef.current = null;
      activeStyleIndexRef.current = 0;
      styleReadyRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigationPosition]);

  return {
    map: mapRef.current,
    mapNodeRef,
    status,
    statusMessage,
    styleRevision,
  };
}
