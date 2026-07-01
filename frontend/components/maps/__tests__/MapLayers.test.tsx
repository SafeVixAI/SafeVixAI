jest.mock('maplibre-gl', function() {
  var fn = jest.fn;
  var sharedMap: Record<string, any> = {};
  var api = {
    __mapInstance: sharedMap,
    Map: fn(function() { return sharedMap }),
    NavigationControl: fn(),
    Marker: fn(),
    Popup: fn(),
    LngLatBounds: fn(),
  };
  return { __esModule: true, default: api, ...api };
});

var storeState = { showTraffic: false, showSafeSpaces: false, showHazardHeatmap: false, setShowSafeSpaces: function() {} };
jest.mock('@/lib/store', function() {
  var fn: any = function(sel?: any) { return typeof sel === 'function' ? sel(storeState) : storeState; };
  fn.getState = function() { return storeState; };
  return {
    useAppStore: fn,
  };
});

jest.mock('@/lib/traffic-layer', function() {
  return { addTrafficLayer: jest.fn(), toggleTrafficLayer: jest.fn() };
});

jest.mock('@/lib/safe-spaces-layer', function() {
  return { addSafeSpacesLayer: jest.fn().mockResolvedValue(undefined) };
});

jest.mock('@/lib/client-logger', function() {
  return { logClientError: jest.fn() };
});

jest.mock('@/components/maps/map-utils', function() {
  return {
    buildAccuracyFeature: function() { return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [] } }; },
    buildFacilityCollection: function() { return { type: 'FeatureCollection', features: [] }; },
    buildPopupContent: function() { return document.createElement('div'); },
    ACCURACY_SOURCE_ID: 'svai-current-location-accuracy',
    ACCURACY_FILL_LAYER_ID: 'svai-current-location-accuracy-fill',
    ACCURACY_LINE_LAYER_ID: 'svai-current-location-accuracy-line',
    FACILITY_SOURCE_ID: 'svai-facilities',
    FACILITY_CLUSTER_LAYER_ID: 'svai-facility-clusters',
    FACILITY_CLUSTER_COUNT_LAYER_ID: 'svai-facility-cluster-count',
    FACILITY_UNCLUSTERED_LAYER_ID: 'svai-facility-points',
    FACILITY_SELECTED_LAYER_ID: 'svai-facility-selected',
    HEATMAP_SOURCE_ID: 'svai-heatmap-source',
    HEATMAP_LAYER_ID: 'svai-heatmap-layer',
  };
});

import React from 'react';
import { render } from '@testing-library/react';
import { MapLayers } from '../MapLayers';

function getMap() { return (require('maplibre-gl') as any).Map(); }

function setupMap() {
  var map = getMap();
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
  map.setLayoutProperty = jest.fn();
  map.easeTo = jest.fn();
  var canvasStyle: Record<string, string> = {};
  map.getCanvas = jest.fn(function() { return { style: canvasStyle } });
  map.getCenter = jest.fn(function() { return { lat: 13, lng: 80 } });
  map.getZoom = jest.fn(function() { return 12 });
  return map;
}

function renderLayers(props: Record<string, any> = {}) {
  return render(React.createElement(MapLayers, Object.assign({
    map: setupMap(),
    styleRevision: 0,
    currentLocation: null,
    facilities: [],
    issues: [],
    selectedFacilityId: null,
  }, props)));
}

