// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('lucide-react', () => ({
  X: () => <span data-testid="x-icon" />,
}));

jest.mock('@gsap/react', () => ({
  useGSAP: jest.fn(function(cb) { if (typeof cb === 'function') cb() }),
}));

jest.mock('@/lib/gsap', () => ({
  gsap: {
    fromTo: jest.fn(() => ({})),
    to: jest.fn(() => ({})),
    globalTimeline: { timeScale: jest.fn() },
  },
}));

import { SystemStatusBar } from '../ui/SystemStatusBar';

describe('SystemStatusBar', function() {
  beforeEach(function() {
    sessionStorage.clear();
  });

  it('does not render when services are operational', async function() {
    global.fetch = jest.fn().mockResolvedValue({ ok: true });
    render(<SystemStatusBar />);
    await act(async () => {
      await new Promise((r) => setTimeout(r, 100));
    });
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('renders degraded status when one service is down', async function() {
    global.fetch = jest.fn()
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: true });
    render(<SystemStatusBar />);
    const statusEl = await screen.findByRole('status');
    expect(statusEl).toBeInTheDocument();
  });

  it('renders down status when all services are down', async function() {
    global.fetch = jest.fn().mockRejectedValue(new Error('network error'));
    render(<SystemStatusBar />);
    expect(await screen.findByText(/waking up/i)).toBeInTheDocument();
  });

  it('shows connection status message', async function() {
    global.fetch = jest.fn().mockRejectedValue(new Error('network error'));
    render(<SystemStatusBar />);
    expect(await screen.findByText(/SafeVixAI/i)).toBeInTheDocument();
  });

  it('has dismiss button', async function() {
    global.fetch = jest.fn().mockRejectedValue(new Error('network error'));
    render(<SystemStatusBar />);
    await screen.findByRole('status');
    expect(screen.getByLabelText('Dismiss System Status')).toBeInTheDocument();
  });

  it('saves dismiss to sessionStorage on dismiss click', async function() {
    global.fetch = jest.fn().mockRejectedValue(new Error('network error'));
    render(<SystemStatusBar />);
    await screen.findByRole('status');
    fireEvent.click(screen.getByLabelText('Dismiss System Status'));
    expect(sessionStorage.getItem('svai-status-dismissed')).toBe('true');
  });
});



