'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { useEffect, useMemo, useRef } from 'react';

import {
  fetchNearbyServices,
  fetchRoadIssues,
} from '@/lib/api';
import { useShallow } from 'zustand/react/shallow';
import { useGeolocation } from '@/lib/geolocation';
import { getAddressFromGPS } from '@/lib/reverse-geocode';
import { NearbyRoadIssue, NearbyService, useAppStore } from '@/lib/store';

const SEARCH_RADIUS_STEPS = [500, 1_000, 5_000, 12_000, 20_000, 35_000, 50_000];

function normalizeServiceCategory(category: string): NearbyService['category'] {
  switch (category) {
    case 'hospital':
    case 'police':
    case 'ambulance':
    case 'fire':
    case 'towing':
    case 'pharmacy':
    case 'puncture':
    case 'showroom':
      return category;
    default:
      return 'hospital';
  }
}

function toStoreServices(
  services: Awaited<ReturnType<typeof fetchNearbyServices>>['services']
): NearbyService[] {
  return services.map((service) => ({
    id: service.id,
    name: service.name,
    category: normalizeServiceCategory(service.category),
    lat: service.lat,
    lon: service.lon,
    distance: service.distanceMeters,
    phone: service.phone ?? service.phoneEmergency ?? undefined,
    address: service.address ?? undefined,
    source: service.source === 'offline' ? 'offline' : 'api',
  }));
}

function toStoreIssues(
  issues: Awaited<ReturnType<typeof fetchRoadIssues>>['issues']
): NearbyRoadIssue[] {
  return issues.map((issue) => ({
    uuid: issue.uuid,
    issueType: issue.issueType,
    severity: issue.severity,
    lat: issue.lat,
    lon: issue.lon,
    distance: issue.distanceMeters,
    status: issue.status,
    description: issue.description ?? undefined,
    authorityName: issue.authorityName ?? undefined,
    roadName: issue.roadName ?? undefined,
    roadType: issue.roadType ?? undefined,
    createdAt: issue.createdAt,
  }));
}

function buildRadiusAttempts(requestedRadius: number) {
  const cappedRadius = Math.max(500, Math.min(requestedRadius, 50_000));
  const attempts = SEARCH_RADIUS_STEPS.filter((step) => step <= cappedRadius);

  if (!attempts.length || attempts[attempts.length - 1] !== cappedRadius) {
    attempts.push(cappedRadius);
  }

  return attempts;
}

