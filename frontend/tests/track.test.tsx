var mockTokenValue = ''
jest.mock('@/lib/live-tracking', function() { return { subscribeToTracking: jest.fn().mockReturnValue({ unsubscribe: jest.fn() }) } })
jest.mock('@/lib/supabase-auth', function() { return { getSupabaseBrowserClient: function() { var c = { channel: function() { return c }, on: function() { return c }, subscribe: function() { return c }, removeChannel: jest.fn() }; return c } } })
jest.mock('@/lib/gsap', function() { return { gsap: { to: jest.fn(), fromTo: jest.fn(), timeline: function() { return { to: jest.fn(), fromTo: jest.fn() } } } } })
jest.mock('@gsap/react', function() { return { useGSAP: function() {} } })
jest.mock('next/dynamic', function() { return function() { return function() { return null } } })
jest.mock('next/navigation', function() {
  return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return { get: function(key) { return key === 'token' ? mockTokenValue : null } } }, useParams: function() { return {} } }
})
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import FamilyTrackingPage from '../app/track/[session_id]/page'

var mockLocationData = {
  session_id: 'session-abc', user_name: 'Jane Doe', blood_group: 'A+',
  vehicle_number: 'TN-07-CD-5678', latitude: 13.0827, longitude: 80.2707,
  accuracy: 15, speed_kmh: 32, battery_percent: 75, is_active: true,
  updated_at: new Date().toISOString(),
}

function makeParams(sid) { return { then: function() {}, status: 'fulfilled', value: { session_id: sid } } }
function okResp(d) { return { ok: true, status: 200, json: function() { return Promise.resolve(d) } } }

describe('FamilyTrackingPage', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    mockTokenValue = ''
    global.fetch = jest.fn()
  })

  it('renders session ended when no token present', function() {
    render(React.createElement(FamilyTrackingPage, { params: makeParams('test-session') }))
    expect(screen.getByText('Session Ended')).toBeTruthy()
  })

  it('renders session expired message', function() {
    var { container } = render(React.createElement(FamilyTrackingPage, { params: makeParams('test-session') }))
    expect(container.textContent).toContain('Session Ended')
  })

  it('renders page with session ID', function() {
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    expect(screen.getByText('Session Ended')).toBeTruthy()
  })

  it('renders without crashing for different session IDs', function() {
    var { container } = render(React.createElement(FamilyTrackingPage, { params: makeParams('another-session') }))
    expect(container).toBeTruthy()
  })

  it('renders with session status indicator', function() {
    var { container } = render(React.createElement(FamilyTrackingPage, { params: makeParams('test-123') }))
    expect(container.textContent).toBeTruthy()
  })

  it('renders loading phase when token exists and fetching', function() {
    mockTokenValue = 'mock-token-123'
    global.fetch.mockReturnValue(new Promise(function() {}))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    expect(screen.getByText(/Accessing Secure Stream/i)).toBeTruthy()
  })

  it('renders session ended when API returns 404', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue({ ok: false, status: 404 })
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('Session Ended')).toBeTruthy() })
  })

  it('renders session ended when API returns 403', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue({ ok: false, status: 403 })
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('Session Ended')).toBeTruthy() })
  })

  it('renders session ended when session is not active', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(Object.assign({}, mockLocationData, { is_active: false })))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('Session Ended')).toBeTruthy() })
  })

  it('renders live user name after successful fetch', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('Jane Doe')).toBeTruthy() })
  })

  it('renders blood group in live stream', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('A+')).toBeTruthy() })
  })

  it('shows dash when blood group is missing', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(Object.assign({}, mockLocationData, { blood_group: null })))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('—')).toBeTruthy() })
  })

  it('renders speed in live stream', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText(/32 km\/h/)).toBeTruthy() })
  })

  it('renders battery percentage', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('75%')).toBeTruthy() })
  })

  it('renders vehicle number', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('TN-07-CD-5678')).toBeTruthy() })
  })

  it('renders LIVE badge', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('LIVE')).toBeTruthy() })
  })

  it('renders connection type badge', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('Realtime')).toBeTruthy() })
  })

  it('renders Call 112 button', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('Call 112')).toBeTruthy() })
  })

  it('renders Call 108 button', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText('Call 108')).toBeTruthy() })
  })

  it('renders emergency advice on expired screen', function() {
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    expect(screen.getByText(/Emergency Advice/i)).toBeTruthy()
  })

  it('renders updated timestamp in live stream', async function() {
    mockTokenValue = 'mock-token'
    global.fetch.mockResolvedValue(okResp(mockLocationData))
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    await waitFor(function() { expect(screen.getByText(/Updated/)).toBeTruthy() })
  })

  it('renders Call Emergency Helpline on expired screen', function() {
    render(React.createElement(FamilyTrackingPage, { params: makeParams('session-abc') }))
    expect(screen.getByText(/Call Emergency Helpline \(112\)/i)).toBeTruthy()
  })
})
