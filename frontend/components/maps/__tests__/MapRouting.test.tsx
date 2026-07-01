jest.mock('maplibre-gl', function() {
  var fn = jest.fn;
  var sharedMap: Record<string, any> = {};
  var api = {
    __mapInstance: sharedMap,
    Map: fn(function() { return sharedMap }),
    NavigationControl: fn(),
    Marker: fn(),
    Popup: fn(),
    LngLatBounds: fn(function() { return { extend: fn().mockReturnThis() } }),
  };
  return { __esModule: true, default: api, ...api };
});

jest.mock('@/components/maps/map-utils', function() {
  return {
    ROUTE_SOURCE_ID: 'svai-active-route',
    ROUTE_ALT_CASING_LAYER_ID: 'svai-alt-route-casing',
    ROUTE_ALT_LINE_LAYER_ID: 'svai-alt-route-line',
    ROUTE_CASING_LAYER_ID: 'svai-active-route-casing',
    ROUTE_LINE_LAYER_ID: 'svai-active-route-line',
  };
});

import React from 'react';
import { render } from '@testing-library/react';
import maplibregl from 'maplibre-gl';
import { MapRouting } from '../MapRouting';

function freshMap() {
  var map = (maplibregl as any).Map();
  map.on = jest.fn();
  map.once = jest.fn();
  map.off = jest.fn();
  map.isStyleLoaded = jest.fn(function() { return true });
  map.getSource = jest.fn();
  map.addSource = jest.fn();
  map.removeSource = jest.fn();
  map.getLayer = jest.fn();
  map.addLayer = jest.fn();
  map.removeLayer = jest.fn();
  map.fitBounds = jest.fn();
  map.easeTo = jest.fn();
  map.getCanvas = jest.fn(function() { return { style: {} } });
  return map;
}

var PATH = [{ lat: 13.0, lon: 80.0 }, { lat: 13.1, lon: 80.1 }];

function renderRouting(props: Record<string, any> = {}) {
  return render(React.createElement(MapRouting, Object.assign({
    map: freshMap(),
    route: null,
    alternativeRoutes: [],
    center: [13.0, 80.0] as [number, number],
    zoom: 13,
    styleRevision: 0,
  }, props)));
}

describe('MapRouting', function() {
  beforeEach(function() { jest.clearAllMocks(); });

  it('renders null', function() {
    var { container } = renderRouting();
    expect(container.innerHTML).toBe('');
  });

  it('adds route layers when route has path', function() {
    var map = freshMap();
    map.getSource.mockReturnValue(undefined);
    map.getLayer.mockReturnValue(undefined);
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    expect(map.addSource).toHaveBeenCalledWith('svai-active-route', expect.any(Object));
    expect(map.addLayer).toHaveBeenCalled();
  });

  it('removes route layers when route has no path', function() {
    var map = freshMap();
    map.getSource.mockReturnValue({});
    map.getLayer.mockReturnValue({});
    render(React.createElement(MapRouting, {
      map, route: { path: [] }, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    expect(map.removeLayer).toHaveBeenCalled();
    expect(map.removeSource).toHaveBeenCalled();
  });

  it('updates existing route source via setData', function() {
    var setData = jest.fn();
    var map = freshMap();
    map.getSource.mockReturnValue({ setData });
    map.getLayer.mockReturnValue({});
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    expect(setData).toHaveBeenCalled();
  });

  it('calls easeTo for center mode', function() {
    var map = freshMap();
    render(React.createElement(MapRouting, {
      map, route: null, center: [13.0, 80.0] as [number, number], zoom: 14, styleRevision: 0,
    }));
    expect(map.easeTo).toHaveBeenCalledWith(expect.objectContaining({ zoom: 14 }));
  });

  it('calls fitBounds for fit viewportMode', function() {
    var map = freshMap();
    map.isStyleLoaded.mockReturnValue(true);
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0, viewportMode: 'fit',
    }));
    expect(map.fitBounds).toHaveBeenCalled();
  });

  it('calls fitBounds when route has path', function() {
    var map = freshMap();
    map.isStyleLoaded.mockReturnValue(true);
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    expect(map.fitBounds).toHaveBeenCalled();
  });

  it('adds alternative route layers when alternativeRoutes provided', function() {
    var map = freshMap();
    map.getSource.mockReturnValue(undefined);
    map.getLayer.mockReturnValue(undefined);
    map.isStyleLoaded.mockReturnValue(true);
    var altRoutes = [{ path: [{ lat: 13.05, lon: 80.05 }, { lat: 13.15, lon: 80.15 }], routeId: 'alt1' }];
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, alternativeRoutes: altRoutes, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    expect(map.addLayer).toHaveBeenCalled();
    // Should have added 4 layers: alt-casing, alt-line, casing, line
    expect(map.addLayer.mock.calls.length).toBeGreaterThanOrEqual(4);
  });

  it('waits for style load before syncing when style not loaded', function() {
    var map = freshMap();
    map.isStyleLoaded.mockReturnValue(false);
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    expect(map.once).toHaveBeenCalledWith('load', expect.any(Function));
  });

  it('includes currentLocation and facilities in viewport bounds', function() {
    var map = freshMap();
    map.getSource.mockReturnValue({ setData: jest.fn() });
    map.getLayer.mockReturnValue({});
    map.isStyleLoaded.mockReturnValue(true);
    var currentLocation = { lat: 13.01, lon: 80.01, accuracy: 50 };
    var facilities = [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.02, 80.02] as [number, number], accentColor: 'red', distance: '1km' }];
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, currentLocation: currentLocation as any, facilities: facilities, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    expect(map.fitBounds).toHaveBeenCalled();
  });

  it('does not re-add layers if they already exist (guard)', function() {
    var map = freshMap();
    map.getSource.mockReturnValue(undefined);
    // Simulate all layers already existing
    map.getLayer.mockReturnValue(true);
    map.isStyleLoaded.mockReturnValue(true);
    render(React.createElement(MapRouting, {
      map, route: { path: PATH, routeId: 'r1' }, center: [13.0, 80.0] as [number, number], zoom: 13, styleRevision: 0,
    }));
    // Only adds source, and checks layers exist (no addLayer calls since all guards return true)
    expect(map.addSource).toHaveBeenCalled();
    expect(map.addLayer).not.toHaveBeenCalled();
  });
});
