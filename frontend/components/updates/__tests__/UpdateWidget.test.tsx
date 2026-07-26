// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import UpdateWidget from '../UpdateWidget';
import { useAppStore } from '@/lib/store';

beforeEach(function () {
  useAppStore.setState({
    updateInfo: {
      currentVersion: '1.0.0',
      latestVersion: null,
      updateAvailable: false,
      channel: 'stable',
      isMandatory: false,
      isSecurity: false,
      lastCheckedAt: null,
      downloadProgress: 0,
      status: 'up-to-date',
    },
  });
});

describe('UpdateWidget', function () {
  test('renders widget heading', function () {
    render(<UpdateWidget />);
    expect(screen.getByText('Updates')).toBeTruthy();
  });

  test('shows up-to-date status', function () {
    render(<UpdateWidget />);
    expect(screen.getByText('Up to date')).toBeTruthy();
  });

  test('shows current version', function () {
    render(<UpdateWidget />);
    expect(screen.getByText(/v1\.0\.0/)).toBeTruthy();
  });

  test('shows "Last checked: Never" when never checked', function () {
    render(<UpdateWidget />);
    expect(screen.getByText(/Never/)).toBeTruthy();
  });

  test('shows available update', function () {
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
        status: 'available',
      },
    });
    render(<UpdateWidget />);
    expect(screen.getByText(/v1\.1\.0 available/)).toBeTruthy();
  });

  test('shows error status', function () {
    useAppStore.setState({
      updateInfo: {
        currentVersion: '1.0.0',
        latestVersion: null,
        updateAvailable: false,
        channel: 'stable',
        isMandatory: false,
        isSecurity: false,
        lastCheckedAt: null,
        downloadProgress: 0,
        status: 'error',
      },
    });
    render(<UpdateWidget />);
    expect(screen.getByText('Check failed')).toBeTruthy();
  });

  test('shows Update Now button when update available', function () {
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
        status: 'available',
      },
    });
    render(<UpdateWidget />);
    expect(screen.getByText('Update Now')).toBeTruthy();
  });

  test('has check-now button', function () {
    render(<UpdateWidget />);
    expect(screen.getByLabelText('Check for updates')).toBeTruthy();
  });

  test('formats last checked timestamp', function () {
    useAppStore.setState({
      updateInfo: {
        currentVersion: '1.0.0',
        latestVersion: null,
        updateAvailable: false,
        channel: 'stable',
        isMandatory: false,
        isSecurity: false,
        lastCheckedAt: '2026-07-25T12:00:00.000Z',
        downloadProgress: 0,
        status: 'up-to-date',
      },
    });
    render(<UpdateWidget />);
    expect(screen.getByText((content) => content.includes('Jul'))).toBeTruthy();
  });
});
