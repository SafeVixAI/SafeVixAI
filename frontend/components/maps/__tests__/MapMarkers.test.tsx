jest.mock('maplibre-gl', function() {
  var fn = jest.fn;
  var sharedMap: Record<string, any> = {};
  var api = {
    __mapInstance: sharedMap,
    Map: fn(function() { return sharedMap }),
    NavigationControl: fn(),
    Marker: fn(function() {
      return {
        setLngLat: fn().mockReturnThis(),
        setPopup: fn().mockReturnThis(),
        addTo: fn().mockReturnThis(),
        remove: fn(),
      };
    }),
    Popup: fn(function() {
      return {
        setLngLat: fn().mockReturnThis(),
        setHTML: fn().mockReturnThis(),
        setDOMContent: fn().mockReturnThis(),
        addTo: fn().mockReturnThis(),
        remove: fn(),
      };
    }),
    LngLatBounds: fn(function() { return { extend: fn().mockReturnThis() } }),
  };
  return { __esModule: true, default: api, ...api };
});

jest.mock('@/components/maps/map-utils', function() {
  return {
    buildMarkerElement: function() {
      var el = document.createElement('div');
      el.setAttribute('role', 'img');
      return el;
    },
    buildPopupContent: function() { return document.createElement('div'); },
    iconForType: function(_t: string) { return 'H'; },
    ACCURACY_SOURCE_ID: 'svai-current-location-accuracy',
    ACCURACY_FILL_LAYER_ID: 'svai-current-location-accuracy-fill',
    ACCURACY_LINE_LAYER_ID: 'svai-current-location-accuracy-line',
    ROUTE_SOURCE_ID: 'svai-active-route',
    ROUTE_ALT_CASING_LAYER_ID: 'svai-alt-route-casing',
    ROUTE_ALT_LINE_LAYER_ID: 'svai-alt-route-line',
    ROUTE_CASING_LAYER_ID: 'svai-active-route-casing',
    ROUTE_LINE_LAYER_ID: 'svai-active-route-line',
    FACILITY_SOURCE_ID: 'svai-facilities',
    FACILITY_CLUSTER_LAYER_ID: 'svai-facility-clusters',
    FACILITY_CLUSTER_COUNT_LAYER_ID: 'svai-facility-cluster-count',
    FACILITY_UNCLUSTERED_LAYER_ID: 'svai-facility-points',
    FACILITY_SELECTED_LAYER_ID: 'svai-facility-selected',
    HEATMAP_SOURCE_ID: 'svai-heatmap-source',
    HEATMAP_LAYER_ID: 'svai-heatmap-layer',
    buildAccuracyFeature: function() { return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [] } }; },
    buildFacilityCollection: function() { return { type: 'FeatureCollection', features: [] }; },
  };
});

import React from 'react';
import { render } from '@testing-library/react';
import maplibregl from 'maplibre-gl';
import { MapMarkers } from '../MapMarkers';

function getMap() { return (maplibregl as any).__mapInstance; }

describe('MapMarkers', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    jest.useFakeTimers();
    getMap().once = jest.fn();
    getMap().on = jest.fn();
    getMap().off = jest.fn();
    getMap().flyTo = jest.fn();
    getMap().isStyleLoaded = jest.fn(function() { return true });
    getMap().getCanvas = jest.fn(function() { return { style: {} } });
    getMap().getSource = jest.fn();
  });

  afterEach(function() {
    jest.useRealTimers();
  });

  it('renders null (no DOM output)', function() {
    var { container } = render(React.createElement(MapMarkers, {
      map: getMap() as any,
      currentLocation: null,
      styleRevision: 0,
    }));
    expect(container.innerHTML).toBe('');
  });

  it('creates a current location marker with popup', function() {
    render(React.createElement(MapMarkers, {
      map: getMap() as any,
      currentLocation: { lat: 13.0827, lon: 80.2707, title: 'You', subtitle: 'Chennai', accuracy: 50 },
      styleRevision: 0,
    }));
    expect(maplibregl.Marker).toHaveBeenCalled();
    expect(maplibregl.Popup).toHaveBeenCalled();
    var markerCalls = (maplibregl.Marker as jest.Mock).mock.instances;
    expect(markerCalls.length).toBeGreaterThanOrEqual(1);
  });

  it('creates issue markers for each issue', function() {
    render(React.createElement(MapMarkers, {
      map: getMap() as any,
      issues: [
        { coords: [13.0, 80.0], label: 'Pothole', overline: 'Issue', accentColor: '#f00', icon: 'warning', description: 'Deep', roadName: 'Main Rd', status: 'open' },
        { coords: [13.1, 80.1], label: 'Crack', overline: 'Issue', accentColor: '#ff0', description: 'Long', roadName: 'Second', status: 'open' },
      ],
      styleRevision: 0,
    }));
    expect((maplibregl.Marker as jest.Mock).mock.instances.length).toBeGreaterThanOrEqual(2);
  });

  it('creates selected facility marker when selectedFacilityId matches', function() {
    render(React.createElement(MapMarkers, {
      map: getMap() as any,
      selectedFacilityId: 'fac-1',
      facilities: [{ id: 'fac-1', name: 'Hospital A', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }],
      styleRevision: 0,
    }));
    expect((maplibregl.Marker as jest.Mock).mock.instances.length).toBeGreaterThanOrEqual(1);
  });

  it('skips selected facility when coords missing', function() {
    render(React.createElement(MapMarkers, {
      map: getMap() as any,
      selectedFacilityId: 'fac-2',
      facilities: [{ id: 'fac-2', name: 'Hospital B', type: 'hospital', accentColor: '#00c896' }],
      styleRevision: 0,
    }));
    expect((maplibregl.Marker as jest.Mock).mock.instances.length).toBe(0);
  });

  it('listens for svai:fly-to custom event', function() {
    var addSpy = jest.spyOn(window, 'addEventListener');
    render(React.createElement(MapMarkers, {
      map: getMap() as any,
      styleRevision: 0,
    }));
    expect(addSpy).toHaveBeenCalledWith('svai:fly-to', expect.any(Function));
    addSpy.mockRestore();
  });

  it('calls flyTo on svai:fly-to event', function() {
    render(React.createElement(MapMarkers, {
      map: getMap() as any,
      styleRevision: 0,
    }));
    var event = new CustomEvent('svai:fly-to', { detail: { lat: 13.0, lng: 80.0 } });
    window.dispatchEvent(event);
    expect(getMap().flyTo).toHaveBeenCalledWith(expect.objectContaining({ zoom: 16 }));
  });
});
