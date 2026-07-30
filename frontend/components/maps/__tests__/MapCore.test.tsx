import React from 'react';
import { render, screen } from '@testing-library/react';
import { MapCore } from '../MapCore';

describe('MapCore', function() {
  let divRef: React.RefObject<HTMLDivElement | null>;

  beforeEach(function() {
    divRef = { current: document.createElement('div') };
  });

  it('renders map container div with correct aria attributes', function() {
    const { container } = render(React.createElement(MapCore, {
      mapNodeRef: divRef,
      status: 'loading' as const,
      statusMessage: 'Loading map...',
    }));
    const mapDiv = container.querySelector('[role="application"]');
    expect(mapDiv).toBeTruthy();
    expect(mapDiv!.getAttribute('aria-label')).toContain('Interactive map');
  });

  it('shows loading overlay when status is loading', function() {
    render(React.createElement(MapCore, {
      mapNodeRef: divRef,
      status: 'loading' as const,
      statusMessage: 'Downloading tiles...',
    }));
    expect(screen.getByText('Initializing Map')).toBeTruthy();
    expect(screen.getByText('Downloading tiles...')).toBeTruthy();
  });

  it('shows error overlay when status is error', function() {
    render(React.createElement(MapCore, {
      mapNodeRef: divRef,
      status: 'error' as const,
      statusMessage: 'Network error',
    }));
    expect(screen.getByText('Map Offline')).toBeTruthy();
    expect(screen.getByText('Network error')).toBeTruthy();
  });

  it('hides overlay when status is ready', function() {
    render(React.createElement(MapCore, {
      mapNodeRef: divRef,
      status: 'ready' as const,
      statusMessage: 'Map ready',
    }));
    expect(screen.queryByText('Initializing Map')).toBeNull();
    expect(screen.queryByText('Map Offline')).toBeNull();
    expect(screen.queryByText('Map ready')).toBeNull();
  });

  it('ref prop is attached to the map container div', function() {
    const ref = { current: null as HTMLDivElement | null };
    render(React.createElement(MapCore, {
      mapNodeRef: ref,
      status: 'loading' as const,
      statusMessage: '',
    }));
    expect(ref.current).toBeInstanceOf(HTMLDivElement);
  });

  it('map container has tabIndex of 0', function() {
    const { container } = render(React.createElement(MapCore, {
      mapNodeRef: { current: document.createElement('div') },
      status: 'loading' as const,
      statusMessage: '',
    }));
    const mapDiv = container.querySelector('[role="application"]');
    expect(mapDiv!.getAttribute('tabindex')).toBe('0');
  });

  it('error overlay shows Map Offline title', function() {
    render(React.createElement(MapCore, {
      mapNodeRef: { current: document.createElement('div') },
      status: 'error' as const,
      statusMessage: 'Connection failed',
    }));
    expect(screen.getByText('Map Offline')).toBeInTheDocument()
    expect(screen.queryByText('Initializing Map')).not.toBeInTheDocument()
  });

  it('loading overlay shows Initializing Map title', function() {
    render(React.createElement(MapCore, {
      mapNodeRef: { current: document.createElement('div') },
      status: 'loading' as const,
      statusMessage: 'Downloading...',
    }));
    expect(screen.getByText('Initializing Map')).toBeInTheDocument()
    expect(screen.queryByText('Map Offline')).not.toBeInTheDocument()
  });

  it('ready status hides both loading and error overlays', function() {
    render(React.createElement(MapCore, {
      mapNodeRef: { current: document.createElement('div') },
      status: 'ready' as const,
      statusMessage: 'All good',
    }));
    expect(screen.queryByText('Initializing Map')).toBeNull()
    expect(screen.queryByText('Map Offline')).toBeNull()
  });
});
