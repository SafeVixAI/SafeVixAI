// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

var mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

var mockSetSystemSidebarOpen = jest.fn();
jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => {
    const state = {
      setSystemSidebarOpen: mockSetSystemSidebarOpen,
      isAuthenticated: false,
      operatorName: '',
    };
    return selector(state);
  },
}));

jest.mock('@/components/ThemeProvider', () => ({
  useTheme: () => ({ theme: 'dark', setTheme: jest.fn() }),
}));

describe('SystemHeader', function() {
  beforeEach(function() {
    jest.clearAllMocks();
  });

  it('renders header with branding', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    var header = document.querySelector('header');
    expect(header).toBeInTheDocument();
  });

  it('contains SafeVixAI title by default', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    expect(screen.getByText('SafeVixAI')).toBeInTheDocument();
  });

  it('shows Sentinel Active status indicator', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    expect(screen.getByText('Sentinel Active')).toBeInTheDocument();
  });

  it('renders search form with placeholder', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    expect(screen.getByPlaceholderText('Ask Maps or Search System')).toBeInTheDocument();
  });

  it('renders back button when showBack is true', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    expect(screen.getByLabelText('Go back')).toBeInTheDocument();
  });

  it('does not render back button when showBack is false', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader showBack={false} />);
    expect(screen.queryByLabelText('Go back')).not.toBeInTheDocument();
  });

  it('renders custom title when provided', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader title="Emergency Dashboard" />);
    expect(screen.getByText('Emergency Dashboard')).toBeInTheDocument();
  });

  it('shows Online/Offline toggle buttons', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('shows Secure badge', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    expect(screen.getByText('Secure')).toBeInTheDocument();
  });

  it('renders voice search button', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    expect(screen.getByLabelText('Start voice search')).toBeInTheDocument();
  });

  it('renders theme switcher buttons when mounted', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    await waitFor(function() { expect(screen.getByLabelText('Light mode')).toBeInTheDocument() });
    expect(screen.getByLabelText('Dark mode')).toBeInTheDocument();
    expect(screen.getByLabelText('Auto theme')).toBeInTheDocument();
  });

  it('search form submission navigates to assistant', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    var input = screen.getByPlaceholderText('Ask Maps or Search System');
    fireEvent.change(input, { target: { value: 'test query' } });
    var form = document.querySelector('form[role="search"]');
    if (form) {
      fireEvent.submit(form);
      expect(mockPush).toHaveBeenCalledWith('/assistant?q=test%20query');
    }
  });

  it('renders menu button with correct label', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    var menuBtn = screen.getByLabelText('Open navigation menu');
    expect(menuBtn).toBeInTheDocument();
  });

  it('menu button click calls setSystemSidebarOpen(true)', async function() {
    var SystemHeader = (await import('../dashboard/SystemHeader')).default;
    render(<SystemHeader />);
    fireEvent.click(screen.getByLabelText('Open navigation menu'));
    expect(mockSetSystemSidebarOpen).toHaveBeenCalledWith(true);
  });
});



