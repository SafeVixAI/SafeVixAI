// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render } from '@testing-library/react'
import React from 'react'
import EmergencyMapInner from '../EmergencyMapInner'

var mockFacilities = [
  { id: '1', name: 'City Hospital', type: 'hospital', coords: [80.2707, 13.0827] as [number, number], accentColor: '#ff0000', distance: '2 km' },
]

describe('EmergencyMapInner', function () {
  it('renders map with facilities', function () {
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: mockFacilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with route and currentLocation', function () {
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: mockFacilities,
        route: { coordinates: [[80.2707, 13.0827]] } as any,
        currentLocation: { lat: 13.08, lon: 80.27 } as any,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with selected facility', function () {
    render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: mockFacilities,
        selectedFacilityId: '1',
      })
    )
  })

  it('renders with ambulance facility type', function () {
    var facilities = [{ ...mockFacilities[0], type: 'ambulance' }]
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with pharmacy facility type', function () {
    var facilities = [{ ...mockFacilities[0], type: 'pharmacy' }]
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with police facility type', function () {
    var facilities = [{ ...mockFacilities[0], type: 'police' }]
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with fire facility type', function () {
    var facilities = [{ ...mockFacilities[0], type: 'fire' }]
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with towing facility type', function () {
    var facilities = [{ ...mockFacilities[0], type: 'towing' }]
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with mechanic facility type', function () {
    var facilities = [{ ...mockFacilities[0], type: 'mechanic' }]
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with unknown facility type', function () {
    var facilities = [{ ...mockFacilities[0], type: 'showroom' }]
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with alternative routes', function () {
    var { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: mockFacilities,
        alternativeRoutes: [{ coordinates: [[80.2707, 13.0827], [80.28, 13.09]] }] as any,
      })
    )
    expect(container).toBeDefined()
  })
})
