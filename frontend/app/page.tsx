'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import dynamic from 'next/dynamic';
import { useAppStore } from '@/lib/store';
import { useHydrated } from '@/lib/use-hydrated';

// Dynamically load the entire dashboard so its JS is NOT included in the
// initial bundle for unauthenticated visitors.  This eliminates the flash
// of dashboard UI that appeared before AuthGuard could redirect to /landing.
const DashboardContent = dynamic(
  () => import('../components/dashboard/DashboardContent'),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 bg-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-brand-light/30 border-t-brand-light rounded-full animate-spin" />
          <span className="text-xs font-mono text-text-3 uppercase tracking-wider">Loading dashboard...</span>
        </div>
      </div>
    ),
  }
);

export default function V2Dashboard() {
  const hydrated = useHydrated();
  const isAuthenticated = useAppStore((s) => s.isAuthenticated);

  // While Zustand store is rehydrating, show nothing (prevents dashboard flash)
  if (!hydrated) {
    return (
      <div className="relative isolate h-[var(--full-content-h)] min-h-[var(--full-content-h)] md:h-[var(--full-content-h-desktop)] md:min-h-[var(--full-content-h-desktop)] w-full overflow-hidden bg-bg text-text-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-brand-light/30 border-t-brand-light rounded-full animate-spin" />
          <span className="text-xs font-mono text-text-3 uppercase tracking-wider">Initializing...</span>
        </div>
      </div>
    );
  }

  // Not authenticated → AuthGuard will redirect, but don't render heavy dashboard
  if (!isAuthenticated) {
    return (
      <div className="relative isolate h-[var(--full-content-h)] min-h-[var(--full-content-h)] md:h-[var(--full-content-h-desktop)] md:min-h-[var(--full-content-h-desktop)] w-full overflow-hidden bg-bg text-text-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-brand-light/30 border-t-brand-light rounded-full animate-spin" />
          <span className="text-xs font-mono text-text-3 uppercase tracking-wider">Verifying session...</span>
        </div>
      </div>
    );
  }

  // Authenticated — lazy-load the actual dashboard
  return (
    <div className="relative isolate h-[var(--full-content-h)] min-h-[var(--full-content-h)] md:h-[var(--full-content-h-desktop)] md:min-h-[var(--full-content-h-desktop)] w-full overflow-hidden bg-surface-1 text-text-1 flex">
      <h1 className="sr-only">SafeVixAI Dashboard</h1>
      <DashboardContent />
    </div>
  );
}