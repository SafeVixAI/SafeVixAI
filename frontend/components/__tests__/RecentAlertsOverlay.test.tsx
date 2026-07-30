// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockState: any = {
  isDesktopSidebarCollapsed: false,
  nearbyRoadIssues: [],
};
jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => selector(mockState),
}));

describe('RecentAlertsOverlay', function() {
  beforeEach(function() {
    mockState.isDesktopSidebarCollapsed = false;
    mockState.nearbyRoadIssues = [];
  });

  it('shows no alerts indicator when list is empty', async function() {
    const RecentAlertsOverlay = (await import('../dashboard/RecentAlertsOverlay')).default;
    render(<RecentAlertsOverlay />);
    expect(screen.getByText('No active alerts nearby')).toBeInTheDocument();
  });

  it('shows count of active alerts when issues exist', async function() {
    mockState.nearbyRoadIssues = [
      {
        uuid: '1',
        issueType: 'pothole',
        severity: 3,
        lat: 13.0827,
        lon: 80.2707,
        distance: 100,
        status: 'open',
        createdAt: '2026-05-25T00:00:00Z',
      },
    ];
    const RecentAlertsOverlay = (await import('../dashboard/RecentAlertsOverlay')).default;
    render(<RecentAlertsOverlay />);
    expect(screen.getByText('1 active alerts nearby')).toBeInTheDocument();
  });

  it('renders alert items with formatted issue type', async function() {
    mockState.nearbyRoadIssues = [
      {
        uuid: '1',
        issueType: 'pothole',
        severity: 3,
        lat: 13.0827,
        lon: 80.2707,
        distance: 100,
        status: 'open',
        createdAt: '2026-05-25T00:00:00Z',
      },
    ];
    const RecentAlertsOverlay = (await import('../dashboard/RecentAlertsOverlay')).default;
    render(<RecentAlertsOverlay />);
    expect(screen.getByText('Pothole')).toBeInTheDocument();
  });

  it('shows only up to 3 alert items', async function() {
    mockState.nearbyRoadIssues = [
      { uuid: '1', issueType: 'pothole', severity: 2, lat: 0, lon: 0, distance: 50, status: 'open', createdAt: '' },
      { uuid: '2', issueType: 'traffic', severity: 3, lat: 0, lon: 0, distance: 50, status: 'open', createdAt: '' },
      { uuid: '3', issueType: 'flood', severity: 4, lat: 0, lon: 0, distance: 50, status: 'open', createdAt: '' },
      { uuid: '4', issueType: 'accident', severity: 5, lat: 0, lon: 0, distance: 50, status: 'open', createdAt: '' },
    ];
    const RecentAlertsOverlay = (await import('../dashboard/RecentAlertsOverlay')).default;
    render(<RecentAlertsOverlay />);
    expect(screen.getByText('4 active alerts nearby')).toBeInTheDocument();
    expect(screen.getByText('Pothole')).toBeInTheDocument();
    expect(screen.getByText('Traffic')).toBeInTheDocument();
    expect(screen.getByText('Flood')).toBeInTheDocument();
    expect(screen.queryByText('Accident')).not.toBeInTheDocument();
  });

  it('renders correct visual for high severity alerts', async function() {
    mockState.nearbyRoadIssues = [
      {
        uuid: '1',
        issueType: 'pothole',
        severity: 5,
        lat: 13.0827,
        lon: 80.2707,
        distance: 100,
        status: 'open',
        createdAt: '2026-05-25T00:00:00Z',
      },
    ];
    const RecentAlertsOverlay = (await import('../dashboard/RecentAlertsOverlay')).default;
    const { container } = render(<RecentAlertsOverlay />);
    const alertItems = container.querySelectorAll('.snap-center');
    expect(alertItems.length).toBe(1);
  });
});



