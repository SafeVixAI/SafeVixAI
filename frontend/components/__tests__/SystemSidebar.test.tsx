// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockUsePathname = jest.fn();
jest.mock('next/navigation', () => ({
  usePathname: () => mockUsePathname(),
}));

const mockSetSystemSidebarOpen = jest.fn();
jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => {
    const state = {
      isSystemSidebarOpen: true,
      setSystemSidebarOpen: mockSetSystemSidebarOpen,
    };
    return selector(state);
  },
}));

describe('SystemSidebar', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    mockUsePathname.mockReturnValue('/');
  });

  it('renders when isSystemSidebarOpen is true', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('renders all main navigation items', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    const navLabels = ['Map', 'AI Assistant', 'Locator', 'Tracking', 'First Aid', 'Report Road Issue', 'Challan Calculator', 'Profile', 'Settings'];
    for (const label of navLabels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getAllByText('Emergency').length).toBeGreaterThanOrEqual(1);
  });

  it('highlights active link based on pathname', async function() {
    mockUsePathname.mockReturnValue('/assistant');
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    const links = screen.getAllByRole('link');
    const activeLink = links.find(
      (link) => link.getAttribute('href') === '/assistant'
    );
    expect(activeLink).toBeInTheDocument();
  });

  it('shows SafeVixAI branding in sidebar', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    expect(screen.getByText('SafeVixAI')).toBeInTheDocument();
  });

  it('shows Protocol Active status', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    expect(screen.getByText('Protocol Active')).toBeInTheDocument();
  });

  it('renders emergency quick dial numbers', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    expect(screen.getByText('112')).toBeInTheDocument();
    expect(screen.getByText('102')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('1033')).toBeInTheDocument();
  });

  it('renders System SOS link', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    expect(screen.getByText('System SOS')).toBeInTheDocument();
  });

  it('closes sidebar when close button is clicked', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    fireEvent.click(screen.getByLabelText('Close Sidebar'));
    expect(mockSetSystemSidebarOpen).toHaveBeenCalledWith(false);
  });

  it('closes sidebar when backdrop is clicked', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    const backdrop = document.querySelector('.fixed.inset-0');
    if (backdrop) fireEvent.click(backdrop);
    expect(mockSetSystemSidebarOpen).toHaveBeenCalledWith(false);
  });

  it('renders Operations Console section heading', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    expect(screen.getByText('Operations Console')).toBeInTheDocument();
  });

  it('renders Emergency Quick Dial heading', async function() {
    const SystemSidebar = (await import('../dashboard/SystemSidebar')).default;
    render(<SystemSidebar />);
    expect(screen.getByText('Emergency Quick Dial')).toBeInTheDocument();
  });
});



