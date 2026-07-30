// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { act, render, waitFor } from '@testing-library/react';
import maplibregl from 'maplibre-gl';
import { toggleTrafficLayer } from '@/lib/traffic-layer';
import { useAppStore } from '@/lib/store';
import { MapLibreCanvas } from '../maps/MapLibreCanvas';

jest.mock(
  'next-themes',
  () => ({
    useTheme: () => ({ resolvedTheme: 'light' }),
  }),
  { virtual: true },
);

jest.mock('@/lib/traffic-layer', () => ({
  addTrafficLayer: jest.fn(),
  toggleTrafficLayer: jest.fn(),
}));

jest.mock('@/lib/safe-spaces-layer', () => ({
  addSafeSpacesLayer: jest.fn(async () => undefined),
}));

jest.mock('@/lib/client-logger', () => ({
  logClientError: jest.fn(),
}));

jest.mock('maplibre-gl', () => {
  const mapRemove = jest.fn();
  const markerRemove = jest.fn();
  const mapInstance = {
    addControl: jest.fn(),
    dragRotate: { disable: jest.fn() },
    touchZoomRotate: { disableRotation: jest.fn() },
    once: jest.fn((_event: string, callback: () => void) => {
      callback();
    }),
    on: jest.fn((event: string, arg1: unknown, arg2?: unknown) => {
      const callback = typeof arg1 === 'function' ? arg1 : typeof arg2 === 'function' ? arg2 : null;
      if (event === 'idle' && callback) {
        callback();
      }
    }),
    off: jest.fn(),
    remove: mapRemove,
    resize: jest.fn(),
    jumpTo: jest.fn(),
    flyTo: jest.fn(),
    setStyle: jest.fn(),
    isStyleLoaded: jest.fn(() => true),
    areTilesLoaded: jest.fn(() => true),
    getSource: jest.fn(() => undefined),
    addSource: jest.fn(),
    removeSource: jest.fn(),
    getLayer: jest.fn(() => undefined),
    addLayer: jest.fn(),
    removeLayer: jest.fn(),
    setLayoutProperty: jest.fn(),
    easeTo: jest.fn(),
    fitBounds: jest.fn(),
    getCanvas: jest.fn(() => ({ style: { cursor: '' } })),
  };

  class MockMarker {
    setLngLat() {
      return this;
    }
    setPopup() {
      return this;
    }
    addTo() {
      return this;
    }
    remove = markerRemove;
  }

  class MockPopup {
    setDOMContent() {
      return this;
    }
    setLngLat() {
      return this;
    }
    addTo() {
      return this;
    }
  }

  class MockLngLatBounds {
    extend() {
      return this;
    }
  }

  const api = {
    __mapRemove: mapRemove,
    __markerRemove: markerRemove,
    __mapInstance: mapInstance,
    Map: jest.fn(() => mapInstance),
    NavigationControl: jest.fn(),
    Marker: MockMarker,
    Popup: MockPopup,
    LngLatBounds: MockLngLatBounds,
  };

  return {
    __esModule: true,
    default: api,
    ...api,
  };
});

describe('MapLibreCanvas', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    useAppStore.setState({
      mapStatus: 'loading',
      mapProvider: null,
      mapError: null,
    });
  });

  it('removes the map on unmount without owning GPS tracking', async function() {
    const { unmount } = render(
      <MapLibreCanvas center={[13.0827, 80.2707]} currentLocation={null} />
    );

    const maplibreMock = maplibregl as typeof maplibregl & {
      __mapRemove: jest.Mock;
      Map: jest.Mock;
    };

    await waitFor(() => expect(maplibreMock.Map).toHaveBeenCalledTimes(1));

    unmount();

    expect(maplibreMock.__mapRemove).toHaveBeenCalledTimes(1);
  });

  it('keeps the same map instance when the center changes', async function() {
    const { rerender } = render(
      <MapLibreCanvas center={[13.0827, 80.2707]} currentLocation={null} />
    );

    const maplibreMock = maplibregl as typeof maplibregl & {
      __mapInstance: { easeTo: jest.Mock };
      Map: jest.Mock;
    };

    await waitFor(() => expect(maplibreMock.Map).toHaveBeenCalledTimes(1));

    rerender(<MapLibreCanvas center={[12.9716, 77.5946]} currentLocation={null} />);

    await waitFor(() => expect(maplibreMock.__mapInstance.easeTo).toHaveBeenCalled());
    expect(maplibreMock.Map).toHaveBeenCalledTimes(1);
  });

  it('keeps the same map instance when facilities update', async function() {
    const { rerender } = render(
      <MapLibreCanvas center={[13.0827, 80.2707]} currentLocation={null} facilities={[]} />
    );

    const maplibreMock = maplibregl as typeof maplibregl & {
      Map: jest.Mock;
    };

    await waitFor(() => expect(maplibreMock.Map).toHaveBeenCalledTimes(1));

    rerender(
      <MapLibreCanvas
        center={[13.0827, 80.2707]}
        currentLocation={null}
        facilities={[
          {
            id: 'hospital-1',
            name: 'City Hospital',
            coords: [13.0827, 80.2707],
            type: 'hospital',
            accentColor: '#ef4444',
          },
        ]}
      />
    );

    expect(maplibreMock.Map).toHaveBeenCalledTimes(1);
  });

  it('toggles traffic without recreating the map', async function() {
    const { rerender } = render(<MapLibreCanvas center={[13.0827, 80.2707]} currentLocation={null} />);

    const maplibreMock = maplibregl as typeof maplibregl & {
      Map: jest.Mock;
    };
    const toggleTrafficLayerMock = toggleTrafficLayer as jest.Mock;

    await act(async () => {
      useAppStore.setState({ showTraffic: true });
    });
    
    // Rerender to ensure useEffect triggers on store/revision updates
    rerender(<MapLibreCanvas center={[13.0827, 80.2707]} currentLocation={null} />);

    await waitFor(() => {
      expect(toggleTrafficLayerMock).toHaveBeenCalled();
    });
    expect(maplibreMock.Map).toHaveBeenCalledTimes(1);
  });

  it('publishes frontend map status when the style is ready', async function() {
    render(<MapLibreCanvas center={[13.0827, 80.2707]} currentLocation={null} />);

    await waitFor(() => {
      expect(useAppStore.getState().mapStatus).toBe('ready');
      expect(useAppStore.getState().mapProvider).toBeTruthy();
      expect(useAppStore.getState().mapError).toBeNull();
    });
  });
});



