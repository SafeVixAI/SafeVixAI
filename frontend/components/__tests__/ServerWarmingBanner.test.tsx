// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockStore = { serverWarming: true };

jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => selector(mockStore),
  useServerWarming: () => mockStore.serverWarming,
}));

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

jest.mock('lucide-react', function() {
  const React2 = require('react');
  return { Loader2: function() { return React2.createElement('span', { 'data-testid': 'loader-icon' }) } }
});

import { ServerWarmingBanner } from '../ui/ServerWarmingBanner';

describe('ServerWarmingBanner', function() {
  it('renders connecting message', function() {
    render(<ServerWarmingBanner />);
    expect(screen.getByText(/Connecting/)).toBeInTheDocument();
  });

  it('shows estimated wait time', function() {
    render(<ServerWarmingBanner />);
    expect(screen.getByText(/30 seconds/)).toBeInTheDocument();
  });

  it('has role status', function() {
    render(<ServerWarmingBanner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders spinner icon', function() {
    render(<ServerWarmingBanner />);
    expect(screen.getByTestId('loader-icon')).toBeInTheDocument();
  });

  it('has warming styling classes', function() {
    const { container } = render(<ServerWarmingBanner />);
    expect(container.firstChild).toHaveClass('fixed');
    expect(container.firstChild).toHaveClass('rounded-full');
    expect(container.firstChild).toHaveClass('shadow-2xl');
  });

  it('does not render when serverWarming is false', function() {
    mockStore.serverWarming = false;
    const { container } = render(<ServerWarmingBanner />);
    expect(container.firstChild).toBeNull();
    mockStore.serverWarming = true;
  });

  it('calls gsap.fromTo when serverWarming is true', function() {
    mockStore.serverWarming = true;
    render(<ServerWarmingBanner />);
    const gsapMock = require('@/lib/gsap');
    expect(gsapMock.gsap.fromTo).toHaveBeenCalled();
  });

  it('calls gsap.to onComplete when serverWarming transitions to false', function() {
    mockStore.serverWarming = true;
    const { rerender } = render(<ServerWarmingBanner />);
    mockStore.serverWarming = false;
    rerender(<ServerWarmingBanner />);
    const gsapMock = require('@/lib/gsap');
    expect(gsapMock.gsap.to).toHaveBeenCalled();
  });
});

