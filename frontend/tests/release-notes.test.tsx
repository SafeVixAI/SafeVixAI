// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ReleaseNotesPage from '@/app/release-notes/page';

const mockFetchReleases = jest.fn();

jest.mock('@/lib/api/update-api', function () {
  return {
    fetchReleases: jest.fn(),
  };
});

jest.mock('@/components/ui/TerminalHeader', function () {
  return { TerminalHeader: function () { return React.createElement('div', { 'data-testid': 'terminal-header' }); } };
});

const releases = [
  { id: 1, version: '1.1.0', channel: 'stable', title: 'Bug fixes', is_security: false, published_at: '2026-07-01T00:00:00Z' },
  { id: 2, version: '1.2.0-beta', channel: 'beta', title: 'New features', is_security: true, published_at: '2026-07-15T00:00:00Z' },
];

describe('ReleaseNotesPage', function () {
  beforeEach(function () {
    jest.clearAllMocks();
    require('@/lib/api/update-api').fetchReleases.mockResolvedValue(releases);
  });

  it('renders page title', async function () {
    render(React.createElement(ReleaseNotesPage));
    expect(await screen.findByText('Release Notes')).toBeInTheDocument();
  });

  it('renders all channel tabs', async function () {
    render(React.createElement(ReleaseNotesPage));
    await screen.findByText('Release Notes');
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Stable')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('Nightly')).toBeInTheDocument();
  });

  it('renders release cards after loading', async function () {
    render(React.createElement(ReleaseNotesPage));
    expect(await screen.findByText('v1.1.0')).toBeInTheDocument();
    expect(await screen.findByText('v1.2.0-beta')).toBeInTheDocument();
  });

  it('shows loading state initially', function () {
    require('@/lib/api/update-api').fetchReleases.mockReturnValue(new Promise(function () {}));
    render(React.createElement(ReleaseNotesPage));
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('shows error state on fetch failure', async function () {
    require('@/lib/api/update-api').fetchReleases.mockRejectedValue(new Error('Network error'));
    render(React.createElement(ReleaseNotesPage));
    expect(await screen.findByText('Failed to load release notes')).toBeInTheDocument();
  });

  it('shows empty state when no releases', async function () {
    require('@/lib/api/update-api').fetchReleases.mockResolvedValue([]);
    render(React.createElement(ReleaseNotesPage));
    expect(await screen.findByText('No releases found')).toBeInTheDocument();
  });

  it('channel filter click calls fetchReleases with correct channel', async function () {
    render(React.createElement(ReleaseNotesPage));
    await screen.findByText('Stable');
    fireEvent.click(screen.getByText('Stable'));
    await waitFor(function () {
      expect(require('@/lib/api/update-api').fetchReleases).toHaveBeenCalledWith('stable', 20, 0);
    });
  });
});
