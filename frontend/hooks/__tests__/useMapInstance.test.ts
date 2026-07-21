// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/traffic-layer', () => ({
  addTrafficLayer: jest.fn(),
  toggleTrafficLayer: jest.fn(),
}))

jest.mock('@/lib/store', () => {
  var storeState = {
    mapStatus: 'loading',
    mapProvider: 'openfreemap',
    mapError: null,
    setMapState: jest.fn(),
  }
  return {
    useAppStore: function(selector) {
      if (typeof selector === 'function') return selector(storeState)
      return storeState
    },
  }
})

jest.mock('@/components/maps/map-styles', () => ({
  buildStyleCandidates: function() {
    return [{ kind: 'openfreemap', label: 'OpenFreeMap', style: { version: 8, sources: {}, layers: [] } }]
  },
}))

import { render, screen, act } from '@testing-library/react'
import React from 'react'
import maplibregl from 'maplibre-gl'

jest.mock('maplibre-gl', () => {
  var fn = jest.fn
  var mapInstance = {
    addControl: fn(),
    dragRotate: { disable: fn() },
    touchZoomRotate: { disableRotation: fn() },
    once: fn(),
    on: fn(),
    off: fn(),
    remove: fn(),
    resize: fn(),
    jumpTo: fn(),
    flyTo: fn(),
    setStyle: fn(),
    setCenter: fn(),
    setZoom: fn(),
    isStyleLoaded: fn(function() { return true }),
    areTilesLoaded: fn(function() { return true }),
    getSource: fn(),
    addSource: fn(),
    removeSource: fn(),
    getLayer: fn(),
    addLayer: fn(),
    removeLayer: fn(),
    setLayoutProperty: fn(),
    getCenter: fn(function() { return { lat: 13, lng: 80 } }),
    getZoom: fn(function() { return 12 }),
    getBounds: fn(function() { return { getNorth: function() { return 1 }, getSouth: function() { return -1 }, getEast: function() { return 1 }, getWest: function() { return -1 } } }),
    fitBounds: fn(),
    getCanvas: fn(function() { return { style: {} } }),
    loaded: fn(function() { return true }),
    project: fn(function() { return { x: 0, y: 0 } }),
    unproject: fn(function() { return { lat: 0, lng: 0 } }),
    easeTo: fn(),
  }
  var api = {
    __mapInstance: mapInstance,
    Map: fn(function() { return mapInstance }),
    NavigationControl: fn(),
    Marker: fn(function() {
      return {
        setLngLat: fn().mockReturnThis(),
        setPopup: fn().mockReturnThis(),
        addTo: fn().mockReturnThis(),
        remove: fn(),
        getElement: fn(function() { return document.createElement('div') }),
      }
    }),
    Popup: fn(function() {
      return {
        setLngLat: fn().mockReturnThis(),
        setHTML: fn().mockReturnThis(),
        addTo: fn().mockReturnThis(),
        remove: fn(),
        setDOMContent: fn().mockReturnThis(),
      }
    }),
    LngLatBounds: fn(function() {
      return { extend: fn().mockReturnThis() }
    }),
  }
  return { __esModule: true, default: api, ...api }
})

beforeEach(function() {
  jest.clearAllMocks()
})

function MapTestComponent(props: any) {
  var hook = require('../useMapInstance').useMapInstance({
    center: props.center || [13.0827, 80.2707],
    zoom: props.zoom || 12,
    resolvedTheme: props.resolvedTheme || 'dark',
    showSatellite: props.showSatellite || false,
    showTraffic: props.showTraffic || false,
    navigationPosition: props.navigationPosition || 'bottom-left',
  })
  return React.createElement('div', {
    ref: hook.mapNodeRef,
    'data-testid': 'map-container',
    'data-status': hook.status,
    'data-message': hook.statusMessage,
  })
}

function getMapInstance() { return (maplibregl as any).__mapInstance }

