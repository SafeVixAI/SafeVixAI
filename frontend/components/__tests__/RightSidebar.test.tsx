// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

let mockState: any = {
  gpsLocation: { lat: 13.0827, lon: 80.2707 },
  nearbyServices: [{ id: '1', name: 'Hospital', lat: 13.08, lon: 80.27, distance: 0.5 }],
  nearbyRoadIssues: [{ id: 'i1', issueType: 'pothole', roadName: 'Main St', distance: 250, severity: 'high' }],
  serviceSearchMeta: { total: 1 },
  connectivity: 'online',
}
jest.mock('@/lib/store', function() {
  return {
    useAppStore: function(selector: any) {
      if (typeof selector === 'function') return selector(mockState)
      return mockState
    },
  }
})

jest.mock('@gsap/react', function() { return { useGSAP: function() { return null } } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn() } } })

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { RightSidebar } from '../RightSidebar'

beforeAll(function() {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: function() {
      return { matches: true, addEventListener: function() {}, removeEventListener: function() {} }
    },
  })
})

describe('RightSidebar', function() {
  beforeEach(function() {
    jest.clearAllMocks()
  })

  it('renders with data showing', function() {
    mockState = { gpsLocation: { lat: 13.0827, lon: 80.2707 }, nearbyServices: [{ id: '1', name: 'Hospital' }], nearbyRoadIssues: [{ id: 'i1', issueType: 'pothole', roadName: 'Main St', distance: 250, severity: 'high' }], serviceSearchMeta: { total: 1 }, connectivity: 'online' }
    render(React.createElement(RightSidebar))
    expect(screen.getByText('Area Intelligence')).toBeTruthy()
  })

  it('shows scanning placeholder when no data', function() {
    mockState = { gpsLocation: null, nearbyServices: [], nearbyRoadIssues: [], serviceSearchMeta: { total: 0 }, connectivity: 'offline' }
    render(React.createElement(RightSidebar))
    expect(screen.getByText(/Scanning Area/)).toBeTruthy()
  })

  it('toggles panel via mobile handle', function() {
    mockState = { gpsLocation: { lat: 13.0827, lon: 80.2707 }, nearbyServices: [{ id: '1', name: 'Hospital' }], nearbyRoadIssues: [{ id: 'i1', issueType: 'pothole', roadName: 'Main St', distance: 250, severity: 'high' }], serviceSearchMeta: { total: 1 }, connectivity: 'online' }
    render(React.createElement(RightSidebar))
    const toggles = screen.getAllByLabelText('Collapse panel')
    fireEvent.click(toggles[0])
    expect(screen.getAllByLabelText('Expand panel').length).toBeGreaterThanOrEqual(1)
  })
})
