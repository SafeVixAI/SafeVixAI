jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/lib/store', function() { return { useAppStore: Object.assign(function(sel) { var state = { gpsLocation: null, userProfile: {}, authToken: null }; return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return {} }, setState: jest.fn(), subscribe: jest.fn() }) } })
jest.mock('@/lib/public-env', function() { return { publicApiWebSocketUrl: 'ws://localhost:8000' } })
jest.mock('@/lib/safety-constants', function() { return { GROUP_TRACKING_BROADCAST_INTERVAL_MS: 5000 } })

var mockWsStatus = 'idle'
var mockWsSend = jest.fn()
var mockWsConnect = jest.fn()
var mockWsDisconnect = jest.fn()
jest.mock('@/lib/useWebSocket', function() {
  return { useWebSocket: function() { return { status: mockWsStatus, send: mockWsSend, connect: mockWsConnect, disconnect: mockWsDisconnect, reconnectAttempt: 3 } } }
})
jest.mock('@/components/EmergencyMap', function() { return { EmergencyMap: function() { return null } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var { render, screen: rtlScreen, fireEvent, act } = require('@testing-library/react')
var React = require('react')
var TrackingPage = require('../app/tracking/page').default

beforeEach(function() {
  mockWsStatus = 'idle'
  mockWsSend.mockClear()
  mockWsConnect.mockClear()
  mockWsDisconnect.mockClear()
})

describe('TrackingPage', function() {
  it('renders Join Tracking Group heading when idle', function() {
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Join Tracking Group')).toBeTruthy()
  })

  it('renders group code input when idle', function() {
    render(React.createElement(TrackingPage))
    expect(rtlScreen.getByPlaceholderText('e.g. SMITH-FAMILY-24')).toBeTruthy()
  })

  it('renders display name input when idle', function() {
    render(React.createElement(TrackingPage))
    expect(rtlScreen.getByPlaceholderText('e.g. John')).toBeTruthy()
  })

  it('renders Start Tracking button when idle', function() {
    render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Start Tracking')).toBeTruthy()
  })

  it('shows Live status badge when connected', function() {
    mockWsStatus = 'connected'
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Live')).toBeTruthy()
  })

  it('shows Connecting badge when connecting', function() {
    mockWsStatus = 'connecting'
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Connecting...')).toBeTruthy()
  })

  it('shows join form when disconnected', function() {
    mockWsStatus = 'disconnected'
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Join Tracking Group')).toBeTruthy()
  })

  it('shows Reconnecting badge with attempt count', function() {
    mockWsStatus = 'reconnecting'
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText(/Reconnecting \(3\/50\)/)).toBeTruthy()
  })

  it('shows Leave button when connected', function() {
    mockWsStatus = 'connected'
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Leave')).toBeTruthy()
  })

  it('shows Active Group heading when connected', function() {
    mockWsStatus = 'connected'
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Active Group')).toBeTruthy()
  })

  it('renders sr-only heading', function() {
    var { container } = render(React.createElement(TrackingPage))
    expect(rtlScreen.getByText('Live Family Tracking')).toBeTruthy()
  })
})
