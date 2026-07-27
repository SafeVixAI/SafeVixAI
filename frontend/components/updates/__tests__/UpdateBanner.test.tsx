// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/api/update-api', function() { return { checkForUpdates: function() { return Promise.resolve({ latest_version: '1.1.0', update_available: true, is_mandatory: false, is_security: false, last_checked_at: '2026-07-27T00:00:00Z', current_version: '1.0.0' }) }, retryOperation: function() { return Promise.resolve() }, restartApplication: function() { return Promise.resolve() }, subscribeToDownloadProgress: function() { return function() {} }, fetchUpdateSettings: function() { return Promise.resolve({}) }, fetchChannels: function() { return Promise.resolve([]) }, fetchUpdateHistory: function() { return Promise.resolve({ installations: [] }) }, updateUpdateSettings: function() { return Promise.resolve({}) }, updatePublicKey: function() { return Promise.resolve({}) } } })

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

  test('does not show Update Now when no update available', function () {
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
    render(<UpdateBanner />);
    expect(screen.queryByText('Update Now')).toBeNull();
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

test('has Update Now button that sets downloading status', async function () {
  render(<UpdateBanner />);
  const btn = await screen.findByText('Update Now');
  fireEvent.click(btn);
  expect(useAppStore.getState().updateInfo.status).toBe('downloading');
});
});
