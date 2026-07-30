// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render } from '@testing-library/react'
import React from 'react'
import EmergencyMapInner from '../EmergencyMapInner'

const mockFacilities = [
  { id: '1', name: 'City Hospital', type: 'hospital', coords: [80.2707, 13.0827] as [number, number], accentColor: '#ff0000', distance: '2 km' },
]

describe('EmergencyMapInner', function () {
  it('renders map with facilities', function () {
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: mockFacilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with route and currentLocation', function () {
    const { container } = render(
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
    const facilities = [{ ...mockFacilities[0], type: 'ambulance' }]
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with pharmacy facility type', function () {
    const facilities = [{ ...mockFacilities[0], type: 'pharmacy' }]
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with police facility type', function () {
    const facilities = [{ ...mockFacilities[0], type: 'police' }]
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with fire facility type', function () {
    const facilities = [{ ...mockFacilities[0], type: 'fire' }]
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with towing facility type', function () {
    const facilities = [{ ...mockFacilities[0], type: 'towing' }]
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with mechanic facility type', function () {
    const facilities = [{ ...mockFacilities[0], type: 'mechanic' }]
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with unknown facility type', function () {
    const facilities = [{ ...mockFacilities[0], type: 'showroom' }]
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: facilities,
      })
    )
    expect(container).toBeDefined()
  })

  it('renders with alternative routes', function () {
    const { container } = render(
      React.createElement(EmergencyMapInner, {
        center: [80.2707, 13.0827] as [number, number],
        facilities: mockFacilities,
        alternativeRoutes: [{ coordinates: [[80.2707, 13.0827], [80.28, 13.09]] }] as any,
      })
    )
    expect(container).toBeDefined()
  })
})
