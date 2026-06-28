// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { useEffect, useMemo, useRef, useState } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useAppStore } from '@/lib/store';
import { fetchRoutePreview, RoutePreviewResponse } from '@/lib/api';
import { formatLocationSubtitle } from '@/lib/location-utils';
import { FALLBACK_MAP_CENTER } from '@/lib/map-defaults';
import {
  type Filter,
  type LocatorService,
  mapService,
  formatCoverageRadius,
  haversineMeters,
  minimumRouteDeviationMeters,
  buildNavigationHref,
} from '@/app/locator/locator-utils';

const DEFAULT_COORDS: [number, number] = FALLBACK_MAP_CENTER;

export function useLocatorSearch() {
  const [activeFilter, setActiveFilter] = useState<Filter>('All');
  const [selectedServiceId, setSelectedServiceId] = useState<string | null>(null);
  const [activeRoute, setActiveRoute] = useState<RoutePreviewResponse | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [routeLoadingId, setRouteLoadingId] = useState<string | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [rerouting, setRerouting] = useState(false);
  
  const lastRerouteAtRef = useRef(0);
  const lastRerouteLocationRef = useRef<[number, number] | null>(null);

  const { gpsError, gpsLocation, nearbyServices, serviceSearchMeta } = useAppStore(useShallow((state) => ({
    gpsError: state.gpsError,
    gpsLocation: state.gpsLocation,
    nearbyServices: state.nearbyServices,
    serviceSearchMeta: state.serviceSearchMeta,
  })))

  const coords: [number, number] = gpsLocation ? [gpsLocation.lat, gpsLocation.lon] : /* istanbul ignore next */ DEFAULT_COORDS;

  const address = gpsError
    ? 'Location access needed'
    : gpsLocation
      ? formatLocationSubtitle(gpsLocation)
      : 'Allow location to find hospitals near you';

  const coverageSummary =
    serviceSearchMeta.radiusUsed > 0
      ? `${formatCoverageRadius(serviceSearchMeta.radiusUsed)} coverage`
      : `${formatCoverageRadius(5000)} coverage`;

  const locating = !gpsLocation && !gpsError;

  const services = useMemo(() => nearbyServices.map(mapService), [nearbyServices]);

  const filtered = useMemo(
    () => services.filter((service) => activeFilter === 'All' || service.filterType === activeFilter),
    [activeFilter, services]
  );

  const selectedService = useMemo(
    () => filtered.find((service) => service.id === selectedServiceId) ?? null,
    [filtered, selectedServiceId]
  );

  const activeRouteOption = useMemo(
    () => activeRoute?.routes.find((route) => route.routeId === selectedRouteId) ?? activeRoute?.routes[0] ?? null,
    [activeRoute, selectedRouteId]
  );

  const alternativeRoutes = useMemo(
    () => activeRoute?.routes.filter((route) => route.routeId !== activeRouteOption?.routeId) ?? [],
    [activeRoute, activeRouteOption?.routeId]
  );

  const navigationHref =
    gpsLocation && selectedService
      ? buildNavigationHref(
          [gpsLocation.lat, gpsLocation.lon],
          selectedService.coords,
        )
      : null;

  // Effects
  useEffect(() => {
    if (filtered.length === 0) {
      setSelectedServiceId(null);
      setActiveRoute(null);
      setSelectedRouteId(null);
      return;
    }

    if (!selectedServiceId || !filtered.some((service) => service.id === selectedServiceId)) {
      setSelectedServiceId(filtered[0].id);
      setActiveRoute(null);
      setSelectedRouteId(null);
    }
  }, [filtered, selectedServiceId]);

  useEffect(() => {
    if (!activeRoute) return;

    if (!selectedRouteId || !activeRoute.routes.some((route) => route.routeId === selectedRouteId)) {
      setSelectedRouteId(activeRoute.selectedRouteId);
    }
  }, [activeRoute, selectedRouteId]);

  useEffect(() => {
    if (!gpsLocation) return;

    setActiveRoute(null);
    setSelectedRouteId(null);
  }, [gpsLocation]);

  function extractRouteError(error: unknown) {
    if (typeof error === 'object' && error !== null) {
      const maybeResponse = error as { response?: { data?: { detail?: string } }; message?: string };
      if (typeof maybeResponse.response?.data?.detail === 'string') {
        return maybeResponse.response.data.detail;
      }
      if (typeof maybeResponse.message === 'string') {
        return maybeResponse.message;
      }
    }
    return 'Unable to calculate the route right now.';
  }

  function handlePreviewService(service: LocatorService) {
    setSelectedServiceId(service.id);
    setRouteError(null);
    if (activeRoute && selectedServiceId !== service.id) {
      setActiveRoute(null);
      setSelectedRouteId(null);
    }
  }

  async function handleLocateService(service: LocatorService) {
    setSelectedServiceId(service.id);
    setRouteError(null);

    if (!gpsLocation) {
      setActiveRoute(null);
      setRouteLoadingId(null);
      setRouteError('Allow location to calculate a road-aware route from your current position.');
      return;
    }

    setRouteLoadingId(service.id);
    try {
      const route = await fetchRoutePreview({
        originLat: gpsLocation.lat,
        originLon: gpsLocation.lon,
        destinationLat: service.coords[0],
        destinationLon: service.coords[1],
        profile: 'driving-car',
        alternatives: 2,
      });
      setActiveRoute(route);
      setSelectedRouteId(route.selectedRouteId);
      lastRerouteAtRef.current = Date.now();
      lastRerouteLocationRef.current = [gpsLocation.lat, gpsLocation.lon];
    } catch (error) {
      setActiveRoute(null);
      setSelectedRouteId(null);
      setRouteError(extractRouteError(error));
    } finally {
      setRouteLoadingId(null);
    }
  }

  function handleSelectRoute(routeId: string) {
    setSelectedRouteId(routeId);
  }

  // Auto Rerouting Effect
  useEffect(() => {
    if (!gpsLocation || !selectedService || !activeRoute || !activeRouteOption || routeLoadingId || rerouting) {
      return;
    }

    const currentLocation: [number, number] = [gpsLocation.lat, gpsLocation.lon];
    const lastRerouteLocation = lastRerouteLocationRef.current;
    const now = Date.now();
    const movedSinceLastReroute = lastRerouteLocation
      ? haversineMeters(currentLocation, lastRerouteLocation)
      : 0;
    const deviation = minimumRouteDeviationMeters(activeRouteOption, currentLocation);

    if (deviation < activeRoute.rerouteThresholdMeters || movedSinceLastReroute < 90 || now - lastRerouteAtRef.current < 15_000) {
      return;
    }

    let cancelled = false;
    setRerouting(true);
    setRouteError(null);

    fetchRoutePreview({
      originLat: gpsLocation.lat,
      originLon: gpsLocation.lon,
      destinationLat: selectedService.coords[0],
      destinationLon: selectedService.coords[1],
      profile: 'driving-car',
      alternatives: 2,
    })
      /* istanbul ignore next */
      .then((route) => {
/* istanbul ignore next */
        if (cancelled) return;
/* istanbul ignore next */
        setActiveRoute(route);
/* istanbul ignore next */
        setSelectedRouteId(route.selectedRouteId);
/* istanbul ignore next */
        lastRerouteAtRef.current = Date.now();
/* istanbul ignore next */
        lastRerouteLocationRef.current = currentLocation;
      })
      /* istanbul ignore next */
      .catch((error) => {
/* istanbul ignore next */
        if (!cancelled) {
/* istanbul ignore next */
          setRouteError(extractRouteError(error));
        }
      })
      /* istanbul ignore next */
      .finally(() => {
        if (!cancelled) {
/* istanbul ignore next */
          setRerouting(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [activeRoute, activeRouteOption, gpsLocation, rerouting, routeLoadingId, selectedService]);

  return {
    activeFilter,
    setActiveFilter,
    selectedServiceId,
    setSelectedServiceId,
    activeRoute,
    selectedRouteId,
    routeLoadingId,
    routeError,
    rerouting,
    coords,
    address,
    coverageSummary,
    locating,
    services,
    filtered,
    selectedService,
    activeRouteOption,
    alternativeRoutes,
    navigationHref,
    gpsLocation,
    serviceSearchMeta,
    handlePreviewService,
    handleLocateService,
    handleSelectRoute,
  };
}
