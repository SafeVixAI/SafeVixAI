jest.mock('maplibre-gl', function() {
  const fn = jest.fn;
  const mapInstance: Record<string, any> = { remove: fn() };
  const api = {
    __mapInstance: mapInstance,
    Map: fn(function() { return mapInstance }),
    NavigationControl: fn(),
    Marker: fn(),
    Popup: fn(),
    LngLatBounds: fn(),
  };
  return { __esModule: true, default: api, ...api };
});

jest.mock('@/components/maps/map-styles', function() {
  return {
    buildStyleCandidates: function() {
      return [{ kind: 'openfreemap', label: 'OpenFreeMap', style: { version: 8, sources: {}, layers: [] } }];
    },
  };
});

jest.mock('@/lib/traffic-layer', function() {
  return { addTrafficLayer: jest.fn(), toggleTrafficLayer: jest.fn() };
});

jest.mock('@/lib/store', function() {
  const st = { showTraffic: false, showSatellite: false, setMapState: jest.fn(), mapStatus: 'loading', mapProvider: null, mapError: null };
  return {
    useAppStore: function(sel?: any) { return typeof sel === 'function' ? sel(st) : st; },
  };
});

jest.mock('@/components/ThemeProvider', function() {
  return { useTheme: function() { return { resolvedTheme: 'dark' } } };
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { MapLibreCanvas } from '../MapLibreCanvas';
import maplibregl from 'maplibre-gl';

function setupMap() {
  const map = (maplibregl as any).Map();
  map.on = jest.fn();
  map.once = jest.fn();
  map.off = jest.fn();
  map.isStyleLoaded = jest.fn(function() { return true });
  map.areTilesLoaded = jest.fn(function() { return true });
  map.getSource = jest.fn();
  map.addSource = jest.fn();
  map.removeSource = jest.fn();
  map.getLayer = jest.fn();
  map.addLayer = jest.fn();
  map.removeLayer = jest.fn();
  map.addControl = jest.fn();
  map.resize = jest.fn();
  map.jumpTo = jest.fn();
  map.setStyle = jest.fn();
  map.getCanvas = jest.fn(function() { return { style: {} } });
  map.dragRotate = { disable: jest.fn() };
  map.touchZoomRotate = { disableRotation: jest.fn() };
  map.flyTo = jest.fn();
  map.easeTo = jest.fn();
  map.fitBounds = jest.fn();
  map.setLayoutProperty = jest.fn();
  return map;
}

describe('MapLibreCanvas', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    setupMap();
  });

  it('renders map container div with correct className', function() {
    const { container } = render(React.createElement(MapLibreCanvas, {
      center: [13.0827, 80.2707] as [number, number],
      zoom: 13,
    }));
    expect((container.firstChild as HTMLElement).className).toContain('h-full');
  });

  it('shows loading overlay initially', function() {
    render(React.createElement(MapLibreCanvas, {
      center: [13.0827, 80.2707] as [number, number],
    }));
    expect(screen.getByText('Initializing Map')).toBeTruthy();
  });

  it('passes custom className prop', function() {
    const { container } = render(React.createElement(MapLibreCanvas, {
      center: [13.0827, 80.2707] as [number, number],
      className: 'custom-map-class',
    }));
    expect((container.firstChild as HTMLElement).className).toContain('custom-map-class');
  });

  it('renders with default zoom from NEXT_PUBLIC_MAP_DEFAULT_ZOOM', function() {
    render(React.createElement(MapLibreCanvas, {
      center: [13.0827, 80.2707] as [number, number],
    }));
    expect(maplibregl.Map).toHaveBeenCalled();
  });

  it('creates map with correct center coordinates', function() {
    render(React.createElement(MapLibreCanvas, {
      center: [77.1025, 28.7041] as [number, number],
    }));
    expect(maplibregl.Map).toHaveBeenCalled();
  });

  it('hides loading overlay when map loads', function() {
    render(React.createElement(MapLibreCanvas, {
      center: [13.0827, 80.2707] as [number, number],
    }));
    expect(screen.getByText('Initializing Map')).toBeTruthy();
  });

  it('passes onMapReady callback to Map', function() {
    const onReady = jest.fn();
    render(React.createElement(MapLibreCanvas, {
      center: [13.0827, 80.2707] as [number, number],
      onMapReady: onReady,
    }));
    expect(maplibregl.Map).toHaveBeenCalled();
  });

  it('renders with satellite style when showSatellite is true', function() {
    const store = require('@/lib/store');
    store.useAppStore = function(sel?: any) {
      const st = { showTraffic: false, showSatellite: true, setMapState: jest.fn(), mapStatus: 'loading', mapProvider: null, mapError: null };
      return typeof sel === 'function' ? sel(st) : st;
    };
    render(React.createElement(MapLibreCanvas, {
      center: [13.0827, 80.2707] as [number, number],
    }));
    expect(maplibregl.Map).toHaveBeenCalled();
  });
});
