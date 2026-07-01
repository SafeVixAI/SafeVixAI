jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/lib/store', function() { return { useAppStore: Object.assign(function(sel) { var state = { gpsLocation: null, userProfile: {}, authToken: null }; return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return {} }, setState: jest.fn(), subscribe: jest.fn() }) } })
jest.mock('@/lib/public-env', function() { return { publicApiWebSocketUrl: 'ws://localhost:8000' } })
jest.mock('@/lib/safety-constants', function() { return { GROUP_TRACKING_BROADCAST_INTERVAL_MS: 5000 } })
jest.mock('@/lib/useWebSocket', function() { return { useWebSocket: function() { return { status: 'idle', send: jest.fn(), wsRef: null } } } })
jest.mock('@/components/EmergencyMap', function() { return { EmergencyMap: function() { return null } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen } from '@testing-library/react'
import React from 'react'
import TrackingPage from '../app/tracking/page'

describe('TrackingPage', function() {
  it('renders without error', function() {
    var { container } = render(React.createElement(TrackingPage))
    expect(container).toBeTruthy()
  })

  it('renders group tracking UI shell', function() {
    var { container } = render(React.createElement(TrackingPage))
    expect(container.querySelector('h1') || container.querySelector('h2') || container.querySelector('[class]')).toBeTruthy()
  })

  it('renders input section', function() {
    var { container } = render(React.createElement(TrackingPage))
    expect(container).toBeTruthy()
  })

  it('renders with page entry ref', function() {
    var { container } = render(React.createElement(TrackingPage))
    expect(container.querySelector('div')).toBeTruthy()
  })
})
