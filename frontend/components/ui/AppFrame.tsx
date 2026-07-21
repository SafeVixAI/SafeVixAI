'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { ReactNode, lazy, Suspense } from 'react';
import { usePathname } from 'next/navigation';
import { AppSidebar } from '@/components/AppSidebar';
import SystemSidebar from '@/components/dashboard/SystemSidebar';
import BottomNav from '@/components/dashboard/BottomNav';
import { RightSidebar } from '@/components/RightSidebar';
import { NetworkMonitor } from '@/components/NetworkMonitor';
import { GlobalSOS } from '@/components/GlobalSOS';
import { KeyboardShortcutsHelp } from '@/components/ui/KeyboardShortcutsHelp';
import { OfflineBanner } from '@/components/ui/OfflineBanner';
import { SystemStatusBar } from '@/components/ui/SystemStatusBar';
import { ServerWarmingBanner } from '@/components/ui/ServerWarmingBanner';
import { ServerHealthStatus } from '@/components/ServerHealthStatus';
import { useAppStore } from '@/lib/store';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { Menu } from 'lucide-react';

const CommandPalette = lazy(() => import('@/components/search/CommandPalette').then((m) => ({ default: m.CommandPalette })));

interface AppFrameProps {
  children: ReactNode;
}

export function AppFrame({ children }: AppFrameProps) {
  const pathname = usePathname();
  const isDesktopSidebarCollapsed = useAppStore((state) => state.isDesktopSidebarCollapsed);
  const setDesktopSidebarCollapsed = useAppStore((state) => state.setDesktopSidebarCollapsed);
  const isThinSidebarEnabled = useAppStore((state) => state.isThinSidebarEnabled);

  // Define routes that should NOT have the global navigation shell (e.g. auth, public emergency views)
  const NO_NAV_ROUTES = [
    '/login', '/signup', '/forgot-password', '/auth',
    '/bystander', '/emergency-card', '/share-receive', 
    '/track', '/landing', '/privacy', '/terms', '/offline'
  ];
  
  // Check if current path matches or starts with a no-nav route
  const isNoNavRoute = NO_NAV_ROUTES.some(route => 
    pathname === route || pathname.startsWith(`${route}/`)
  );

  if (isNoNavRoute) {
    return (
      <div className="flex min-h-dvh w-full bg-bg text-text-1 transition-colors duration-300">
        <NetworkMonitor />
        <SystemStatusBar />
        <OfflineBanner />
        <ServerWarmingBanner />
        <ServerHealthStatus />
        {/* Intentionally omitting GlobalSOS, Sidebar, and BottomNav for these standalone pages */}
        <main className="flex-1 w-full relative flex flex-col">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh w-full bg-bg text-text-1 transition-colors duration-300">
      {/* ── Skip Link for Accessibility ── */}
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 p-2 bg-surface-1 text-text-1 font-bold rounded">
        Skip to main content
      </a>

      {/* ── Global Utilities ── */}
      <NetworkMonitor />
      <GlobalSOS />
      <Suspense fallback={null}><CommandPalette /></Suspense>
      <KeyboardShortcutsHelp />
      <SystemStatusBar />
      <OfflineBanner />
      <ServerWarmingBanner />
      <ServerHealthStatus />

      {/* ── Navigation Shell ── */}
      
      {/* 1. Desktop Sidebar */}
      <div className="hidden lg:block">
        <AppSidebar />
        {isDesktopSidebarCollapsed && !isThinSidebarEnabled && (
          <button
            onClick={() => setDesktopSidebarCollapsed(false)}
            aria-label="Expand Sidebar"
            className="fixed top-4 left-4 z-50 w-12 h-12 flex items-center justify-center bg-surface-2/90 backdrop-blur-xl border border-border rounded-xl shadow-lg hover:bg-surface-3 hover:scale-105 active:scale-95 transition-all text-text-1"
          >
            <Menu className="w-5 h-5" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* 2. Mobile Sidebar Drawer */}
      <SystemSidebar />

      {/* ── Main Content Area ── */}
      <main 
        id="main" 
        className={`flex-1 relative flex flex-col min-h-dvh min-w-0 transition-all duration-300 pb-[var(--bottom-nav-h,84px)] lg:pb-0 ${
          !isDesktopSidebarCollapsed ? 'lg:ml-[280px]' : isThinSidebarEnabled ? 'lg:ml-[88px]' : 'lg:ml-0'
        }`}
      >
        <AuthGuard>
        <div className="relative flex-1 w-full flex flex-col">
          {children}
        </div>
        </AuthGuard>
      </main>
      
      {/* Right action panel is desktop-only; mobile uses bottom navigation and full-screen pages. */}
      <div className="hidden lg:block">
        <RightSidebar />
      </div>

      {/* 3. Mobile Bottom Navigation */}
      <div className="lg:hidden z-40 relative">
        <BottomNav />
      </div>
    </div>
  );
}