export default function DashboardMapBootstrap() {
  const { location, error, refresh } = useGeolocation();
  const lastHydrationKeyRef = useRef<string | null>(null);
  const {
    gpsLocation,
    mapSearchTarget,
    connectivity,
    serviceCategory,
    serviceRadius,
    setGpsLocation,
    setConnectivity,
    setNearbyRoadIssues,
    setNearbyServices,
    setRoadIssueSearchMeta,
    setServiceSearchMeta,
  } = useAppStore(useShallow((state) => ({
    gpsLocation: state.gpsLocation,
    mapSearchTarget: state.mapSearchTarget,
    connectivity: state.connectivity,
    serviceCategory: state.serviceCategory,
    serviceRadius: state.serviceRadius,
    setGpsLocation: state.setGpsLocation,
    setConnectivity: state.setConnectivity,
    setNearbyRoadIssues: state.setNearbyRoadIssues,
    setNearbyServices: state.setNearbyServices,
    setRoadIssueSearchMeta: state.setRoadIssueSearchMeta,
    setServiceSearchMeta: state.setServiceSearchMeta,
  })));

  useEffect(() => {
    const syncConnectivity = () => {
      setConnectivity(navigator.onLine ? 'online' : 'offline');
    };

    syncConnectivity();
    window.addEventListener('online', syncConnectivity);
    window.addEventListener('offline', syncConnectivity);

    return () => {
      window.removeEventListener('online', syncConnectivity);
      window.removeEventListener('offline', syncConnectivity);
    };
  }, [setConnectivity]);

  useEffect(() => {
    const handleRefresh = () => {
      refresh();
    };

    window.addEventListener('svai:refresh-location', handleRefresh);

    return () => {
      window.removeEventListener('svai:refresh-location', handleRefresh);
    };
  }, [refresh]);

  useEffect(() => {
    if (location || mapSearchTarget || !error) {
      return;
    }

    setConnectivity(navigator.onLine ? 'cached' : 'offline');
    setNearbyServices([]);
    setNearbyRoadIssues([]);
    setServiceSearchMeta({
      count: 0,
      radiusUsed: 0,
      requestedRadius: serviceRadius,
      source: 'api',
    });
    setRoadIssueSearchMeta({
      count: 0,
      radiusUsed: 0,
    });
  }, [
    error,
    location,
    mapSearchTarget,
    serviceRadius,
    setConnectivity,
    setNearbyRoadIssues,
    setNearbyServices,
    setRoadIssueSearchMeta,
    setServiceSearchMeta,
  ]);

  const lat = mapSearchTarget?.lat ?? location?.lat ?? gpsLocation?.lat;
  const lon = mapSearchTarget?.lon ?? location?.lon ?? gpsLocation?.lon;
  const requestedCategory = useMemo(
    () => (serviceCategory === 'all' ? undefined : serviceCategory),
    [serviceCategory]
  );
  const radiusAttempts = useMemo(() => buildRadiusAttempts(serviceRadius), [serviceRadius]);
  const hydrationKey = lat != null && lon != null
    ? `${lat.toFixed(4)}:${lon.toFixed(4)}:${requestedCategory ?? 'all'}:${serviceRadius}:${mapSearchTarget?.timestamp ?? 'gps'}`
    : null;

  useEffect(() => {
    if (lat == null || lon == null) {
      return;
    }

    const resolvedLat = lat;
    const resolvedLon = lon;
    let cancelled = false;

    if (hydrationKey && lastHydrationKeyRef.current === hydrationKey) {
      return;
    }
    lastHydrationKeyRef.current = hydrationKey;

    const controller = new AbortController();

    async function loadServicesWithFallback() {
      let latestFailure: unknown = null;

      for (const radius of radiusAttempts) {
        try {
          const response = await fetchNearbyServices({
            lat: resolvedLat,
            lon: resolvedLon,
            radius,
            categories: requestedCategory,
            limit: 24, signal: controller.signal,
          });

          if (response.services.length > 0 || radius === radiusAttempts[radiusAttempts.length - 1]) {
            return {
              ...response,
              requestedRadius: radius,
            };
          }
        } catch (requestError) {
          latestFailure = requestError;
        }
      }

      if (latestFailure) {
        throw latestFailure;
      }

      return {
        services: [],
        count: 0,
        radiusUsed: radiusAttempts[radiusAttempts.length - 1] ?? serviceRadius,
        source: 'api',
        requestedRadius: radiusAttempts[radiusAttempts.length - 1] ?? serviceRadius,
      };
    }

    async function hydrateDashboardMap() {
      const [servicesResult, issuesResult, geocodeResult] = await Promise.allSettled([
        loadServicesWithFallback(),
        fetchRoadIssues({
          lat: resolvedLat,
          lon: resolvedLon,
          radius: serviceRadius,
          limit: 12, signal: controller.signal,
        }),
        getAddressFromGPS(resolvedLat, resolvedLon),
      ]);

      if (cancelled) {
        return;
      }

      const servicesOk = servicesResult.status === 'fulfilled';
      const issuesOk = issuesResult.status === 'fulfilled';
      const geocodeOk = geocodeResult.status === 'fulfilled' && geocodeResult.value !== null;

      if (servicesOk) {
        setNearbyServices(toStoreServices(servicesResult.value.services));
        setServiceSearchMeta({
          count: servicesResult.value.count,
          radiusUsed: servicesResult.value.radiusUsed,
          requestedRadius: servicesResult.value.requestedRadius,
          source: servicesResult.value.source,
        });
      } else {
        setNearbyServices([]);
        setServiceSearchMeta({
          count: 0,
          radiusUsed: radiusAttempts[radiusAttempts.length - 1] ?? serviceRadius,
          requestedRadius: radiusAttempts[radiusAttempts.length - 1] ?? serviceRadius,
          source: connectivity === 'offline' ? 'offline' : 'api',
        });
      }

      if (issuesOk) {
        setNearbyRoadIssues(toStoreIssues(issuesResult.value.issues));
        setRoadIssueSearchMeta({
          count: issuesResult.value.count,
          radiusUsed: issuesResult.value.radiusUsed,
        });
      } else {
        setNearbyRoadIssues([]);
        setRoadIssueSearchMeta({
          count: 0,
          radiusUsed: serviceRadius,
        });
      }

      if (geocodeOk && !mapSearchTarget) {
        const geocode = geocodeResult.value!;
        setGpsLocation({
          lat: resolvedLat,
          lon: resolvedLon,
          accuracy: gpsLocation?.accuracy ?? location?.accuracy ?? 0,
          timestamp: gpsLocation?.timestamp ?? location?.timestamp ?? Date.now(),
          city: geocode.city ?? gpsLocation?.city,
          state: geocode.state ?? gpsLocation?.state,
          displayName: geocode.displayAddress ?? gpsLocation?.displayName,
        });
      }

      if (servicesOk || issuesOk || geocodeOk) {
        setConnectivity('online');
      } else {
        setConnectivity(navigator.onLine ? 'cached' : 'offline');
        lastHydrationKeyRef.current = null;
      }
    }

    hydrateDashboardMap().catch(() => {
      if (!cancelled) {
        setConnectivity(navigator.onLine ? 'cached' : 'offline');
        lastHydrationKeyRef.current = null;
      }
    });

    return () => {
      cancelled = true; controller.abort();
    };
  }, [
    gpsLocation?.accuracy,
    gpsLocation?.city,
    gpsLocation?.displayName,
    gpsLocation?.state,
    gpsLocation?.timestamp,
    hydrationKey,
    lat,
    location?.accuracy,
    location?.timestamp,
    lon,
    mapSearchTarget,
    serviceRadius,
    requestedCategory,
    radiusAttempts,
    connectivity,
    setConnectivity,
    setGpsLocation,
    setNearbyRoadIssues,
    setRoadIssueSearchMeta,
    setNearbyServices,
    setServiceSearchMeta,
  ]);

  return null;
}