// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

var mockStore = {
  isDesktopSidebarCollapsed: false,
  isThinSidebarEnabled: false,
  setDesktopSidebarCollapsed: jest.fn(),
};

jest.mock('next/navigation', () => ({
  usePathname: () => '/',
}));

jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => selector(mockStore),
}));

jest.mock('lucide-react', () => ({
  Menu: () => <span data-testid="menu-icon" />,
}));

jest.mock('@/components/AppSidebar', () => ({
  AppSidebar: () => <div data-testid="app-sidebar" />,
}));

jest.mock('@/components/dashboard/SystemSidebar', () => ({
  __esModule: true,
  default: () => <div data-testid="system-sidebar" />,
}));

jest.mock('@/components/dashboard/BottomNav', () => ({
  __esModule: true,
  default: () => <div data-testid="bottom-nav" />,
}));

jest.mock('@/components/RightSidebar', () => ({
  RightSidebar: () => <div data-testid="right-sidebar" />,
}));

jest.mock('@/components/NetworkMonitor', () => ({
  NetworkMonitor: () => <div data-testid="network-monitor" />,
}));

jest.mock('@/components/GlobalSOS', () => ({
  GlobalSOS: () => <div data-testid="global-sos" />,
}));

jest.mock('@/components/search/CommandPalette', () => ({
  CommandPalette: () => <div data-testid="command-palette" />,
}));

jest.mock('@/components/ui/KeyboardShortcutsHelp', () => ({
  KeyboardShortcutsHelp: () => <div data-testid="keyboard-shortcuts" />,
}));

jest.mock('@/components/ui/OfflineBanner', () => ({
  OfflineBanner: () => <div data-testid="offline-banner" />,
}));

jest.mock('@/components/ui/SystemStatusBar', () => ({
  SystemStatusBar: () => <div data-testid="system-status-bar" />,
}));

jest.mock('@/components/ui/ServerWarmingBanner', () => ({
  ServerWarmingBanner: () => <div data-testid="server-warming-banner" />,
}));

jest.mock('@/components/auth/AuthGuard', () => ({
  AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import { AppFrame } from '../ui/AppFrame';

describe('AppFrame', function() {
  it('renders children inside frame', function() {
    render(<AppFrame><span data-testid="child">content</span></AppFrame>);
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('renders text children', function() {
    render(<AppFrame>Hello World</AppFrame>);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('has global utility components', function() {
    render(<AppFrame>content</AppFrame>);
    expect(screen.getByTestId('network-monitor')).toBeInTheDocument();
    expect(screen.getByTestId('global-sos')).toBeInTheDocument();
    expect(screen.getByTestId('command-palette')).toBeInTheDocument();
    expect(screen.getByTestId('keyboard-shortcuts')).toBeInTheDocument();
    expect(screen.getByTestId('system-status-bar')).toBeInTheDocument();
    expect(screen.getByTestId('offline-banner')).toBeInTheDocument();
    expect(screen.getByTestId('server-warming-banner')).toBeInTheDocument();
  });

  it('has sidebar and navigation components', function() {
    render(<AppFrame>content</AppFrame>);
    expect(screen.getByTestId('app-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('system-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('bottom-nav')).toBeInTheDocument();
    expect(screen.getByTestId('right-sidebar')).toBeInTheDocument();
  });

  it('has skip to main content link', function() {
    render(<AppFrame>content</AppFrame>);
    var skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute('href', '#main');
  });

  it('has main content area with id main', function() {
    render(<AppFrame>content</AppFrame>);
    expect(document.getElementById('main')).toBeInTheDocument();
  });

  it('has correct wrapper structure', function() {
    var { container } = render(<AppFrame>content</AppFrame>);
    expect(container.firstChild).toHaveClass('flex');
    expect(container.firstChild).toHaveClass('min-h-dvh');
  });

  it('shows Expand Sidebar button when collapsed and thin disabled', function() {
    mockStore.isDesktopSidebarCollapsed = true;
    mockStore.isThinSidebarEnabled = false;
    render(<AppFrame>content</AppFrame>);
    expect(screen.getByLabelText('Expand Sidebar')).toBeInTheDocument();
  });

  it('hides Expand Sidebar button when thin enabled', function() {
    mockStore.isDesktopSidebarCollapsed = true;
    mockStore.isThinSidebarEnabled = true;
    render(<AppFrame>content</AppFrame>);
    expect(screen.queryByLabelText('Expand Sidebar')).toBeNull();
  });

  it('hides Expand Sidebar button when not collapsed', function() {
    mockStore.isDesktopSidebarCollapsed = false;
    mockStore.isThinSidebarEnabled = false;
    render(<AppFrame>content</AppFrame>);
    expect(screen.queryByLabelText('Expand Sidebar')).toBeNull();
  });
});



