'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import dynamic from 'next/dynamic';
import TopSearch from '../components/dashboard/TopSearch';
import FloatingSidebarControls from '../components/dashboard/FloatingSidebarControls';
import RecentAlertsOverlay from '../components/dashboard/RecentAlertsOverlay';
import DashboardMapBootstrap from '../components/dashboard/DashboardMapBootstrap';


// Dynamically load the map without SSR so MapLibre boots only in the browser.
const MapBackground = dynamic(
  () => import('../components/dashboard/MapBackgroundInner'),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 bg-surface-3/50 dark:bg-surface-3/50 animate-pulse flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border-4 border-brand/20 border-t-brand animate-spin" />
      </div>
    )
  });

export default function V2Dashboard() {
  return (
    <div className="relative isolate h-[var(--full-content-h)] min-h-[var(--full-content-h)] md:h-[var(--full-content-h-desktop)] md:min-h-[var(--full-content-h-desktop)] w-full overflow-hidden bg-surface-1 text-text-1 flex">
      <h1 className="sr-only">SafeVixAI Dashboard</h1>
      <div className="relative flex-1 h-full w-full overflow-hidden">
        <DashboardMapBootstrap />
        <MapBackground />
        <TopSearch isMapPage={true} />
        <FloatingSidebarControls />
        <RecentAlertsOverlay />
      </div>
    </div>
  );
}