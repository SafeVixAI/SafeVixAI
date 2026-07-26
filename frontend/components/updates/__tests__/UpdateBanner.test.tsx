// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import UpdateBanner from '../UpdateBanner';
import { useAppStore } from '@/lib/store';

beforeEach(() => {
  useAppStore.setState({
    updateInfo: {
      currentVersion: '1.0.0',
      latestVersion: '1.1.0',
      updateAvailable: true,
      channel: 'stable',
      isMandatory: false,
      isSecurity: false,
      lastCheckedAt: null,
      downloadProgress: 0,
      status: 'up-to-date',
    },
    updateBannerDismissed: false,
  });
});

describe('UpdateBanner', function () {
  test('renders when update is available', function () {
    render(<UpdateBanner />);
    expect(screen.getByText(/Update available/)).toBeTruthy();
  });

  test('shows version number', function () {
    render(<UpdateBanner />);
    expect(screen.getByText(/v1\.1\.0/)).toBeTruthy();
  });

  test('shows dismiss button for non-mandatory update', function () {
    render(<UpdateBanner />);
    expect(screen.getByLabelText('Dismiss update banner')).toBeTruthy();
  });

  test('does not show dismiss button for mandatory update', function () {
    useAppStore.setState({
      updateInfo: {
        currentVersion: '1.0.0',
        latestVersion: '2.0.0',
        updateAvailable: true,
        channel: 'stable',
        isMandatory: true,
        isSecurity: false,
        lastCheckedAt: null,
        downloadProgress: 0,
        status: 'available',
      },
    });
    render(<UpdateBanner />);
    expect(screen.queryByLabelText('Dismiss update banner')).toBeNull();
  });

  test('dismisses banner on close click', function () {
    render(<UpdateBanner />);
    fireEvent.click(screen.getByLabelText('Dismiss update banner'));
    expect(useAppStore.getState().updateBannerDismissed).toBe(true);
  });

  test('does not render when dismissed', function () {
    useAppStore.setState({ updateBannerDismissed: true });
    const { container } = render(<UpdateBanner />);
    expect(container.innerHTML).toBe('');
  });

  test('does not render when no update available', function () {
    useAppStore.setState({
      updateInfo: {
        currentVersion: '1.0.0',
        latestVersion: '1.0.0',
        updateAvailable: false,
        channel: 'stable',
        isMandatory: false,
        isSecurity: false,
        lastCheckedAt: new Date().toISOString(),
        downloadProgress: 0,
        status: 'up-to-date',
      },
    });
    const { container } = render(<UpdateBanner />);
    expect(container.innerHTML).toBe('');
  });

  test('shows security badge for security release', function () {
    useAppStore.setState({
      updateInfo: {
        currentVersion: '1.0.0',
        latestVersion: '1.1.0',
        updateAvailable: true,
        channel: 'stable',
        isMandatory: false,
        isSecurity: true,
        lastCheckedAt: null,
        downloadProgress: 0,
        status: 'available',
      },
    });
    render(<UpdateBanner />);
    expect(screen.getByText('Security')).toBeTruthy();
  });

  test('has Update Now button that sets downloading status', function () {
    render(<UpdateBanner />);
    fireEvent.click(screen.getByText('Update Now'));
    expect(useAppStore.getState().updateInfo.status).toBe('downloading');
  });
});