describe('MapLayers', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    storeState.showTraffic = false;
    storeState.showSafeSpaces = false;
    storeState.showHazardHeatmap = false;
  });

  it('renders null', function() {
    var { container } = renderLayers();
    expect(container.innerHTML).toBe('');
  });

  describe('accuracy overlay', function() {
    it('removes accuracy layers when no accuracy provided', function() {
      var map = setupMap();
      map.getLayer.mockReturnValue({});
      map.getSource.mockReturnValue({ setData: jest.fn() });
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, currentLocation: {},
      }));
      expect(map.removeLayer).toHaveBeenCalled();
      expect(map.removeSource).toHaveBeenCalled();
    });

    it('adds accuracy layers when accuracy is provided', function() {
      var map = setupMap();
      map.getLayer.mockReturnValue(undefined);
      map.getSource.mockImplementation(function(id: string) {
        if (id === 'svai-current-location-accuracy') return undefined;
        return { setData: jest.fn() };
      });
      render(React.createElement(MapLayers, {
        map, styleRevision: 0,
        currentLocation: { lat: 13.0, lon: 80.0, accuracy: 50 },
      }));
      expect(map.addSource).toHaveBeenCalledWith('svai-current-location-accuracy', expect.any(Object));
      expect(map.addLayer).toHaveBeenCalled();
    });
  });

  describe('facility layers', function() {
    it('adds facility source with clustering when no source exists', function() {
      var map = setupMap();
      map.getSource.mockReturnValue(undefined);
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0,
        facilities: [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }],
      }));
      expect(map.addSource).toHaveBeenCalledWith('svai-facilities', expect.objectContaining({ cluster: true }));
    });
  });

  describe('traffic layer', function() {
    it('toggles traffic layer per showTraffic state', function() {
      renderLayers();
      var traffic = require('@/lib/traffic-layer');
      expect(traffic.toggleTrafficLayer).toHaveBeenCalled();
    });
  });

  describe('issue layers with issues', function() {
    it('renders without crashing when issues are provided', function() {
      var map = setupMap();
      map.getSource.mockReturnValue(undefined);
      map.getLayer.mockReturnValue(undefined);
      var { container } = render(React.createElement(MapLayers, {
        map, styleRevision: 0,
        currentLocation: null,
        facilities: [],
        issues: [{ id: 'i1', title: 'Pothole', lat: 13.0, lon: 80.0, severity: 'high' as const, category: 'pothole' as const }],
      }));
      expect(container.innerHTML).toBe('');
    });
  });

  describe('style revision change', function() {
    it('re-renders when styleRevision increments', function() {
      var map = setupMap();
      map.getSource.mockReturnValue(undefined);
      map.getLayer.mockReturnValue(undefined);
      var { rerender, container } = render(React.createElement(MapLayers, {
        map, styleRevision: 0,
        currentLocation: {},
        facilities: [],
        issues: [],
      }));
      rerender(React.createElement(MapLayers, {
        map, styleRevision: 1,
        currentLocation: {},
        facilities: [],
        issues: [],
      }));
      expect(container).toBeDefined();
    });
  });

  describe('style not loaded', function() {
    it('calls map.once(load) when style is not loaded', function() {
      var map = setupMap();
      map.isStyleLoaded = jest.fn(function() { return false });
      map.once = jest.fn();
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, currentLocation: { lat: 13, lon: 80, accuracy: 50 },
      }));
      expect(map.once).toHaveBeenCalledWith('load', expect.any(Function));
    });
  });

  describe('heatmap layer', function() {
    it('adds heatmap source and layer when showHazardHeatmap is true with issues', function() {
      storeState.showHazardHeatmap = true;
      var map = setupMap();
      map.getSource.mockReturnValue(undefined);
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [], currentLocation: null,
        issues: [{ id: 'i1', title: 'Pothole', lat: 13.0, lon: 80.0, severity: 'high' as const, category: 'pothole' as const, coords: [13, 80] as [number, number] }],
      }));
      expect(map.addSource).toHaveBeenCalledWith('svai-heatmap-source', expect.any(Object));
    });

    it('removes heatmap when showHazardHeatmap turns off', function() {
      storeState.showHazardHeatmap = false;
      var map = setupMap();
      map.getSource.mockReturnValue({ setData: jest.fn() });
      map.getLayer.mockReturnValue({});
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [], currentLocation: null,
        issues: [{ id: 'i1', title: 'Pothole', lat: 13.0, lon: 80.0, severity: 'high' as const, category: 'pothole' as const, coords: [13, 80] as [number, number] }],
      }));
      expect(map.removeLayer).toHaveBeenCalled();
    });
  });

  describe('safe spaces layer', function() {
    it('adds safe spaces layer when showSafeSpaces is true', function() {
      storeState.showSafeSpaces = true;
      storeState.showHazardHeatmap = false;
      storeState.showTraffic = false;
      var map = setupMap();
      map.getSource.mockReturnValue(undefined);
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [], currentLocation: { lat: 13.0, lon: 80.0, accuracy: 50 },
      }));
      var safeSpaces = require('@/lib/safe-spaces-layer');
      expect(safeSpaces.addSafeSpacesLayer).toHaveBeenCalled();
    });
  });

  describe('traffic layer', function() {
    it('adds traffic layer when showTraffic is true', function() {
      storeState.showTraffic = true;
      var map = setupMap();
      map.getSource.mockReturnValue(undefined);
      map.getLayer = jest.fn().mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [], currentLocation: null,
      }));
      var traffic = require('@/lib/traffic-layer');
      expect(traffic.addTrafficLayer).toHaveBeenCalled();
    });
  });

  describe('cluster click handler', function() {
    it('expands cluster on click', function() {
      var map = setupMap();
      map.getSource = jest.fn(function() { return {
        getClusterExpansionZoom: jest.fn(function(id, cb) { cb(null, 15); }),
        setData: jest.fn(),
      }; });
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }], currentLocation: null,
      }));
      var clickCall = map.on.mock.calls.find(function(c) { return c[0] === 'click' && c[1] === 'svai-facility-clusters' });
      expect(clickCall).toBeDefined();
      var handler = clickCall[2];
      handler({ features: [{ properties: { cluster_id: 1 }, geometry: { type: 'Point', coordinates: [80.0, 13.0] } }] });
      expect(map.easeTo).toHaveBeenCalled();
    });
  });

  describe('facility click handler', function() {
    it('opens popup on facility click', function() {
      var popup = { setLngLat: jest.fn(function() { return this }), setDOMContent: jest.fn(function() { return this }), addTo: jest.fn() };
      (require('maplibre-gl').default as any).Popup = jest.fn(function() { return popup });
      var map = setupMap();
      map.getSource = jest.fn(function() { return { getClusterExpansionZoom: jest.fn(), setData: jest.fn() }; });
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }], currentLocation: null,
      }));
      var clickCall = map.on.mock.calls.find(function(c) { return c[0] === 'click' && c[1] === 'svai-facility-points' });
      expect(clickCall).toBeDefined();
      var handler = clickCall[2];
      handler({ features: [{ properties: { name: 'City Hospital', type: 'hospital', distance: '0.5 km' }, geometry: { type: 'Point', coordinates: [80.0, 13.0] } }] });
      expect(popup.setLngLat).toHaveBeenCalled();
      expect(popup.addTo).toHaveBeenCalled();
    });
  });

  describe('pointer handlers', function() {
    it('sets cursor on pointer enter', function() {
      var map = setupMap();
      map.getSource = jest.fn(function() { return { setData: jest.fn() }; });
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }], currentLocation: null,
      }));
      var enterCall = map.on.mock.calls.find(function(c) { return c[0] === 'mouseenter' && c[1] === 'svai-facility-clusters' });
      expect(enterCall).toBeDefined();
      enterCall[2]();
      expect(map.getCanvas().style.cursor).toBe('pointer');
    });

    it('clears cursor on pointer leave', function() {
      var map = setupMap();
      map.getSource = jest.fn(function() { return { setData: jest.fn() }; });
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }], currentLocation: null,
      }));
      var leaveCall = map.on.mock.calls.find(function(c) { return c[0] === 'mouseleave' && c[1] === 'svai-facility-clusters' });
      expect(leaveCall).toBeDefined();
      leaveCall[2]();
      expect(map.getCanvas().style.cursor).toBe('');
    });
  });

  describe('safe spaces error', function() {
    it('logs error and disables safe spaces on failure', function() {
      storeState.showSafeSpaces = true;
      var safeSpaces = require('@/lib/safe-spaces-layer');
      safeSpaces.addSafeSpacesLayer.mockRejectedValue(new Error('network fail'));
      var map = setupMap();
      map.getSource.mockReturnValue(undefined);
      map.getLayer.mockReturnValue(undefined);
      render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [], currentLocation: { lat: 13.0, lon: 80.0, accuracy: 50 },
      }));
      // Wait for promise rejection
      return new Promise(function(r) { setTimeout(r, 10) }).then(function() {
        var logger = require('@/lib/client-logger');
        expect(logger.logClientError).toHaveBeenCalled();
      });
    });
  });

  describe('safe spaces visibility toggle', function() {
    beforeEach(function() {
      storeState.showSafeSpaces = true;
    });

    it('toggles safe spaces visibility when showSafeSpaces changes', function() {
      var map = setupMap();
      map.getSource = jest.fn(function() { return { setData: jest.fn() }; });
      map.getLayer.mockReturnValue({});  // layers already exist
      var { rerender } = render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [], currentLocation: { lat: 13.0, lon: 80.0, accuracy: 50 },
      }));
      expect(map.setLayoutProperty).toHaveBeenCalled();
      // Toggle off
      storeState.showSafeSpaces = false;
      rerender(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [], currentLocation: { lat: 13.0, lon: 80.0, accuracy: 50 },
      }));
      expect(map.setLayoutProperty).toHaveBeenCalledWith('safe-spaces-circles', 'visibility', 'none');
    });
  });

  describe('facility handlers with style not loaded', function() {
    it('binds handlers via map.once(load) when style not loaded', function() {
      var map = setupMap();
      map.isStyleLoaded = jest.fn(function() { return false });
      map.getSource = jest.fn(function() { return { setData: jest.fn() }; });
      map.getLayer.mockReturnValue(undefined);
      var { rerender } = render(React.createElement(MapLayers, {
        map, styleRevision: 0, facilities: [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }], currentLocation: null,
      }));
      // Effect deferred to once('load')
      expect(map.once).toHaveBeenCalledWith('load', expect.any(Function));
      // Now trigger the load callback and re-render with style loaded
      map.isStyleLoaded = jest.fn(function() { return true });
      var loadCb = map.once.mock.calls.find(function(c) { return c[0] === 'load'; });
      if (loadCb) { loadCb[1](); }
      rerender(React.createElement(MapLayers, {
        map, styleRevision: 1, facilities: [{ id: 'f1', name: 'Hosp', type: 'hospital', coords: [13.0, 80.0], accentColor: '#00c896' }], currentLocation: null,
      }));
      expect(map.on).toHaveBeenCalledWith('click', 'svai-facility-clusters', expect.any(Function));
    });
  });
});
