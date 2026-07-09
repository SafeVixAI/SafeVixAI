jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  var React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
  }
})

var React = require('react')
var { render, screen } = require('@testing-library/react')
var CommandCenter = require('../CommandCenter').default

describe('CommandCenter', function() {
  it('renders the section overline', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('LIVE INTELLIGENCE')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('Command Center')).toBeTruthy()
  })

  it('renders the section description', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText(/Real-time national operations dashboard/)).toBeTruthy()
  })

  it('renders the dashboard title bar', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('SafeVixAI Command Center')).toBeTruthy()
  })

  it('renders the LIVE badge', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('Live')).toBeTruthy()
  })

  it('renders all 5 active incidents', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('Vehicle Collision')).toBeTruthy()
    expect(screen.getByText('SOS Alert')).toBeTruthy()
    expect(screen.getByText('Road Hazard')).toBeTruthy()
    expect(screen.getByText('Traffic Congestion')).toBeTruthy()
    expect(screen.getByText('Medical Emergency')).toBeTruthy()
  })

  it('renders incident locations', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText(/NH-44, Hyderabad/)).toBeTruthy()
    expect(screen.getByText(/MG Road, Bengaluru/)).toBeTruthy()
  })

  it('renders severity badges', function() {
    render(React.createElement(CommandCenter))
    var p0Badges = screen.getAllByText('P0')
    expect(p0Badges.length).toBeGreaterThanOrEqual(2)
    var p1Badges = screen.getAllByText('P1')
    expect(p1Badges.length).toBeGreaterThanOrEqual(1)
    var p2Badges = screen.getAllByText('P2')
    expect(p2Badges.length).toBeGreaterThanOrEqual(1)
  })

  it('renders the India SVG map', function() {
    render(React.createElement(CommandCenter))
    var map = screen.getByRole('img')
    expect(map.getAttribute('aria-label')).toContain('India')
  })

  it('renders ACTIVE INCIDENTS panel label', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('ACTIVE INCIDENTS')).toBeTruthy()
  })

  it('renders NATIONAL OVERVIEW panel label', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('NATIONAL OVERVIEW')).toBeTruthy()
  })

  it('renders ANALYTICS panel label', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('ANALYTICS')).toBeTruthy()
  })

  it('renders stat pills with values', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText(/Active: 47/)).toBeTruthy()
    expect(screen.getByText(/Resolved: 312/)).toBeTruthy()
    expect(screen.getByText(/Monitoring: 1,247/)).toBeTruthy()
    expect(screen.getByText(/Response: 4.2m/)).toBeTruthy()
  })

  it('renders AI Alerts', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText(/Pattern detected: NH-44 corridor/)).toBeTruthy()
    expect(screen.getByText(/Anomaly flagged: Ring Road congestion/)).toBeTruthy()
    expect(screen.getByText(/Predictive alert: Weekend surge area/)).toBeTruthy()
  })

  it('renders severity distribution bars', function() {
    render(React.createElement(CommandCenter))
    expect(screen.getByText('Severity Distribution')).toBeTruthy()
    expect(screen.getByText('P0 Critical')).toBeTruthy()
    expect(screen.getByText('P1 High')).toBeTruthy()
    expect(screen.getByText('P2 Medium')).toBeTruthy()
  })
})
