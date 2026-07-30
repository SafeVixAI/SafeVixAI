jest.mock('@/components/maps/MapLibreCanvas', function() {
  return {
    MapLibreCanvas: function MockMapLibreCanvas(_props: any) {
      const React = require('react')
      return React.createElement('div', { 'data-testid': 'maplibre-canvas' })
    },
    MapLibreFacility: {},
    MapLibreIssue: {},
  }
})

const mockAppState = {
  gpsLocation: null as any,
  mapSearchTarget: null as any,
  nearbyServices: [] as any[],
  nearbyRoadIssues: [] as any[],
}

jest.mock('@/lib/store', function() {
  const actual = jest.requireActual('@/lib/store')
  return {
    ...actual,
    useAppStore: function(selector: any) {
      return selector(mockAppState)
    },
  }
})

import { render, screen } from '@testing-library/react'
import React from 'react'
import MapBackgroundInner from '../MapBackgroundInner'

describe('MapBackgroundInner', function() {
  beforeEach(function() {
    mockAppState.gpsLocation = null
    mockAppState.mapSearchTarget = null
    mockAppState.nearbyServices = []
    mockAppState.nearbyRoadIssues = []
  })

  it('renders map container and MapLibreCanvas', function() {
    const { container } = render(React.createElement(MapBackgroundInner))
    expect(container.querySelector('.absolute.inset-0')).toBeTruthy()
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('shows allow location prompt when no gps or search', function() {
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByText('Allow location to find hospitals near you')).toBeInTheDocument()
  })

  it('shows search area chip when mapSearchTarget is set', function() {
    mockAppState.mapSearchTarget = { lat: 13.1, lon: 80.2, label: 'Chennai', timestamp: Date.now() }
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByText(/Search area - Chennai/)).toBeInTheDocument()
  })

  it('shows approximate location warning when accuracy >= 2500', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 3000, timestamp: Date.now(), city: 'Chennai' }
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByText(/Approximate device location/)).toBeInTheDocument()
  })

  it('does not show overlay banners when gps is accurate and no search', function() {
    mockAppState.gpsLocation = { lat: 13.0827, lon: 80.2707, accuracy: 50, timestamp: Date.now(), city: 'Chennai' }
    render(React.createElement(MapBackgroundInner))
    expect(screen.queryByText('Allow location to find hospitals near you')).toBeNull()
    expect(screen.queryByText(/Search area/)).toBeNull()
    expect(screen.queryByText(/Approximate device location/)).toBeNull()
  })

  it('renders with nearby services and road issues', function() {
    mockAppState.gpsLocation = { lat: 13.0827, lon: 80.2707, accuracy: 50, timestamp: Date.now(), city: 'Chennai' }
    mockAppState.nearbyServices = [
      { id: '1', name: 'City Hospital', category: 'hospital', lat: 13.1, lon: 80.2, distance: 500, phone: '123', address: 'Main St' },
      { id: '2', name: 'Police Station', category: 'police', lat: 13.0, lon: 80.3, distance: 1200 },
    ]
    mockAppState.nearbyRoadIssues = [
      { uuid: 'i1', issueType: 'Flooding', severity: 4, lat: 13.05, lon: 80.25, distance: 800, status: 'reported', description: 'Water logging', createdAt: Date.now() },
      { uuid: 'i2', issueType: 'Traffic Jam', severity: 2, lat: 13.08, lon: 80.28, distance: 200, status: 'confirmed', roadName: 'Main Rd', createdAt: Date.now() },
    ]
    const { container } = render(React.createElement(MapBackgroundInner))
    expect(container.querySelector('.absolute.inset-0')).toBeTruthy()
  })

  it('shows search chip over gps when both exist', function() {
    mockAppState.gpsLocation = { lat: 13.0827, lon: 80.2707, accuracy: 50, timestamp: Date.now(), city: 'Chennai' }
    mockAppState.mapSearchTarget = { lat: 13.1, lon: 80.2, label: 'Mylapore', timestamp: Date.now() }
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByText(/Search area - Mylapore/)).toBeInTheDocument()
    expect(screen.queryByText('Allow location to find hospitals near you')).toBeNull()
  })

  it('renders with emergency service type', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyServices = [
      { id: '3', name: 'Fire Station', category: 'fire', lat: 13.1, lon: 80.2, distance: 1000, phone: '911' },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with ambulance service', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyServices = [
      { id: '4', name: 'Medic Ambulance', category: 'ambulance', lat: 13.1, lon: 80.2, distance: 2000 },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with puncture service (tire repair)', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyServices = [
      { id: '5', name: 'Fast Tyres', category: 'puncture', lat: 13.1, lon: 80.2, distance: 500 },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with showroom service', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyServices = [
      { id: '6', name: 'Honda Showroom', category: 'showroom', lat: 13.1, lon: 80.2, distance: 3000 },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with towing service', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyServices = [
      { id: '7', name: 'Tow Truck Co', category: 'towing', lat: 13.1, lon: 80.2, distance: 1500 },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with pharmacy service', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyServices = [
      { id: '8', name: 'MedPlus Pharmacy', category: 'pharmacy', lat: 13.1, lon: 80.2, distance: 800 },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with rain-related road issue', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyRoadIssues = [
      { uuid: 'i3', issueType: 'Heavy Rain', severity: 3, lat: 13.1, lon: 80.2, distance: 400, status: 'reported', createdAt: Date.now() },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with traffic-related road issue', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyRoadIssues = [
      { uuid: 'i4', issueType: 'Traffic Congestion', severity: 2, lat: 13.1, lon: 80.2, distance: 300, status: 'confirmed', createdAt: Date.now() },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with low severity issue (default icon)', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyRoadIssues = [
      { uuid: 'i5', issueType: 'Streetlight Out', severity: 1, lat: 13.1, lon: 80.2, distance: 600, status: 'reported', createdAt: Date.now() },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })

  it('renders with 1km+ distance (km format)', function() {
    mockAppState.gpsLocation = { lat: 13, lon: 80, accuracy: 100, timestamp: Date.now() }
    mockAppState.nearbyServices = [
      { id: '9', name: 'Far Hospital', category: 'hospital', lat: 14.0, lon: 81.0, distance: 2500 },
    ]
    render(React.createElement(MapBackgroundInner))
    expect(screen.getByTestId('maplibre-canvas')).toBeInTheDocument()
  })
})