describe('useMapInstance', function() {
  it('renders with loading status', function() {
    render(React.createElement(MapTestComponent))
    var el = screen.getByTestId('map-container')
    expect(el).toBeTruthy()
    expect(el.getAttribute('data-status')).toBe('loading')
  })

  it('creates Map with correct zoom and constraints', function() {
    render(React.createElement(MapTestComponent, { zoom: 14 }))
    expect(maplibregl.Map).toHaveBeenCalled()
    var args = (maplibregl.Map as jest.Mock).mock.calls[0][0]
    expect(args.zoom).toBe(14)
    expect(args.maxZoom).toBe(18)
    expect(args.minZoom).toBe(3)
    expect(args.renderWorldCopies).toBe(false)
  })

  it('calls once("load") and on events on the map', function() {
    render(React.createElement(MapTestComponent))
    var map = getMapInstance()
    expect(map.once).toHaveBeenCalledWith('load', expect.any(Function))
    expect(map.on).toHaveBeenCalledWith('idle', expect.any(Function))
    expect(map.on).toHaveBeenCalledWith('error', expect.any(Function))
    expect(map.on).toHaveBeenCalledWith('styleimagemissing', expect.any(Function))
  })

  it('adds NavigationControl and disables rotations', function() {
    render(React.createElement(MapTestComponent))
    expect(maplibregl.NavigationControl).toHaveBeenCalledWith({ showCompass: false, visualizePitch: false })
    var map = getMapInstance()
    expect(map.dragRotate.disable).toHaveBeenCalled()
    expect(map.touchZoomRotate.disableRotation).toHaveBeenCalled()
  })

  it('adds traffic layer on load and toggles per showTraffic', function() {
    render(React.createElement(MapTestComponent, { showTraffic: true }))
    var map = getMapInstance()
    var loadHandler = map.once.mock.calls.find(function(c) { return c[0] === 'load' })?.[1]
    loadHandler()
    var trafficLayer = require('@/lib/traffic-layer')
    expect(trafficLayer.addTrafficLayer).toHaveBeenCalled()
    expect(trafficLayer.toggleTrafficLayer).toHaveBeenCalled()
  })

  it('transitions to ready on idle when style and tiles loaded', function() {
    render(React.createElement(MapTestComponent))
    var map = getMapInstance()
    map.isStyleLoaded.mockReturnValue(true)
    map.areTilesLoaded.mockReturnValue(true)
    var idleHandler = map.on.mock.calls.find(function(c) { return c[0] === 'idle' })?.[1]
    act(function() { idleHandler() })
    expect(screen.getByTestId('map-container').getAttribute('data-status')).toBe('ready')
  })

  it('sets error after 12s timeout when style not loaded', function() {
    jest.useFakeTimers()
    var map = getMapInstance()
    map.isStyleLoaded.mockReturnValue(false)
    map.areTilesLoaded.mockReturnValue(false)
    render(React.createElement(MapTestComponent))
    act(function() { jest.advanceTimersByTime(12000) })
    expect(screen.getByTestId('map-container').getAttribute('data-status')).toBe('error')
  })

  it('registers resize listener and cleans up on unmount', function() {
    var addSpy = jest.spyOn(window, 'addEventListener')
    var removeSpy = jest.spyOn(window, 'removeEventListener')
    render(React.createElement(MapTestComponent))
    expect(addSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    var instance = render(React.createElement(MapTestComponent))
    instance.unmount()
    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    addSpy.mockRestore()
    removeSpy.mockRestore()
  })

  it('does not create Map when mapNodeRef is null', function() {
    require('@testing-library/react').renderHook(function() {
      return require('../useMapInstance').useMapInstance({ center: [13.0827, 80.2707], zoom: 12, resolvedTheme: 'dark', showSatellite: false, showTraffic: false })
    })
    expect(maplibregl.Map).not.toHaveBeenCalled()
  })

  it('returns styleRevision', function() {
    var result = require('@testing-library/react').renderHook(function() {
      return require('../useMapInstance').useMapInstance({ center: [13.0827, 80.2707], zoom: 12, resolvedTheme: 'dark', showSatellite: false, showTraffic: false })
    }).result
    expect(typeof result.current.styleRevision).toBe('number')
  })

  it('resizes and jumps to center on load event', function() {
    render(React.createElement(MapTestComponent))
    var map = getMapInstance()
    var loadHandler = map.once.mock.calls.find(function(c) { return c[0] === 'load' })?.[1]
    loadHandler()
    expect(map.resize).toHaveBeenCalled()
    expect(map.jumpTo).toHaveBeenCalled()
  })

  it('switches style when theme changes after map is ready', function() {
    var { rerender } = render(React.createElement(MapTestComponent, { resolvedTheme: 'dark' }))
    var map = getMapInstance()
    map.isStyleLoaded.mockReturnValue(true)
    rerender(React.createElement(MapTestComponent, { resolvedTheme: 'light' }))
    expect(map.setStyle).toHaveBeenCalled()
  })
})
