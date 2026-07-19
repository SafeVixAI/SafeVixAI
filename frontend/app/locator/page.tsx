// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';



import DashboardMapBootstrap from '@/components/dashboard/DashboardMapBootstrap';
import SystemHeader from '@/components/dashboard/SystemHeader';
import TopSearch from '@/components/dashboard/TopSearch';
import { useTranslation } from 'react-i18next';
import { useLocatorSearch } from '@/hooks/useLocatorSearch';
import { useSwipe } from '@/hooks/useSwipe';
import type { ServiceSearchMeta } from '@/lib/store';
import { RouteOption, RoutePreviewResponse } from '@/lib/api';
import { MapPin } from 'lucide-react';
import { useState } from 'react';

import { LocatorFilters } from './components/LocatorFilters';
import { LocatorMap } from './components/LocatorMap';
import { DesktopResultsList, MobileResultsList } from './components/LocatorResults';
import { EmptyState, RouteStatusCard } from './locator-components';
import { Filter, LocatorService } from './locator-utils';
import { SkeletonCard } from '@/components/ui/SkeletonCard';
import { PRIMARY_EMERGENCY_BAR } from '@/lib/emergency-numbers';

function MobileLocator({
  coords,
  currentLocation,
  address,
  filtered,
  locating,
  serviceSearchMeta,
  coverageSummary,
  activeFilter,
  setActiveFilter,
  activeRoute,
  activeRouteOption,
  alternativeRoutes,
  routeError,
  routeLoadingId,
  selectedServiceId,
  selectedServiceName,
  navigationHref,
  selectedRouteId,
  rerouting,
  onLocateService,
  onSelectRoute,
  onPreviewService,
}: {
  coords: [number, number];
  currentLocation: {
    lat: number;
    lon: number;
    accuracy: number;
    displayName?: string;
  } | null;
  address: string;
  filtered: LocatorService[];
  locating: boolean;
  serviceSearchMeta: ServiceSearchMeta;
  coverageSummary: string;
  activeFilter: Filter;
  setActiveFilter: (_filter: Filter) => void;
  activeRoute: RoutePreviewResponse | null;
  activeRouteOption: RouteOption | null;
  alternativeRoutes: RouteOption[];
  routeError: string | null;
  routeLoadingId: string | null;
  selectedServiceId: string | null;
  selectedServiceName: string | null;
  navigationHref: string | null;
  selectedRouteId: string | null;
  rerouting: boolean;
  onLocateService: (_service: LocatorService) => void;
  onSelectRoute: (_routeId: string) => void;
  onPreviewService: (_service: LocatorService) => void;
}) {
  const { t } = useTranslation();
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');
  const { onTouchStart: swipeStart, onTouchEnd: swipeEnd } = useSwipe({
    onSwipeUp: () => setViewMode('list'),
    onSwipeDown: () => setViewMode('map'),
    onSwipeLeft: () => setViewMode('list'),
    onSwipeRight: () => setViewMode('map'),
  });
  const locationIsApproximate = Boolean(currentLocation && currentLocation.accuracy >= 2500);
  const currentLocationAccuracy = currentLocation
    ? currentLocation.accuracy >= 1000
      ? `${(currentLocation.accuracy / 1000).toFixed(1)} km accuracy`
      : `${Math.round(currentLocation.accuracy)} m accuracy`
    : null;

  return (
    <div className="sv-aurora min-h-dvh pb-48 bg-surface-2 dark:bg-surface-1 text-text-1 dark:text-text-1 font-['Inter'] selection:bg-brand/30 relative overflow-x-hidden w-full">
      <SystemHeader title={t('locator.resource_dispatch')} showBack={false} />

      <div className="lg:hidden relative z-[100]">
        <TopSearch isMapPage={true} forceShow={true} showBack={false} />
      </div>

      <div className="pt-24 lg:pt-0 px-5 flex items-center justify-between relative z-10 hide-on-short-screen">
        <div>
          <h2 className="text-text-1 dark:text-text-1 font-black tracking-tight text-xl font-space uppercase">
            {t('locator.emergency_locator')}
          </h2>
          <p className="text-[11px] text-text-2 dark:text-brand-light font-bold opacity-80 mt-1 tracking-wider uppercase">
            {address} - {coverageSummary}
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-light/10 border border-brand-light/20">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse" />
          <span className="text-[10px] font-semibold text-brand-dim dark:text-brand-light uppercase tracking-widest">
            {t('locator.live_hud')}
          </span>
        </div>
      </div>

      <main className="relative z-10 pt-4 pb-40 w-full sv-swipe-area" onTouchStart={swipeStart} onTouchEnd={swipeEnd}>
        {/* View mode toggle indicator */}
        <div className="flex justify-center gap-1.5 pb-2 lg:hidden">
          <button onClick={() => setViewMode('map')} className={`h-1.5 rounded-full transition-all duration-300 ${viewMode === 'map' ? 'w-6 bg-brand-light' : 'w-2 bg-border'}`} aria-label={t('locator.locate')} />
          <button onClick={() => setViewMode('list')} className={`h-1.5 rounded-full transition-all duration-300 ${viewMode === 'list' ? 'w-6 bg-brand-light' : 'w-2 bg-border'}`} aria-label={t('locator.filters.All')} />
          <span className="text-[9px] font-semibold text-text-3 uppercase tracking-widest ml-2 self-center">Swipe ↔</span>
        </div>

        {viewMode === 'map' && (
        <section className="relative h-[calc(var(--full-content-h)_-_128px)] min-h-[320px] max-h-[520px] w-full px-4 border-b border-border-md dark:border-white/5 overflow-hidden">
          <div className="relative h-full w-full rounded-lg overflow-hidden bg-surface-3 dark:bg-[#030e20] border border-border-md dark:border-white/10 shadow-2xl">
            <div className="absolute inset-0 z-0">
              <LocatorMap
                coords={coords}
                filtered={filtered}
                activeRouteOption={activeRouteOption}
                alternativeRoutes={alternativeRoutes}
                currentLocation={currentLocation}
                address={address}
                selectedServiceId={selectedServiceId}
              />
            </div>
            <div className="absolute inset-0 pointer-events-none z-10" />
          </div>
        </section>
        )}

        {viewMode === 'list' && (
        <>
        <section className="mt-6 px-4 relative">
          <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-surface-2 dark:from-surface-1 to-transparent z-20 pointer-events-none" />
          <LocatorFilters activeFilter={activeFilter} setActiveFilter={setActiveFilter} />
        </section>

        <section className="mt-2 px-4 space-y-4">
          <RouteStatusCard
            activeRoute={activeRoute}
            activeRouteOption={activeRouteOption}
            routeError={routeError}
            loadingLabel={filtered.find((service) => service.id === routeLoadingId)?.name ?? null}
            selectedServiceName={selectedServiceName}
            navigationHref={navigationHref}
            selectedRouteId={selectedRouteId}
            onSelectRoute={onSelectRoute}
            rerouting={rerouting}
          />
          {locationIsApproximate && currentLocationAccuracy ? (
            <div className="rounded-lg border border-warning/20 bg-warning/10/90 px-4 py-3 text-amber-900 shadow-sm dark:border-warning/20 dark:bg-warning/10 dark:text-warning">
              <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-amber-600 dark:text-amber-300">
                {t('locator.approximate_location')}
              </div>
              <p className="mt-1 text-sm font-semibold">
                {t('locator.approximate_location_warning', { accuracy: currentLocationAccuracy })}
              </p>
            </div>
          ) : null}
          {locating ? (
            <div className="space-y-4">
              <SkeletonCard lines={2} hasIcon={true} hasButton={true} />
              <SkeletonCard lines={2} hasIcon={true} hasButton={true} />
              <SkeletonCard lines={2} hasIcon={true} hasButton={true} />
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              locating={locating}
              activeFilter={activeFilter}
              searchMeta={serviceSearchMeta}
            />
          ) : (
            <MobileResultsList
              filtered={filtered}
              selectedServiceId={selectedServiceId}
              routeLoadingId={routeLoadingId}
              onLocateService={onLocateService}
              onPreviewService={onPreviewService}
            />
          )}
        </section>
        </>
        )}
      </main>
    </div>
  );
}

