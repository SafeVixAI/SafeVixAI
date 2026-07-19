// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

var storeListeners = new Set()
jest.mock('@/lib/store', () => {
  var React = require('react')
  var storeState = {
    gpsError: null,
    gpsLocation: { lat: 13.0827, lon: 80.2707, accuracy: 50, timestamp: Date.now(), city: 'Chennai', state: 'Tamil Nadu' },
    nearbyServices: [],
    serviceSearchMeta: { count: 0, radiusUsed: 0, requestedRadius: 0, source: 'api' },
    connectivity: 'online',
    setMapState: jest.fn(),
  }
  return {
    useAppStore: function(selector) {
      var [, forceUpdate] = React.useState(0)
      React.useEffect(function() {
        var fn = function() { forceUpdate(function(n) { return n + 1 }) }
        storeListeners.add(fn)
        return function() { storeListeners.delete(fn) }
      }, [])
      if (typeof selector === 'function') {
        if (selector.toString().includes('useShallow')) {
          var shallow = require('zustand/react/shallow').useShallow
          return selector({ gpsError: storeState.gpsError, gpsLocation: storeState.gpsLocation, nearbyServices: storeState.nearbyServices, serviceSearchMeta: storeState.serviceSearchMeta })
        }
        return selector(storeState)
      }
      return storeState
    },
    __setStoreState: function(k, v) { storeState[k] = v; if (typeof v === 'object') { Object.assign(storeState, v) } storeListeners.forEach(function(fn) { fn() }) },
    __resetStore: function() {
      storeState.gpsError = null
      storeState.gpsLocation = { lat: 13.0827, lon: 80.2707, accuracy: 50, timestamp: Date.now(), city: 'Chennai', state: 'Tamil Nadu' }
      storeState.nearbyServices = []
      storeState.serviceSearchMeta = { count: 0, radiusUsed: 0, requestedRadius: 0, source: 'api' }
      storeListeners.forEach(function(fn) { fn() })
    },
  }
})

jest.mock('@/lib/location-utils', () => ({
  formatLocationSubtitle: function(loc) { return loc ? loc.city + ', ' + loc.state : 'Unknown' },
}))

jest.mock('@/lib/map-defaults', () => ({
  FALLBACK_MAP_CENTER: [20.5937, 78.9629],
}))

var mockFetchRoutePreview = jest.fn()
jest.mock('@/lib/api', () => ({
  fetchRoutePreview: function() { return mockFetchRoutePreview.apply(null, arguments) },
}))

var mockMinimumDeviation = 50
jest.mock('@/app/locator/locator-utils', () => ({
  mapService: function(service) {
    var typeMap = { hospital: 'Hospital', ambulance: 'Ambulance', police: 'Police', fire: 'Fire', towing: 'Towing' }
    var filterMap = { hospital: 'Hospital', ambulance: 'Hospital', pharmacy: 'Hospital', police: 'Police', fire: 'Fire', towing: 'Towing', puncture: 'Mechanic', showroom: 'Mechanic' }
    var colorMap = { hospital: '#ef4444', ambulance: '#10b981', police: '#3b82f6', fire: '#f97316', towing: '#f59e0b' }
    return {
      id: service.id, name: service.name,
      type: typeMap[service.category] || 'Mechanic',
      filterType: filterMap[service.category] || 'Mechanic',
      distance: '1.2 km', address: service.address || 'Address unavailable',
      accentColor: colorMap[service.category] || '#8b5cf6',
      coords: [service.lat, service.lon],
      phone: service.phone,
      category: service.category,
    }
  },
  formatCoverageRadius: function(d) { return d >= 1000 ? Math.round(d / 1000) + ' km' : Math.round(d) + ' m' },
  haversineMeters: function(from, to) { return 100 },
  minimumRouteDeviationMeters: function(route, location) { return mockMinimumDeviation },
  buildNavigationHref: function(origin, dest) { return 'https://maps.google.com/dir/?api=1&origin=' + origin[0] + ',' + origin[1] + '&destination=' + dest[0] + ',' + dest[1] + '&travelmode=driving' },
}))

