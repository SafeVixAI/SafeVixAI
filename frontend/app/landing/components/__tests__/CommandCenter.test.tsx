jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  var React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
  }
})

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var CommandCenter = require('../CommandCenter').default

describe('CommandCenter', function() {
  it('renders the section overline', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('LIVE INTELLIGENCE')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('Command Center')).toBeTruthy()
  })

  it('renders the section description', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText(/Real-time national operations dashboard/)).toBeTruthy()
  })

  it('renders the dashboard title bar', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('SafeVixAI Command Center')).toBeTruthy()
  })

  it('renders the LIVE badge', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('Live')).toBeTruthy()
  })

  it('renders all 5 active incidents', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('Vehicle Collision')).toBeTruthy()
    expect(rtlScreen.getByText('SOS Alert')).toBeTruthy()
    expect(rtlScreen.getByText('Road Hazard')).toBeTruthy()
    expect(rtlScreen.getByText('Traffic Congestion')).toBeTruthy()
    expect(rtlScreen.getByText('Medical Emergency')).toBeTruthy()
  })

  it('renders incident locations', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText(/NH-44, Hyderabad/)).toBeTruthy()
    expect(rtlScreen.getByText(/MG Road, Bengaluru/)).toBeTruthy()
  })

  it('renders severity badges', function() {
    render(React.createElement(CommandCenter))
    var p0Badges = rtlScreen.getAllByText('P0')
    expect(p0Badges.length).toBeGreaterThanOrEqual(2)
    var p1Badges = rtlScreen.getAllByText('P1')
    expect(p1Badges.length).toBeGreaterThanOrEqual(1)
    var p2Badges = rtlScreen.getAllByText('P2')
    expect(p2Badges.length).toBeGreaterThanOrEqual(1)
  })

  it('renders the India SVG map', function() {
    render(React.createElement(CommandCenter))
    var map = rtlScreen.getByRole('img')
    expect(map.getAttribute('aria-label')).toContain('India')
  })

  it('renders ACTIVE INCIDENTS panel label', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('ACTIVE INCIDENTS')).toBeTruthy()
  })

  it('renders NATIONAL OVERVIEW panel label', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('NATIONAL OVERVIEW')).toBeTruthy()
  })

  it('renders ANALYTICS panel label', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('ANALYTICS')).toBeTruthy()
  })

  it('renders stat pills with values', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText(/Active: 47/)).toBeTruthy()
    expect(rtlScreen.getByText(/Resolved: 312/)).toBeTruthy()
    expect(rtlScreen.getByText(/Monitoring: 1,247/)).toBeTruthy()
    expect(rtlScreen.getByText(/Response: 4.2m/)).toBeTruthy()
  })

  it('renders AI Alerts', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText(/Pattern detected: NH-44 corridor/)).toBeTruthy()
    expect(rtlScreen.getByText(/Anomaly flagged: Ring Road congestion/)).toBeTruthy()
    expect(rtlScreen.getByText(/Predictive alert: Weekend surge area/)).toBeTruthy()
  })

  it('renders severity distribution bars', function() {
    render(React.createElement(CommandCenter))
    expect(rtlScreen.getByText('Severity Distribution')).toBeTruthy()
    expect(rtlScreen.getByText('P0 Critical')).toBeTruthy()
    expect(rtlScreen.getByText('P1 High')).toBeTruthy()
    expect(rtlScreen.getByText('P2 Medium')).toBeTruthy()
  })
})
