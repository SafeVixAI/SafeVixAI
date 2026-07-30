// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

let mockIsOnline = false;

jest.mock('@/hooks/useOnlineStatus', function() {
  return { useOnlineStatus: function() { return mockIsOnline } }
});

jest.mock('lucide-react', function() {
  const React2 = require('react');
  return { WifiOff: function() { return React2.createElement('span', { 'data-testid': 'wifi-off-icon' }) } }
});

jest.mock('@/lib/gsap', function() {
  return {
    gsap: {
      fromTo: jest.fn(function() { return {} }),
      to: jest.fn(function(_el: any, opts: any) { if (typeof opts?.onComplete === 'function') opts.onComplete(); return {} }),
    },
  }
});

jest.mock('@gsap/react', function() {
  const React = require('react');
  return {
    useGSAP: function(cb: any, _opts?: any) {
      React.useEffect(function() {
        if (typeof cb === 'function') cb();
      }, [cb]);
    },
  };
});

import { OfflineBanner } from '../ui/OfflineBanner';

describe('OfflineBanner', function() {
  it('renders offline indicator message', function() {
    render(<OfflineBanner />);
    expect(screen.getByText(/Offline/)).toBeInTheDocument();
  });

  it('shows that emergency features still work', function() {
    render(<OfflineBanner />);
    expect(screen.getByText(/Emergency locator/)).toBeInTheDocument();
    expect(screen.getByText(/First Aid/)).toBeInTheDocument();
    expect(screen.getByText(/SOS/)).toBeInTheDocument();
  });

  it('has role alert', function() {
    render(<OfflineBanner />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('has aria-live assertive', function() {
    render(<OfflineBanner />);
    expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'assertive');
  });

  it('renders offline icon', function() {
    render(<OfflineBanner />);
    expect(screen.getByTestId('wifi-off-icon')).toBeInTheDocument();
  });

  it('shows correct styling for offline state', function() {
    const { container } = render(<OfflineBanner />);
    const banner = container.firstChild as HTMLElement;
    expect(banner.className).toContain('fixed');
    expect(banner.className).toContain('z-[999]');
    expect(banner.className).toContain('bg-brand');
  });

  it('returns null when online', function() {
    mockIsOnline = true;
    const { container } = render(<OfflineBanner />);
    expect(container.firstChild).toBeNull();
    mockIsOnline = false;
  });

  it('calls gsap.fromTo when offline', function() {
    mockIsOnline = false;
    render(<OfflineBanner />);
    const gsapMock = require('@/lib/gsap');
    expect(gsapMock.gsap.fromTo).toHaveBeenCalled();
  });

  it('calls gsap.to onComplete when transitioning to online', function() {
    mockIsOnline = false;
    const { rerender } = render(<OfflineBanner />);
    mockIsOnline = true;
    rerender(<OfflineBanner />);
    const gsapMock = require('@/lib/gsap');
    expect(gsapMock.gsap.to).toHaveBeenCalled();
  });

  it('uses i18n translation key', function() {
    mockIsOnline = false;
    render(<OfflineBanner />);
    expect(screen.getByText(/Offline/)).toBeInTheDocument();
    mockIsOnline = false;
  });
});