import { renderHook, act } from '@testing-library/react'

var mockRoute = {
  routes: [
    { routeId: 'route-1', label: 'Fastest', distanceMeters: 5000, durationSeconds: 600, path: [{ lat: 13.08, lon: 80.27 }] },
    { routeId: 'route-2', label: 'Scenic', distanceMeters: 8000, durationSeconds: 900, path: [{ lat: 13.09, lon: 80.28 }] },
  ],
  selectedRouteId: 'route-1',
  rerouteThresholdMeters: 200,
}

var mockServices = [
  { id: 's1', name: 'Apollo Hospital', category: 'hospital', lat: 13.08, lon: 80.27, distance: 1200, address: 'Chennai', phone: '112', source: 'api' },
  { id: 's2', name: 'Kilpauk Police', category: 'police', lat: 13.09, lon: 80.25, distance: 2500, address: 'Chennai', phone: '100', source: 'api' },
]

describe('useLocatorSearch', function() {
  beforeEach(function() {
    mockFetchRoutePreview.mockReset()
    mockFetchRoutePreview.mockResolvedValue(mockRoute)
    var store = require('@/lib/store')
    store.__resetStore()
  })

  it('returns locating=true when no gps and no error', function() {
    var store = require('@/lib/store')
    store.__setStoreState('gpsLocation', null)
    store.__setStoreState('gpsError', null)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.locating).toBe(true)
  })

  it('returns address from gpsLocation', function() {
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.address).toContain('Chennai')
  })

  it('returns location-needed text when gps error', function() {
    var store = require('@/lib/store')
    store.__setStoreState('gpsError', 'permission denied')
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.address).toBe('Location access needed')
  })

  it('returns enable-location text when no gps', function() {
    var store = require('@/lib/store')
    store.__setStoreState('gpsLocation', null)
    store.__setStoreState('gpsError', null)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.address).toBe('Allow location to find hospitals near you')
  })

  it('uses FALLBACK_MAP_CENTER when no gps', function() {
    var store = require('@/lib/store')
    store.__setStoreState('gpsLocation', null)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.coords).toEqual([20.5937, 78.9629])
  })

  it('uses gpsLocation coords when available', function() {
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.coords).toEqual([13.0827, 80.2707])
  })

  it('maps nearbyServices to services', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.services).toHaveLength(2)
    expect(result.current.services[0].name).toBe('Apollo Hospital')
  })

  it('filters services by activeFilter', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    act(function() { result.current.setActiveFilter('Police') })
    expect(result.current.filtered).toHaveLength(1)
    expect(result.current.filtered[0].name).toBe('Kilpauk Police')
  })

  it('selects first service when filtered changes', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.selectedServiceId).toBe('s1')
    act(function() { result.current.setActiveFilter('Police') })
    expect(result.current.selectedServiceId).toBe('s2')
  })

  it('clears selection when filter yields empty', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    act(function() { result.current.setActiveFilter('Fire') })
    expect(result.current.selectedServiceId).toBeNull()
    expect(result.current.activeRoute).toBeNull()
  })

  it('handlePreviewService sets selectedServiceId and clears route', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    act(function() { result.current.handlePreviewService(result.current.services[1]) })
    expect(result.current.selectedServiceId).toBe('s2')
  })

  it('handleLocateService fetches route and sets activeRoute', async function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    expect(mockFetchRoutePreview).toHaveBeenCalledWith(expect.objectContaining({ destinationLat: 13.08, destinationLon: 80.27 }))
    expect(result.current.activeRoute).toEqual(mockRoute)
    expect(result.current.selectedRouteId).toBe('route-1')
  })

  it('handleLocateService sets error when no gps', async function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    store.__setStoreState('gpsLocation', null)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    expect(result.current.routeError).toBe('Allow location to calculate a road-aware route from your current position.')
  })

  it('handleLocateService sets routeError on fetch failure', async function() {
    mockFetchRoutePreview.mockRejectedValue(new Error('API timeout'))
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    expect(result.current.routeError).toBe('API timeout')
    expect(result.current.routeLoadingId).toBeNull()
  })

  it('handleLocateService extracts error detail from axios-like response', async function() {
    mockFetchRoutePreview.mockRejectedValue({ response: { data: { detail: 'Server overloaded' } } })
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    expect(result.current.routeError).toBe('Server overloaded')
  })

  it('handleSelectRoute updates selectedRouteId', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    act(function() { result.current.handlePreviewService(result.current.services[0]) })
    act(function() { result.current.handleSelectRoute('route-2') })
    expect(result.current.selectedRouteId).toBe('route-2')
  })

  it('computes coverageSummary from serviceSearchMeta', function() {
    var store = require('@/lib/store')
    store.__setStoreState('serviceSearchMeta', { count: 5, radiusUsed: 3000, requestedRadius: 5000, source: 'api' })
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.coverageSummary).toBe('3 km coverage')
  })

  it('computes navigationHref when gps and service available', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.navigationHref).toContain('maps.google.com')
  })

  it('returns null navigationHref when no gps', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    store.__setStoreState('gpsLocation', null)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    expect(result.current.navigationHref).toBeNull()
  })

  it('sets routeLoadingId during locate and clears after', async function() {
    var resolveRoute
    mockFetchRoutePreview.mockImplementation(function() { return new Promise(function(r) { resolveRoute = r }) })
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    var locatePromise
    act(function() { locatePromise = result.current.handleLocateService(result.current.services[0]) })
    expect(result.current.routeLoadingId).toBe('s1')
    await act(async function() { resolveRoute(mockRoute); await locatePromise })
    expect(result.current.routeLoadingId).toBeNull()
  })

  it('clears route when gpsLocation changes', function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    act(function() { result.current.handlePreviewService(result.current.services[0]) })
    act(function() { store.__setStoreState('gpsLocation', { lat: 13.10, lon: 80.30, accuracy: 30, timestamp: Date.now() }) })
    expect(result.current.activeRoute).toBeNull()
  })

  it('sets selectedRouteId from activeRoute when current routeId invalid', async function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    act(function() { result.current.handleSelectRoute('nonexistent-route') })
    expect(result.current.selectedRouteId).toBe('route-1')
  })

  it('returns default error message for non-object errors', async function() {
    mockFetchRoutePreview.mockRejectedValue('just a string')
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    expect(result.current.routeError).toBe('Unable to calculate the route right now.')
  })

  it('handlePreviewService clears active route when switching services', async function() {
    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    expect(result.current.activeRoute).toEqual(mockRoute)
    act(function() { result.current.handlePreviewService(result.current.services[1]) })
    expect(result.current.activeRoute).toBeNull()
    expect(result.current.selectedRouteId).toBeNull()
  })

  it('auto-reroutes when gps deviates above threshold', async function() {
    var originalMinimumDeviation = mockMinimumDeviation
    mockMinimumDeviation = 250
    jest.useFakeTimers()

    var store = require('@/lib/store')
    store.__setStoreState('nearbyServices', mockServices as any)
    var result = renderHook(function() { return require('../useLocatorSearch').useLocatorSearch() }).result
    await act(async function() { await result.current.handleLocateService(result.current.services[0]) })
    expect(result.current.activeRoute).toEqual(mockRoute)
    mockFetchRoutePreview.mockClear()

    jest.advanceTimersByTime(20000)

    act(function() {
      store.__setStoreState('gpsLocation', { lat: 13.12, lon: 80.35, accuracy: 30, timestamp: Date.now() })
    })

    await act(async function() { jest.runAllTimers() })
    expect(mockFetchRoutePreview).toHaveBeenCalled()

    mockMinimumDeviation = originalMinimumDeviation
    jest.useRealTimers()
  })
})

