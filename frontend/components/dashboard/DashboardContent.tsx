'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import dynamic from 'next/dynamic';
import TopSearch from './TopSearch';
import FloatingSidebarControls from './FloatingSidebarControls';
import RecentAlertsOverlay from './RecentAlertsOverlay';
import DashboardMapBootstrap from './DashboardMapBootstrap';

// Dynamically load the map without SSR so MapLibre boots only in the browser.
const MapBackground = dynamic(
  () => import('./MapBackgroundInner'),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 bg-surface-3/50 dark:bg-surface-3/50 animate-pulse flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border-4 border-brand/20 border-t-brand animate-spin" />
      </div>
    ),
  }
);

export default function DashboardContent() {
  return (
    <div className="relative flex-1 h-full w-full overflow-hidden">
      <DashboardMapBootstrap />
      <MapBackground />
      <TopSearch isMapPage={true} />
      <FloatingSidebarControls />
      <RecentAlertsOverlay />
    </div>
  );
}
