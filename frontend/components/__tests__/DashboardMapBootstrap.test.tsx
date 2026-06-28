jest.mock('@/lib/api', function() {
  return {
    fetchNearbyServices: jest.fn(function() { return Promise.resolve({ services: [], count: 0, source: 'api', radiusUsed: 5000 }) }),
    fetchRoadIssues: jest.fn(function() { return Promise.resolve({ issues: [], count: 0, radiusUsed: 5000 }) }),
  }
})

jest.mock('@/lib/geolocation', function() {
  var mockLocation = { lat: 13.0827, lon: 80.2707, accuracy: 50 }
  return {
    useGeolocation: function() { return { location: mockLocation, error: null, refresh: jest.fn() } },
  }
})

jest.mock('@/lib/reverse-geocode', function() {
  return {
    getAddressFromGPS: jest.fn(function() { return Promise.resolve({ city: 'Chennai', state: 'Tamil Nadu', displayAddress: 'Chennai, TN' }) }),
  }
})

import { render } from '@testing-library/react'
import React from 'react'
import DashboardMapBootstrap from '../dashboard/DashboardMapBootstrap'

var mockSetFunctions = {
  setConnectivity: jest.fn(),
  setGpsLocation: jest.fn(),
  setNearbyServices: jest.fn(),
  setNearbyRoadIssues: jest.fn(),
  setServiceSearchMeta: jest.fn(),
  setRoadIssueSearchMeta: jest.fn(),
}

var mockAppState = {
  gpsLocation: null as any,
  mapSearchTarget: null as any,
  connectivity: 'online',
  serviceCategory: 'all',
  serviceRadius: 5000,
  ...mockSetFunctions,
}

jest.mock('@/lib/store', function() {
  var actual = jest.requireActual('@/lib/store')
  return {
    ...actual,
    useAppStore: function(selector: any) {
      return selector(mockAppState)
    },
  }
})

var api = require('@/lib/api')

describe('DashboardMapBootstrap', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    mockAppState.gpsLocation = null
    mockAppState.mapSearchTarget = null
    mockAppState.connectivity = 'online'
    mockAppState.serviceCategory = 'all'
    mockAppState.serviceRadius = 5000
  })

  it('renders null (no DOM output)', function() {
    var container = render(React.createElement(DashboardMapBootstrap))
    expect(container.container.innerHTML).toBe('')
  })

  it('calls fetchRoadIssues on mount with lat/lon from geolocation', function() {
    render(React.createElement(DashboardMapBootstrap))
    expect(api.fetchRoadIssues).toHaveBeenCalledTimes(1)
    var call = api.fetchRoadIssues.mock.calls[0][0]
    expect(call.lat).toBeCloseTo(13.0827, 3)
    expect(call.lon).toBeCloseTo(80.2707, 3)
  })

  it('passes limit 12 and signal to fetchRoadIssues', function() {
    render(React.createElement(DashboardMapBootstrap))
    var call = api.fetchRoadIssues.mock.calls[0][0]
    expect(call.limit).toBe(12)
    expect(call.signal).toBeDefined()
  })

  it('uses mapSearchTarget coords for fetchRoadIssues when set', function() {
    mockAppState.mapSearchTarget = { lat: 12.97, lon: 77.59, label: 'Bangalore', timestamp: Date.now() }
    render(React.createElement(DashboardMapBootstrap))
    var call = api.fetchRoadIssues.mock.calls[0][0]
    expect(call.lat).toBeCloseTo(12.97, 2)
    expect(call.lon).toBeCloseTo(77.59, 2)
  })

  it('calls fetchNearbyServices with limit 24 and signal', function() {
    render(React.createElement(DashboardMapBootstrap))
    expect(api.fetchNearbyServices).toHaveBeenCalled()
    var call = api.fetchNearbyServices.mock.calls[0][0]
    expect(call.limit).toBe(24)
    expect(call.signal).toBeDefined()
  })

  it('sets connectivity to "online" on mount', function() {
    render(React.createElement(DashboardMapBootstrap))
    expect(mockSetFunctions.setConnectivity).toHaveBeenCalledWith('online')
  })

  it('passes serviceCategory as categories when not "all"', function() {
    mockAppState.serviceCategory = 'hospital'
    render(React.createElement(DashboardMapBootstrap))
    var call = api.fetchNearbyServices.mock.calls[0][0]
    expect(call.categories).toBe('hospital')
  })

  it('fetches nearby services with first radius step', function() {
    render(React.createElement(DashboardMapBootstrap))
    var call = api.fetchNearbyServices.mock.calls[0][0]
    expect(call.radius).toBe(500)
  })

  it('fetches road issues with serviceRadius', function() {
    render(React.createElement(DashboardMapBootstrap))
    var call = api.fetchRoadIssues.mock.calls[0][0]
    expect(call.radius).toBe(5000)
  })

  it('sets connectivity even when gpsLocation is present in store', function() {
    mockAppState.gpsLocation = { lat: 13.0, lon: 80.0, accuracy: 100, timestamp: Date.now() }
    render(React.createElement(DashboardMapBootstrap))
    expect(mockSetFunctions.setConnectivity).toHaveBeenCalledWith('online')
  })

  it('uses radius=500 as first fetchNearbyServices call', function() {
    render(React.createElement(DashboardMapBootstrap))
    expect(api.fetchNearbyServices.mock.calls[0][0].radius).toBe(500)
  })
})
