// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockState = {
  userProfile: { bloodGroup: 'O+', vehicleNumber: 'TN01AB1234' },
  soundsEnabled: false,
};
jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => selector(mockState),
}));

jest.mock('@/lib/haptics', () => ({
  haptics: { sos: jest.fn(), heavy: jest.fn() },
}));

jest.mock('@/lib/sounds', () => ({
  sounds: { countdown: jest.fn() },
}));

jest.mock('../../components/crash/ProgressRing', () => ({
  ProgressRing: ({ seconds, total }: { seconds: number; total: number }) => (
    <div data-testid="progress-ring" data-seconds={seconds} data-total={total}>
      {seconds}/{total}
    </div>
  ),
}));

jest.mock('@gsap/react', () => ({
  useGSAP: (callback: any) => {
    if (typeof callback === 'function') callback();
    return {};
  },
}));

jest.mock('@/lib/gsap', () => ({
  gsap: {
    fromTo: jest.fn(() => ({})),
    to: jest.fn(() => ({})),
  },
}));

describe('CrashCountdown', function() {
  const mockOnCancel = jest.fn();
  const mockOnDispatch = jest.fn();

  beforeEach(function() {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(function() {
    jest.useRealTimers();
  });

  it('renders countdown with severity', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    expect(screen.getByText('HIGH CRASH DETECTED')).toBeInTheDocument();
  });

  it('renders countdown number', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="medium" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('renders cancel button', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="low" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    const cancelBtn = screen.getByText('I AM SAFE — CANCEL SOS');
    expect(cancelBtn).toBeInTheDocument();
  });

  it('calls onCancel when cancel button clicked', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    fireEvent.click(screen.getByText('I AM SAFE — CANCEL SOS'));
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('calls onDispatch after countdown reaches zero', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    act(() => { jest.advanceTimersByTime(21000); });
    expect(mockOnDispatch).toHaveBeenCalled();
  });

  it('has alertdialog role', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });

  it('renders user profile info', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    expect(screen.getByText('O+')).toBeInTheDocument();
    expect(screen.getByText('TN01AB1234')).toBeInTheDocument();
  });

  it('renders progress ring', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    expect(screen.getByTestId('progress-ring')).toBeInTheDocument();
  });

  it('shows countdown aria-label', async function() {
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    expect(screen.getByLabelText('20 seconds to auto SOS')).toBeInTheDocument();
  });

  it('calls haptics.sos on mount', async function() {
    const hapticsMod = require('@/lib/haptics');
    const { CrashCountdown } = await import('../crash/CrashCountdown');
    render(<CrashCountdown severity="high" onCancel={mockOnCancel} onDispatch={mockOnDispatch} />);
    expect(hapticsMod.haptics.sos).toHaveBeenCalled();
  });
});



