// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

/**
 * Locator — Shared UI Components
 * ServiceIcon, EmptyState, RouteStatusCard extracted from page.tsx.
 */

import {
  Activity,
  Flame,
  Loader2,
  Navigation,
  Shield,
  Siren,
  Truck,
  Wrench,
} from 'lucide-react';
import { RouteOption, RoutePreviewResponse } from '@/lib/api';
import { ServiceSearchMeta } from '@/lib/store';
import {
  type Filter,
  type ServiceCardType,
  formatCoverageRadius,
  formatDistance,
  formatDuration,
} from './locator-utils';

export const ServiceIcon = ({ type, className }: { type: ServiceCardType; className?: string }) => {
  switch (type) {
    case 'Hospital':
      return <Activity className={className} />;
    case 'Ambulance':
      return <Siren className={className} />;
    case 'Pharmacy':
      return <Activity className={className} />;
    case 'Police':
      return <Shield className={className} />;
    case 'Fire':
      return <Flame className={className} />;
    case 'Towing':
      return <Truck className={className} />;
    case 'Mechanic':
    default:
      return <Wrench className={className} />;
  }
};

export function EmptyState({
  locating,
  activeFilter,
  searchMeta,
}: {
  locating: boolean;
  activeFilter: Filter;
  searchMeta: ServiceSearchMeta;
}) {
  const expandedBeyondDefault = searchMeta.radiusUsed > 5000;
  const hasNearbyServicesInOtherFilters = activeFilter !== 'All' && searchMeta.count > 0;

  return (
    <div className="rounded-lg border border-border-md dark:border-white/5 bg-white/80 dark:bg-surface-2/40 backdrop-blur-xl p-6 text-center">
      <h3 className="text-base font-black text-text-1 dark:text-text-1">
        {locating ? 'Finding nearest hospitals...' : 'No hospitals in 5km — expanding search radius...'}
      </h3>
      <p className="mt-2 text-sm text-text-2 dark:text-text-2">
        {locating
          ? 'Once the live backend responds, emergency resources will appear here.'
          : hasNearbyServicesInOtherFilters
            ? `We found nearby resources within ${formatCoverageRadius(searchMeta.radiusUsed)}, but none matched the ${activeFilter.toLowerCase()} filter.`
            : expandedBeyondDefault
              ? `Search widened to ${formatCoverageRadius(searchMeta.radiusUsed)} and still found no matching services. Try refreshing your location or switching filters.`
              : 'Try switching the filter or refreshing your location.'}
      </p>
    </div>
  );
}

export function RouteStatusCard({
  activeRoute,
  activeRouteOption,
  routeError,
  loadingLabel,
  selectedServiceName,
  navigationHref,
  selectedRouteId,
  onSelectRoute,
  rerouting,
}: {
  activeRoute: RoutePreviewResponse | null;
  activeRouteOption: RouteOption | null;
  routeError: string | null;
  loadingLabel: string | null;
  selectedServiceName: string | null;
  navigationHref: string | null;
  selectedRouteId: string | null;
  onSelectRoute: (_routeId: string) => void;
  rerouting: boolean;
}) {
  if (!activeRoute && !routeError && !loadingLabel) return null;

  if (routeError) {
    return (
      <div className="rounded-lg border border-warning/20 bg-warning/10/90 p-4 text-amber-900 shadow-sm dark:border-warning/20 dark:bg-warning/10 dark:text-warning">
        <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-amber-600 dark:text-amber-300">
          Route Unavailable
        </div>
        <p className="mt-2 text-sm font-semibold">{routeError}</p>
      </div>
    );
  }

  if (loadingLabel) {
    return (
      <div className="rounded-lg border border-brand/20 bg-brand/90 p-4 shadow-sm dark:border-brand/20 dark:bg-brand/10">
        <div className="flex items-center gap-3 text-brand dark:text-brand-light">
          <Loader2 size={16} className="animate-spin" />
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-brand dark:text-brand-light">
              Building Route
            </div>
            <p className="mt-1 text-sm font-semibold">Calculating the clearest drive to {loadingLabel}.</p>
          </div>
        </div>
      </div>
    );
  }

  if (!activeRoute || !activeRouteOption) return null;

  return (
    <div className="rounded-lg border border-brand-light/20 bg-brand-light/10/90 p-4 shadow-sm dark:border-brand-light/20 dark:bg-brand-light/10">
      <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-brand dark:text-brand-light">
        {rerouting ? 'Rerouting' : 'Route Ready'}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-sm font-semibold text-brand dark:text-brand-light">
        <span>{selectedServiceName ?? 'Destination selected'}</span>
        <span className="opacity-50">|</span>
        <span>{formatDuration(activeRouteOption.durationSeconds)}</span>
        <span className="opacity-50">|</span>
        <span>{formatDistance(activeRouteOption.distanceMeters)}</span>
      </div>
      <p className="mt-1 text-xs font-medium text-brand/ dark:text-brand-light/">
        Provider: {activeRoute.provider}
      </p>
      {activeRoute.warnings.length > 0 ? (
        <div className="mt-3 rounded-xl border border-warning/20/70 bg-warning/10/80 px-3 py-2 text-[11px] font-semibold text-amber-900 dark:border-warning/ dark:bg-warning/10 dark:text-warning">
          {activeRoute.warnings[0]}
        </div>
      ) : null}
      {activeRoute.routes.length > 1 ? (
        <div className="mt-3">
          <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-brand/ dark:text-brand-light/">
            Route Options
          </div>
          <div className="flex flex-wrap gap-2">
            {activeRoute.routes.map((routeOption) => {
              const isSelected = selectedRouteId === routeOption.routeId;
              return (
                <button
                  key={routeOption.routeId}
                  type="button"
                  onClick={() => onSelectRoute(routeOption.routeId)}
                  className={`rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.18em] transition ${
                    isSelected
                      ? 'border-brand-light bg-brand text-white shadow-lg shadow-brand/'
                      : 'border-brand-light/20 bg-white/80 text-brand hover:border-brand-light hover:bg-brand-light/15 dark:border-brand-light/15 dark:bg-white/5 dark:text-brand-light dark:hover:bg-brand-light/10'
                  }`}
                >
                  {routeOption.label} - {formatDuration(routeOption.durationSeconds)}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
      <div className="mt-4">
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-brand/ dark:text-brand-light/">
          Step-by-Step
        </div>
        <ol className="space-y-2">
          {activeRouteOption.steps.slice(0, 6).map((step) => (
            <li
              key={`${activeRouteOption.routeId}-${step.index}`}
              className="rounded-xl border border-brand-light/20/70 bg-white/80 px-3 py-2 text-left dark:border-brand-light/10 dark:bg-white/5"
            >
              <div className="flex items-start gap-3">
                <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand text-[10px] font-semibold text-white">
                  {step.index}
                </span>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-text-1 dark:text-brand-light">
                    {step.instruction}
                  </div>
                  <div className="mt-1 text-[11px] font-medium text-brand/80 dark:text-brand-light/">
                    {[step.streetName, formatDistance(step.distanceMeters), formatDuration(step.durationSeconds)]
                      .filter(Boolean)
                      .join(' - ')}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </div>
      {navigationHref ? (
        <a
          href={navigationHref}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-flex items-center gap-2 rounded-full border border-brand-light bg-white/80 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand transition hover:border-brand-light hover:bg-brand-light/15 dark:border-brand-light/15 dark:bg-white/5 dark:text-brand-light dark:hover:bg-brand-light/10"
        >
          <Navigation size={14} />
          Open External Navigation
        </a>
      ) : null}
    </div>
  );
}
