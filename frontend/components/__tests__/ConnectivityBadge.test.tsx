// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockUseAppStore = jest.fn();

jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => mockUseAppStore(selector),
}));

import { ConnectivityBadge } from '../ConnectivityBadge';

describe('ConnectivityBadge', function() {
  beforeEach(function() {
    mockUseAppStore.mockReset();
  });

  it('renders online label', function() {
    mockUseAppStore.mockReturnValue('online');
    render(<ConnectivityBadge />);
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('renders cached label', function() {
    mockUseAppStore.mockReturnValue('cached');
    render(<ConnectivityBadge />);
    expect(screen.getByText('Cached')).toBeInTheDocument();
  });

  it('renders offline label', function() {
    mockUseAppStore.mockReturnValue('offline');
    render(<ConnectivityBadge />);
    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('renders ai-offline label', function() {
    mockUseAppStore.mockReturnValue('ai-offline');
    render(<ConnectivityBadge />);
    expect(screen.getByText('AI Active')).toBeInTheDocument();
  });

  it('has role status', function() {
    mockUseAppStore.mockReturnValue('online');
    render(<ConnectivityBadge />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has aria-live polite', function() {
    mockUseAppStore.mockReturnValue('online');
    render(<ConnectivityBadge />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');
  });

  it('has aria-label with connectivity state', function() {
    mockUseAppStore.mockReturnValue('offline');
    render(<ConnectivityBadge />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Connectivity: Offline');
  });

  it('applies correct color class for online', function() {
    mockUseAppStore.mockReturnValue('online');
    const { container } = render(<ConnectivityBadge />);
    expect(container.firstChild).toHaveClass('sv-conn-online');
  });

  it('applies correct color class for cached', function() {
    mockUseAppStore.mockReturnValue('cached');
    const { container } = render(<ConnectivityBadge />);
    expect(container.firstChild).toHaveClass('sv-conn-cached');
  });

  it('applies correct color class for offline', function() {
    mockUseAppStore.mockReturnValue('offline');
    const { container } = render(<ConnectivityBadge />);
    expect(container.firstChild).toHaveClass('sv-conn-offline');
  });

  it('applies correct color class for ai-offline', function() {
    mockUseAppStore.mockReturnValue('ai-offline');
    const { container } = render(<ConnectivityBadge />);
    expect(container.firstChild).toHaveClass('sv-conn-ai');
  });

  it('applies custom className', function() {
    mockUseAppStore.mockReturnValue('online');
    const { container } = render(<ConnectivityBadge className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('has sv-conn-badge class', function() {
    mockUseAppStore.mockReturnValue('online');
    const { container } = render(<ConnectivityBadge />);
    expect(container.firstChild).toHaveClass('sv-conn-badge');
  });
});