function DesktopLocator({
  coords,
  currentLocation,
  address,
  filtered,
  locating,
  serviceSearchMeta,
  coverageSummary,
  activeFilter,
  setActiveFilter,
  activeRoute,
  activeRouteOption,
  alternativeRoutes,
  routeError,
  routeLoadingId,
  selectedServiceId,
  selectedServiceName,
  navigationHref,
  selectedRouteId,
  rerouting,
  onLocateService,
  onSelectRoute,
  onPreviewService,
}: {
  coords: [number, number];
  currentLocation: {
    lat: number;
    lon: number;
    accuracy: number;
    displayName?: string;
  } | null;
  address: string;
  filtered: LocatorService[];
  locating: boolean;
  serviceSearchMeta: ServiceSearchMeta;
  coverageSummary: string;
  activeFilter: Filter;
  setActiveFilter: (_filter: Filter) => void;
  activeRoute: RoutePreviewResponse | null;
  activeRouteOption: RouteOption | null;
  alternativeRoutes: RouteOption[];
  routeError: string | null;
  routeLoadingId: string | null;
  selectedServiceId: string | null;
  selectedServiceName: string | null;
  navigationHref: string | null;
  selectedRouteId: string | null;
  rerouting: boolean;
  onLocateService: (_service: LocatorService) => void;
  onSelectRoute: (_routeId: string) => void;
  onPreviewService: (_service: LocatorService) => void;
}) {
  const { t } = useTranslation();
  const locationIsApproximate = Boolean(currentLocation && currentLocation.accuracy >= 2500);
  const currentLocationAccuracy = currentLocation
    ? currentLocation.accuracy >= 1000
      ? `${(currentLocation.accuracy / 1000).toFixed(1)} km accuracy`
      : `${Math.round(currentLocation.accuracy)} m accuracy`
    : null;

  const labelKeyMap: Record<string, string> = {
    'SOS': 'emergency.system_sos',
    'POLICE': 'emergency.police',
    'AMBULANCE': 'emergency.ambulance',
    'HIGHWAY': 'emergency.highway'
  };

  return (
    <div className="w-full h-[var(--full-content-h-desktop)] bg-surface-2 dark:bg-surface-1 text-text-1 dark:text-text-1 font-['Inter'] relative overflow-hidden flex flex-col">
      <SystemHeader title={t('locator.resource_dispatch')} showBack={false} />

      <main className="flex-1 flex w-full relative z-0 overflow-hidden lg:mt-0">
        <section className="flex-1 h-full relative overflow-hidden bg-surface-3 dark:bg-bg border-r border-border-md dark:border-white/5">
          <div className="absolute top-20 left-6 right-6 z-20 flex justify-center">
            <div className="flex gap-1 bg-white/90 dark:bg-bg/80 backdrop-blur-2xl p-1.5 rounded-lg border border-border-md dark:border-white/10 shadow-2xl overflow-x-auto [scrollbar-width:none]">
              <LocatorFilters activeFilter={activeFilter} setActiveFilter={setActiveFilter} />
            </div>
          </div>

          <div className="absolute inset-0 z-0">
            <LocatorMap
              coords={coords}
              filtered={filtered}
              activeRouteOption={activeRouteOption}
              alternativeRoutes={alternativeRoutes}
              currentLocation={currentLocation}
              address={address}
              selectedServiceId={selectedServiceId}
            />
            <div className="absolute inset-0 pointer-events-none bg-surface-1/ dark:bg-black/20 mix-blend-color z-10" />
          </div>

          <div className="absolute bottom-8 left-8 z-20 bg-white/90 dark:bg-surface-1/90 backdrop-blur-md p-4 rounded-lg border border-border-md dark:border-white/10 shadow-xl min-w-[180px] hidden lg:block">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-2 h-2 rounded-full bg-brand-light animate-pulse" />
              <span className="text-[10px] font-semibold tracking-widest text-text-2 uppercase">{t('locator.telemetry_active')}</span>
            </div>
            <div className="text-sm font-semibold text-text-1 dark:text-brand-light tracking-tight">{address}</div>
            <div className="mt-1 text-xs font-semibold text-text-2 dark:text-text-2">{coverageSummary}</div>
          </div>
        </section>

        <section className="w-[300px] lg:w-[340px] xl:w-[360px] h-full bg-white dark:bg-surface-1 flex flex-col z-20 shadow-2xl overflow-hidden shadow-[-10px_0_30px_-15px_rgba(0,0,0,0.1)] dark:shadow-[-10px_0_30px_-15px_rgba(0,0,0,0.5)] border-l border-border-md dark:border-white/5">
          <div className="p-6 lg:p-8 pb-4 shrink-0">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-brand flex items-center justify-center shadow-lg shadow-brand/20 shrink-0">
                <MapPin className="text-white w-5 h-5" />
              </div>
              <div className="overflow-hidden">
                <h2 className="text-[10px] font-semibold uppercase tracking-[0.1em] text-brand dark:text-brand-light whitespace-nowrap">
                  {t('locator.locator_subsystem')}
                </h2>
                <h2 className="text-xl lg:text-2xl font-black tracking-tight text-text-1 dark:text-white leading-none truncate">
                  {t('locator.emergency_resources')}
                </h2>
              </div>
            </div>
            <p className="text-text-2 dark:text-text-2 text-xs lg:text-sm font-medium">
              {filtered.length === 1 
                ? t('locator.found_facilities_one', { location: coverageSummary }) 
                : t('locator.found_facilities_other', { count: filtered.length, location: coverageSummary })}
            </p>
            <div className="mt-4">
              <RouteStatusCard
                activeRoute={activeRoute}
                activeRouteOption={activeRouteOption}
                routeError={routeError}
                loadingLabel={filtered.find((service) => service.id === routeLoadingId)?.name ?? null}
                selectedServiceName={selectedServiceName}
                navigationHref={navigationHref}
                selectedRouteId={selectedRouteId}
                onSelectRoute={onSelectRoute}
                rerouting={rerouting}
              />
              {locationIsApproximate && currentLocationAccuracy ? (
                <div className="mt-4 rounded-lg border border-warning/20 bg-warning/10/90 px-4 py-3 text-amber-900 shadow-sm dark:border-warning/20 dark:bg-warning/10 dark:text-warning">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-amber-600 dark:text-amber-300">
                    {t('locator.approximate_location')}
                  </div>
                  <p className="mt-1 text-sm font-semibold">
                    {t('locator.approximate_location_warning_desktop', { accuracy: currentLocationAccuracy })}
                  </p>
                </div>
              ) : null}
            </div>
          </div>

          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {locating ? (
              <div className="px-6 lg:px-8 py-4 space-y-4 overflow-y-auto">
                <SkeletonCard lines={2} hasIcon={true} hasButton={true} />
                <SkeletonCard lines={2} hasIcon={true} hasButton={true} />
                <SkeletonCard lines={2} hasIcon={true} hasButton={true} />
              </div>
            ) : filtered.length === 0 ? (
              <div className="px-6 lg:px-8 py-4">
                <EmptyState
                  locating={locating}
                  activeFilter={activeFilter}
                  searchMeta={serviceSearchMeta}
                />
              </div>
            ) : (
              <DesktopResultsList
                filtered={filtered}
                selectedServiceId={selectedServiceId}
                routeLoadingId={routeLoadingId}
                onLocateService={onLocateService}
                onPreviewService={onPreviewService}
              />
            )}
          </div>

          <div className="p-6 lg:p-8 bg-surface-2 dark:bg-surface-1/ border-t border-border-md dark:border-white/5 grid grid-cols-2 lg:grid-cols-4 gap-2 lg:gap-3 shrink-0">
            {PRIMARY_EMERGENCY_BAR.map((dial) => (
              <a key={dial.service} href={`tel:${dial.service}`} className="flex flex-col items-center justify-center py-3 lg:py-4 bg-white dark:bg-white/5 rounded-lg border border-border-md dark:border-white/5 hover:border-brand/50 transition-all group">
                <span className="text-base lg:text-lg font-black text-text-1 dark:text-white group-hover:text-brand dark:text-brand-light">{dial.service}</span>
                <span className="text-[7px] lg:text-[8px] font-bold text-text-2 uppercase tracking-widest">{t(labelKeyMap[dial.label] || 'emergency.emergency')}</span>
              </a>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default function LocatorPage() {
  const locator = useLocatorSearch();

  return (
    <div className="w-full h-full min-h-dvh flex flex-col overflow-hidden">
      <h1 className="sr-only">Emergency Locator</h1>
      <DashboardMapBootstrap />
      <div className="lg:hidden flex-1 flex flex-col">
        <MobileLocator
          coords={locator.coords}
          currentLocation={locator.gpsLocation}
          address={locator.address}
          filtered={locator.filtered}
          locating={locator.locating}
          serviceSearchMeta={locator.serviceSearchMeta}
          coverageSummary={locator.coverageSummary}
          activeFilter={locator.activeFilter}
          setActiveFilter={locator.setActiveFilter}
          activeRoute={locator.activeRoute}
          activeRouteOption={locator.activeRouteOption}
          alternativeRoutes={locator.alternativeRoutes}
          routeError={locator.routeError}
          routeLoadingId={locator.routeLoadingId}
          selectedServiceId={locator.selectedServiceId}
          selectedServiceName={locator.selectedService ? locator.selectedService.name : null}
          navigationHref={locator.navigationHref}
          selectedRouteId={locator.selectedRouteId}
          rerouting={locator.rerouting}
          onLocateService={locator.handleLocateService}
          onSelectRoute={locator.handleSelectRoute}
          onPreviewService={locator.handlePreviewService}
        />
      </div>

      <div className="hidden lg:flex flex-1 flex-col h-full overflow-hidden">
        <DesktopLocator
          coords={locator.coords}
          currentLocation={locator.gpsLocation}
          address={locator.address}
          filtered={locator.filtered}
          locating={locator.locating}
          serviceSearchMeta={locator.serviceSearchMeta}
          coverageSummary={locator.coverageSummary}
          activeFilter={locator.activeFilter}
          setActiveFilter={locator.setActiveFilter}
          activeRoute={locator.activeRoute}
          activeRouteOption={locator.activeRouteOption}
          alternativeRoutes={locator.alternativeRoutes}
          routeError={locator.routeError}
          routeLoadingId={locator.routeLoadingId}
          selectedServiceId={locator.selectedServiceId}
          selectedServiceName={locator.selectedService ? locator.selectedService.name : null}
          navigationHref={locator.navigationHref}
          selectedRouteId={locator.selectedRouteId}
          rerouting={locator.rerouting}
          onLocateService={locator.handleLocateService}
          onSelectRoute={locator.handleSelectRoute}
          onPreviewService={locator.handlePreviewService}
        />
      </div>
    </div>
  );
}
